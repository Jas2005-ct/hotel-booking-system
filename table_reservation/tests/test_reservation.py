from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser, TableLayout
from table_reservation.models import TableReservation, TableAssign
from datetime import date, time, timedelta, datetime
from django.utils import timezone


class ReservationTest(TestCase):
    def setUp(self):
        self.guest_user = CustomUser.objects.create_user(
            email='guest@gmail.com',
            password='password123',
            role='guest',
            phone_no='1234567890',
            name='Guest User'
        )
        self.waiter_user = CustomUser.objects.create_user(
            email='waiter@gmail.com',
            password='password123',
            role='waiter',
            phone_no='1122334455',
            name='Waiter User'
        )
        self.admin_user = CustomUser.objects.create_user(
            email='admin@gmail.com',
            password='password123',
            role='admin',
            phone_no='9988776655',
            name='Admin User'
        )
        self.table = TableLayout.objects.create(
            floor_no=1,
            Location='indoor',
            capacity=4,
            available=True
        )

        # Assign Permissions
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        ct_reservation = ContentType.objects.get_for_model(TableReservation)
        ct_assign = ContentType.objects.get_for_model(TableAssign)

        # for Guest: add_tablereservation
        perm_add_res = Permission.objects.get(content_type=ct_reservation, codename='add_tablereservation')
        self.guest_user.user_permissions.add(perm_add_res)

        # for Waiter: change_tableassign
        perm_change_assign = Permission.objects.get(content_type=ct_assign, codename='change_tableassign')
        self.waiter_user.user_permissions.add(perm_change_assign)
        
        # for Admin: view_tablereservation and change_tableassign
        perm_view_res = Permission.objects.get(content_type=ct_reservation, codename='view_tablereservation')
        self.admin_user.user_permissions.add(perm_view_res)
        self.admin_user.user_permissions.add(perm_change_assign)

    def test_reservation_creation(self):
        self.client.login(email='guest@gmail.com', password='password123')
        url = reverse('table_reservation:table_book_form')
        
        future_date = (timezone.now() + timedelta(days=1)).date()
        
        data = {
            'seat': 2,
            'time_schedule': future_date,
            'start_time': '18:00',
            'duration': '01:30'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(TableReservation.objects.count(), 1)
        reservation = TableReservation.objects.first()
        self.assertEqual(reservation.user, self.guest_user)
        self.assertEqual(reservation.table, self.table)
    
    def test_assign_waiter(self):
        self.client.login(email='waiter@gmail.com', password='password123')
        res = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=timezone.now().date(),
            start_time=time(19, 0),
            end_time=time(20, 30),
            seat=2
        )

        url = reverse('table_reservation:table_assign')
        data = {'pk': res.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        assignment = TableAssign.objects.get(tabereservation=res)
        self.assertTrue(assignment.assigned)
        self.assertEqual(assignment.waiter, self.waiter_user)

    def test_unassign_waiter(self):
        self.client.login(email='waiter@gmail.com', password='password123')
    
        res = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=timezone.now().date(),
            start_time=time(19, 0),
            end_time=time(20, 30),
            seat=2
        )
        TableAssign.objects.create(
            tabereservation=res,
            waiter=self.waiter_user,
            assigned=True
        )
        url = reverse('table_reservation:table_unassign')
        data = {'pk': res.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        json_resp = response.json()
        self.assertTrue(json_resp['success'])

        assignment = TableAssign.objects.get(tabereservation=res)
        self.assertFalse(assignment.assigned)
        self.assertTrue(assignment.completed)
        self.table.refresh_from_db()
        self.assertTrue(self.table.available)

    def test_reservation_past_time(self):
        self.client.login(email='guest@gmail.com', password='password123')
        past_date = (timezone.now() - timedelta(days=1)).date()
        data = {
            'seat': 2,
            'time_schedule': past_date,
            'start_time': '18:00',
            'duration': '01:30'
        }
        url = reverse('table_reservation:table_book_form')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response['success'])
        self.assertTrue('time_schedule' in json_response['errors'] or 'start_time' in json_response['errors'])

    def test_reservation_before_1_hour(self):
        self.client.login(email='guest@gmail.com', password='password123')
        today = timezone.now().date()
        time_now = (timezone.now() + timedelta(minutes=30)).time()
        
        data = {
            'seat': 2,
            'time_schedule': today,
            'start_time': time_now.strftime('%H:%M'),
            'duration': '01:30'
        }
        url = reverse('table_reservation:table_book_form')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response['success'])
        self.assertIn('start_time', json_response['errors'])

    def test_delete_table_reservation(self):
        self.client.login(email='guest@gmail.com', password='password123')
        future_date = (timezone.now() + timedelta(days=2)).date()
        reservation = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=future_date,
            start_time=time(18, 0),
            end_time=time(19, 30),
            seat=2
        )
        
        url = reverse('table_reservation:table_delete')
        data = {'pk': reservation.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['message'], 'Reservation deleted successfully')
        self.assertFalse(TableReservation.objects.filter(pk=reservation.pk).exists())

    def test_delete_table_reservation_after_assigned(self):    
        self.client.login(email='guest@gmail.com', password='password123')
        future_date = (timezone.now() + timedelta(days=2)).date()
        
        reservation = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=future_date,
            start_time=time(18, 0),
            end_time=time(19, 30),
            seat=2
        )
        
        TableAssign.objects.create(
            tabereservation=reservation,
            waiter=self.waiter_user,
            assigned=True
        )
        
        url = reverse('table_reservation:table_delete')
        data = {'pk': reservation.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['message'], 'Reservation deleted successfully')

    def test_assign_waiter_able_to_checkout(self):
        self.client.login(email='waiter@gmail.com', password='password123')
        
        future_date = (timezone.now() + timedelta(days=2)).date()
        reservation = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=future_date,
            start_time=time(18, 0),
            end_time=time(19, 30),
            seat=2
        )
        TableAssign.objects.create(
            tabereservation=reservation,
            waiter=self.waiter_user,
            assigned=True
        )
        url = reverse('table_reservation:table_unassign')
        data = {'pk': reservation.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['message'], 'Table checked out Successfully')

    def test_unasign_waiter_unable_to_checkout(self):
        self.client.login(email='waiter@gmail.com', password='password123')
        other_waiter = CustomUser.objects.create_user(
            email='other_waiter@gmail.com',
            password='password123',
            role='waiter',
            phone_no='1112223334',
            name='Other Waiter'
        )
        
        future_date = (timezone.now() + timedelta(days=2)).date()
        reservation = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=future_date,
            start_time=time(18, 0),
            end_time=time(19, 30),
            seat=2
        )
        TableAssign.objects.create(
            tabereservation=reservation,
            waiter=other_waiter,
            assigned=True
        )
        url = reverse('table_reservation:table_unassign')
        data = {'pk': reservation.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertFalse(json_response['success'])
        self.assertEqual(json_response['message'], 'You are not authorized to unassign this table')
    
    def test_table_reserve_without_time(self):
        self.client.login(email='guest@gmail.com', password='password123')
        future_date = (timezone.now() + timedelta(days=2)).date()
        data = {
            'seat': 2,
            'time_schedule': future_date,
            'duration': '01:30'
        }
        url = reverse('table_reservation:table_book_form')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertFalse(json_response['success'])
        self.assertTrue(json_response['message'])

    def test_table_reserve_without_seat(self):
        self.client.login(email='guest@gmail.com', password='password123')
        future_date = (timezone.now() + timedelta(days=2)).date()
        data = {
            'time_schedule': future_date,
            'start_time': '18:00',
            'duration': '01:30'
        }
        url = reverse('table_reservation:table_book_form')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response['success'])
        self.assertTrue('seat' in json_response['errors'])

    def test_table_assign_by_admin_not_able(self):
        self.client.login(email='admin@gmail.com', password='password123')
        future_date = (timezone.now() + timedelta(days=2)).date()
        reservation = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=future_date,
            start_time=time(18, 0),
            end_time=time(19, 30),
            seat=2
        )
        TableAssign.objects.create(
            tabereservation=reservation,
            waiter=self.waiter_user,
            assigned=True
        )
        url = reverse('table_reservation:table_unassign')
        data = {'pk': reservation.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertFalse(json_response['success'])
        self.assertEqual(json_response['message'], 'You are not authorized to unassign this table')