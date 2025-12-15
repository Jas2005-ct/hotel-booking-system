from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser, TableLayout
from table_reservation.models import TableReservation, TableAssign
from datetime import date, time, timedelta, datetime
from django.utils import timezone

class TableTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='testuser@gmail.com',
            password='testpass123',
            role='admin',
            phone_no='0987654321',
            name='testuser'
        )
        self.table = TableLayout.objects.create(
            floor_no=1,
            Location='indoor',
            capacity=4,
            available=True
        )
        self.client.login(email='testuser@gmail.com', password='testpass123')

    def test_table_create(self):
        url = reverse('accounts:tablecreate')
        data = {
            'floor_no': 2,
            'Location': 'outdoor',
            'capacity': 6,
            'available': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TableLayout.objects.count(), 2)

    def test_table_update(self):
        url = reverse('accounts:tableupdate', args=[self.table.pk])
        data = {
            'floor_no': 2,
            'Location': 'roof_top',
            'capacity': 8,
            'available': False
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.table.refresh_from_db()
        self.assertEqual(self.table.floor_no, 2)
        self.assertEqual(self.table.Location, 'roof_top')
        self.assertEqual(self.table.capacity, 8)

    def test_table_delete(self):
        url = reverse('accounts:tabledelete', args=[self.table.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(TableLayout.objects.count(), 0)


    def test_table_status(self):
        url = reverse('accounts:tablestatus', args=[self.table.pk])
        data = {'status': 'unavailable'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.table.refresh_from_db()
        self.assertFalse(self.table.available)


        data = {'status': 'available'}
        response = self.client.post(url, data)
        self.table.refresh_from_db()
        self.assertTrue(self.table.available)

class ReservationTest(TestCase):
    def setUp(self):
        # Create Users
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

        # Create Table
        self.table = TableLayout.objects.create(
            floor_no=1,
            Location='indoor',
            capacity=4,
            available=True
        )

    def test_reservation_creation(self):
        self.client.login(email='guest@gmail.com', password='password123')
        url = reverse('table_reservation:table_book_form')
        
        # Future date
        future_date = (timezone.now() + timedelta(days=1)).date()
        
        data = {
            'seat': 2,
            'time_schedule': future_date,
            'start_time': '18:00',
            'duration': '01:30' # Assuming form sends this or handled in view
        }
        
        # The view expects form data which includes seat, time_schedule, start_time
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        
        # Verify reservation created
        self.assertEqual(TableReservation.objects.count(), 1)
        reservation = TableReservation.objects.first()
        self.assertEqual(reservation.user, self.guest_user)
        self.assertEqual(reservation.table, self.table)

    def test_reservation_view_split(self):
        self.client.login(email='admin@gmail.com', password='password123')
        
        # Create Past Reservation (completed)
        past_date = (timezone.now() - timedelta(days=1)).date()
        past_res = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=past_date,
            start_time=time(18, 0),
            end_time=time(19, 30),
            seat=2
        )
        # Create assignment and complete it so it shows in past_reservations
        TableAssign.objects.create(
            tabereservation=past_res,
            waiter=self.waiter_user,
            assigned=False,
            completed=True
        )

        # Create Upcoming Reservation
        future_date = (timezone.now() + timedelta(days=1)).date()
        upcoming_res = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(minutes=90),
            time_schedule=future_date,
            start_time=time(18, 0),
            end_time=time(19, 30),
            seat=2
        )

        url = reverse('table_reservation:table_reserved')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Check context for split
        context = response.context
        self.assertIn(upcoming_res, context['upcoming_reservations'])
        self.assertIn(past_res, context['past_reservations'])

    def test_assign_waiter(self):
        self.client.login(email='waiter@gmail.com', password='password123')
        
        # Create Reservation
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

        # Verify Assignment
        assignment = TableAssign.objects.get(tabereservation=res)
        self.assertTrue(assignment.assigned)
        self.assertEqual(assignment.waiter, self.waiter_user)

    def test_unassign_waiter(self):
        self.client.login(email='waiter@gmail.com', password='password123')
        
        # Create Reservation and Assignment
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

        # Verify Assignment Updated
        assignment = TableAssign.objects.get(tabereservation=res)
        self.assertFalse(assignment.assigned)
        self.assertTrue(assignment.completed)
        
        # Verify Table Available
        self.table.refresh_from_db()
        self.assertTrue(self.table.available)


