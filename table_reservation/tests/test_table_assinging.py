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
        """Test that registering a new guest user sends a welcome email."""
        mail.outbox = [] # Clear outbox
        
        # User valid data for the form.
        register_data = {
            'email': 'newguest@gmail.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword',
            'phone_no': '9998887776',
            'name': 'New Guest'
        }
        
        # Post to GuestUserView
        response = self.client.post(reverse('accounts:guestuser'), register_data)
        
        # Check redirection
        self.assertEqual(response.status_code, 302) 
        self.assertTrue(CustomUser.objects.filter(email='newguest@gmail.com').exists())
        
        # Verify Email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Welcome to our Hotel Management System', mail.outbox[0].subject)
        # Check receiver
        self.assertEqual(mail.outbox[0].to, ['newguest@gmail.com'])

    def test_full_reservation_flow(self):
        """Test full flow: Reservation + Email, Waiter Assign, Waiter Unassign."""
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

        future_time = timezone.now() + timedelta(hours=2)
        book_data = {
            'user_id': guest_user.id,
            'table_no': self.table_layout.table_no,
            'duration': 30,
            'time_schedule': future_time.strftime('%Y-%m-%dT%H:%M')
        }
        
        response = self.client.post(
            reverse('table_reservation:table_book_form'),
            json.dumps(book_data),
            content_type='application/json'
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

    def test_assign_already_assigned(self):
        guest = CustomUser.objects.create_user(
            email='g1@gmail.com', password='p', role='guest', name='G1', phone_no='1111111111'
        )
        reservation = TableReservation.objects.create(
            user=guest, table=self.table_layout, duration=timedelta(minutes=30), time_schedule=timezone.now()
        )
        
        self.client.login(email='waiter@gmail.com', password='testpassword')
        TableAssign.objects.create(tabereservation=reservation, waiter=self.waiter, assigned=True)
        
        response = self.client.post(reverse('table_reservation:table_assign'), {'pk': reservation.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], 'Table is already assigned')

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

    def test_unassign_non_existent_assignment(self):
        """Test unassigning a reservation that has no active assignment."""
        guest = CustomUser.objects.create_user(
            email='g3@gmail.com', password='p', role='guest', name='G3', phone_no='4444444444'
        )
        reservation = TableReservation.objects.create(
            user=guest, table=self.table_layout, duration=timedelta(minutes=30), time_schedule=timezone.now()
        )
        
        self.client.login(email='waiter@gmail.com', password='testpassword')
        response = self.client.post(reverse('table_reservation:table_unassign'), {'pk': reservation.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertIn('Active assignment not found', response.json()['message'])