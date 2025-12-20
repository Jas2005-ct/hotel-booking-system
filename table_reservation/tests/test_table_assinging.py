from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from table_reservation.tasks import reminder_before_one_hour
from django.test import TestCase, override_settings
from accounts.models import CustomUser, TableLayout
from table_reservation.models import TableReservation, TableAssign
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import Group
from django.core import mail
from django.conf import settings
import json

@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class TableAssignTest(TestCase):
    def setUp(self):
        self.guest_group = Group.objects.create(name='guest')
        self.waiter_group = Group.objects.create(name='waiter')
        self.admin_group = Group.objects.create(name='admin')
        ct_reservation = ContentType.objects.get_for_model(TableReservation)
        ct_assign = ContentType.objects.get_for_model(TableAssign)
        perm_add_res = Permission.objects.get(content_type=ct_reservation, codename='add_tablereservation')
        self.guest_group.permissions.add(perm_add_res)
        perm_change_assign = Permission.objects.get(content_type=ct_assign, codename='change_tableassign')
        perm_view_res = Permission.objects.get(content_type=ct_reservation, codename='view_tablereservation')
        self.waiter_group.permissions.add(perm_change_assign)
        self.waiter_group.permissions.add(perm_view_res)
        perm_view_res = Permission.objects.get(content_type=ct_reservation, codename='view_tablereservation')
        self.admin_group.permissions.add(perm_view_res)

        self.table_layout = TableLayout.objects.create(
            table_no=1, floor_no=1, Location='roof-top', capacity=4, available=True
        )

        self.waiter = CustomUser.objects.create_user(
            email='waiter@gmail.com',
            password='testpassword',
            role='waiter',
            phone_no='1234567890',
            name='waiter'
        )
        self.waiter.groups.add(self.waiter_group)

    def test_user_registration_email(self):
        mail.outbox = []
        register_data = {
            'email': 'newguest@gmail.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword',
            'phone_no': '9998887776',
            'name': 'New Guest'
        }
        
        response = self.client.post(reverse('accounts:guestuser'), register_data)
        
        self.assertEqual(response.status_code, 302) 
        self.assertTrue(CustomUser.objects.filter(email='newguest@gmail.com').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Welcome to our Hotel Management System', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['newguest@gmail.com'])

    def test_full_reservation_flow(self):
        mail.outbox = []
        
        guest_user = CustomUser.objects.create_user(
            email='guestflow@gmail.com',
            password='password123',
            role='guest',
            phone_no='1112223334',
            name='Flow Guest'
        )
        guest_user.groups.add(self.guest_group)
        self.client.login(email='guestflow@gmail.com', password='password123')

        future_time = timezone.localtime() + timedelta(minutes=75)
        book_data = {
            'seat': 4,
            'time_schedule': future_time.date(),
            'start_time': future_time.strftime('%H:%M')
        }
        
        response = self.client.post(
            reverse('table_reservation:table_book_form'),
            book_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        self.table_layout.refresh_from_db()
        self.assertFalse(self.table_layout.available)
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Thank For Your reservation', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['guestflow@gmail.com'])

        self.client.login(email='waiter@gmail.com', password='testpassword')
        reservation = TableReservation.objects.get(user=guest_user)
        
        assign_data = {
            'pk': reservation.id
        }
        response = self.client.post(
            reverse('table_reservation:table_assign'),
            assign_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        assignment = TableAssign.objects.get(tabereservation=reservation)
        self.assertTrue(assignment.assigned)
        self.assertEqual(assignment.waiter, self.waiter)
        self.assertFalse(assignment.completed)

        response = self.client.post(
            reverse('table_reservation:table_unassign'),
            assign_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        assignment.refresh_from_db()
        self.assertFalse(assignment.assigned)
        self.assertTrue(assignment.completed)
        self.table_layout.refresh_from_db()
        self.assertTrue(self.table_layout.available)

    def test_unauthorized_unassign(self):
        guest = CustomUser.objects.create_user(
            email='g2@gmail.com', password='p', role='guest', name='G2', phone_no='2222222222'
        )
        reservation = TableReservation.objects.create(
            user=guest, table=self.table_layout, duration=timedelta(minutes=30), time_schedule=timezone.now()
        )
        
        TableAssign.objects.create(tabereservation=reservation, waiter=self.waiter, assigned=True)
        other_waiter = CustomUser.objects.create_user(
            email='otherwaiter@gmail.com', password='p', role='waiter', name='Other', phone_no='3333333333'
        )
        other_waiter.groups.add(self.waiter_group)
        self.client.login(email='otherwaiter@gmail.com', password='p')
        response = self.client.post(reverse('table_reservation:table_unassign'), {'pk': reservation.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], 'You are not authorized to unassign this table')

    def test_remainder_mail_before_one_hour(self):
        guest = CustomUser.objects.create_user(
            email='g3@gmail.com', password='p', role='guest', name='G3', phone_no='4444444444'
        )
        now = timezone.localtime()
        target_time = now + timedelta(hours=1)
        reservation = TableReservation.objects.create(
            user=guest, 
            table=self.table_layout, 
            duration=timedelta(minutes=30), 
            time_schedule=target_time.date(),
            start_time=target_time.time()
        )
        TableAssign.objects.create(tabereservation=reservation, waiter=self.waiter, assigned=True)
        mail.outbox = []
        reminder_before_one_hour()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Gentle Reminder', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['g3@gmail.com'])
        
    def test_change_table_status(self):
        # Test that change_table_status updates availability for approaching reservations
        from table_reservation.tasks import change_table_status
        
        # 1. Reservation within 90 mins (should block table)
        data_now_user = CustomUser.objects.create_user(
            email='now@gmail.com', password='p', role='guest', name='Now', phone_no='555555'
        )
        near_future = timezone.now() + timedelta(minutes=30)
        table1 = TableLayout.objects.create(
            table_no=10, floor_no=1, Location='indoor', capacity=4, available=True
        )
        TableReservation.objects.create(
            user=data_now_user, 
            table=table1, 
            duration=timedelta(minutes=90), 
            time_schedule=near_future.date(),
            start_time=near_future.time()
        )
        
        # 2. Reservation > 90 mins (should NOT block table)
        data_later_user = CustomUser.objects.create_user(
            email='later@gmail.com', password='p', role='guest', name='Later', phone_no='666666'
        )
        far_future = timezone.now() + timedelta(minutes=120)
        table2 = TableLayout.objects.create(
            table_no=11, floor_no=1, Location='indoor', capacity=4, available=True
        )
        TableReservation.objects.create(
            user=data_later_user, 
            table=table2, 
            duration=timedelta(minutes=90), 
            time_schedule=far_future.date(),
            start_time=far_future.time()
        )
        
        change_table_status()
        
        table1.refresh_from_db()
        table2.refresh_from_db()
        
        self.assertFalse(table1.available, "Table should be unavailable (reservation within 90 mins)")
        self.assertTrue(table2.available, "Table should remain available (reservation > 90 mins)")


    def test_shows_only_assigned_tables_by_user(self):
        guest = CustomUser.objects.create_user(
            email='g2@gmail.com', password='p', role='guest', name='G2', phone_no='2222222222'
        )
        reservation = TableReservation.objects.create(
            user=guest, 
            table=self.table_layout, 
            duration=timedelta(minutes=30), 
            time_schedule=timezone.localtime().date(),
            start_time=timezone.localtime().time()
        )
        TableAssign.objects.create(tabereservation=reservation, waiter=self.waiter, assigned=True)
        other_waiter = CustomUser.objects.create_user(
            email='otherwaiter@gmail.com', password='p', role='waiter', name='Other', phone_no='3333333333'
        )
        other_waiter.groups.add(self.waiter_group)
        self.client.login(email='otherwaiter@gmail.com', password='p') 
        response = self.client.get(reverse('table_reservation:table_reserved'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['table_res']), 1)