from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser, Menu, TableLayout
from django.contrib.auth.models import Group

class MenuTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='testuser@gmail.com',
            password='testpass123',
            role='admin',
            phone_no='0987654321',
            name='testuser'
        )
        self.menu = Menu.objects.create(
            name='testmenu',
            price=100,
            description='testmenu',
            food_category='indian',
            food_type='veg'
        )
        self.client.login(email='testuser@gmail.com', password='testpass123')
    
    def test_menu_create(self):
        url = reverse('accounts:menucreate')
        data = {
            'name': 'newmenu',
            'price': 150,
            'description': 'newmenu',
            'food_category': 'chinese',
            'food_type': 'non-veg'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Menu.objects.count(), 2) 

    def test_menu_update(self):
        url = reverse('accounts:menuupdate', args=[self.menu.pk])
        data = {
            'name': 'updatedmenu',
            'price': 200,
            'description': 'updatedmenu',
            'food_category': 'italian',
            'food_type': 'veg'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.menu.refresh_from_db()
        self.assertEqual(self.menu.name, 'updatedmenu')
        self.assertEqual(self.menu.price, 200)

    def test_menu_delete(self):
        url = reverse('accounts:menudelete', args=[self.menu.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(Menu.objects.count(), 0)