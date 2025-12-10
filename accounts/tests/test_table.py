from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser, TableLayout

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
