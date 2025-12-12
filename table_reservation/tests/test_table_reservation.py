from django.test import TestCase
from accounts.models import CustomUser,TableLayout
from table_reservation.models import TableReservation
from datetime import datetime, timedelta
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import Group
from table_reservation.views import *
import json

class TableReservatoinTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='testuser@gmail.com',
            password='testpassword',
            role='guest',
            phone_no='1234567892',
            name='testuser'
        )
        self.user.groups.add(Group.objects.create(name='guest'))
        self.client.login(email='testuser@gmail.com',password='testpassword')
        self.table_layout = TableLayout.objects.create(
            table_no = 1,floor_no = 1,Location='roof-top',capacity=4,available=True
        )
        self.waiter = CustomUser.objects.create_user(
            email='waiter@gmail.com',
            password='testpassword',
            role='waiter',
            phone_no='1234567890',
            name='waiter'
        )
        self.waiter.groups.add(Group.objects.create(name='waiter'))
        self.admin = CustomUser.objects.create_user(
            email='admin@gmail.com',
            password='testpassword',
            role='admin',
            phone_no='1234567891',
            name='admin'
        )
        self.admin.groups.add(Group.objects.create(name='admin'))

    def test_table_reservation_success(self):
        self.client.login(email='testuser@gmail.com',password='testpassword')
        future_time = timezone.now() + timedelta(hours=2)
        data = {
            'user_id' : self.user.id,
            'table_no': self.table_layout.table_no,
            'duration': 30,
            'time_schedule': future_time.strftime('%Y-%m-%dT%H:%M')
        }
        response = self.client.post(
            reverse('table_reservation:table_book_form'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(TableReservation.objects.count(),1)
        self.assertEqual(TableReservation.objects.first().user,self.user)
        self.assertEqual(TableReservation.objects.first().table,self.table_layout)
        self.assertEqual(TableReservation.objects.first().duration,timedelta(minutes=30))

    def test_reservation_duration_above_90(self):
        self.client.login(email='testuser@gmail.com',password='testpassword')
        future_time = timezone.now() + timedelta(hours=2)
        data = {
            'table_no': self.table_layout.table_no,
            'duration': 100,
            'time_schedule': future_time.strftime('%Y-%m-%dT%H:%M')
        }
        response = self.client.post(
            reverse('table_reservation:table_book_form'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        json_resp = response.json()
        self.assertFalse(json_resp['success'])
        self.assertTrue(
            "Ensure this value is less than or equal to 90" in json_resp['message'] or 
            "less than 90 minutes" in json_resp['message']
        )
        self.assertEqual(TableReservation.objects.count(), 0)

    def test_reservation_past_date(self):
        self.client.login(email='testuser@gmail.com',password='testpassword')
        past_time = timezone.now() - timedelta(days=1)
        data = {
            'table_no': self.table_layout.table_no,
            'duration': 30,
            'time_schedule': past_time.strftime('%Y-%m-%dT%H:%M')
        }
        response = self.client.post(
            reverse('table_reservation:table_book_form'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        json_resp = response.json()
        self.assertFalse(json_resp['success'])
        self.assertIn("past time", json_resp['message'])
        self.assertEqual(TableReservation.objects.count(), 0)

    def test_reservation_30min_before_schedule(self):
        self.client.login(email='testuser@gmail.com',password='testpassword')
        short_notice_time = timezone.now() + timedelta(minutes=30)
        data = {
            'table_no': self.table_layout.table_no,
            'duration': 30,
            'time_schedule': short_notice_time.strftime('%Y-%m-%dT%H:%M')
        }
        response = self.client.post(
            reverse('table_reservation:table_book_form'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        json_resp = response.json()
        self.assertFalse(json_resp['success'])
        self.assertIn("less than an hour", json_resp['message'])
        self.assertEqual(TableReservation.objects.count(), 0)

    def test_table_show_only_available(self):
        self.client.login(email='testuser@gmail.com',password='testpassword')
        booked_table = TableLayout.objects.create(
            table_no=2, floor_no=1, Location='roof-top', capacity=4, available=False
        )
        response = self.client.get(reverse('table_reservation:guesthome'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.table_layout, response.context['tables'])
        self.assertNotIn(booked_table, response.context['tables'])

    def test_booking_hides_table_and_shows_to_staff(self):
        self.client.login(email='testuser@gmail.com', password='testpassword')
        future_time = timezone.now() + timedelta(hours=2)
        data = {
            'user_id': self.user.id,
            'table_no': self.table_layout.table_no,
            'duration': 30,
            'time_schedule': future_time.strftime('%Y-%m-%dT%H:%M')
        }
        response = self.client.post(
            reverse('table_reservation:table_book_form'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.table_layout.refresh_from_db()
        self.assertFalse(self.table_layout.available)
        response = self.client.get(reverse('table_reservation:guesthome'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.table_layout, response.context['tables'])
        self.client.login(email='waiter@gmail.com', password='testpassword')
        response = self.client.get(reverse('table_reservation:table_reserved'))
        self.assertEqual(response.status_code, 200)
        reservation = TableReservation.objects.get(table=self.table_layout, user=self.user)
        self.assertIn(reservation, response.context['upcoming_reservations'])
        self.client.login(email='admin@gmail.com', password='testpassword')
        response = self.client.get(reverse('table_reservation:table_reserved'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(reservation, response.context['upcoming_reservations'])
