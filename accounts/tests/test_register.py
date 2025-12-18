from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from django.contrib.auth.models import Group
from accounts.forms import CustomUserForm
from accounts.views import*

class RegisterTest(TestCase):
    def setUp(self):
        self.group_admin = Group.objects.create(name='admin')
        self.group_waiter = Group.objects.create(name='waiter')
        self.group_guest = Group.objects.create(name='guest')
        self.role_admin = 'admin'
        self.role_waiter = 'waiter'
        self.role_kitchen = 'kitchen_staff'
        self.role_guest = 'guest'
        self.user = CustomUser.objects.create_user(email='testuser@gmail.com',password='testpass123',role='admin',phone_no='1234567890',name='testuser')
        self.user.groups.add(self.group_admin)
        self.client.login(email='testuser@gmail.com',password='testpass123')

    def test_admin_register(self):
        url = reverse('accounts:adminuser')
        data = {
            'email': 'newadmin@gmail.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': self.role_admin,
            'phone_no': '9987654321',
            'name': 'newadmin'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomUser.objects.count(), 2)
        self.assertEqual(response.url, reverse('admin_report:admin_home'))

    def test_guest_register(self):
        url = reverse('accounts:guestuser')
        data = {
            'email': 'newguest@gmail.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': self.role_guest,
            'phone_no': '9987654321',
            'name': 'newguest'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomUser.objects.count(), 2)

    def test_waiter_register(self):
        url = reverse('accounts:waiteruser')
        data = {
            'email': 'newwaiter@gmail.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': self.role_waiter,
            'phone_no': '9987654321',
            'name': 'newwaiter'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomUser.objects.count(), 2)
        self.assertEqual(response.url, reverse('accounts:management'))    
    
    def test_kitchen_register(self):
        url = reverse('accounts:kitchenuser')
        data = {
            'email': 'newkitchen@gmail.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': self.role_kitchen,
            'phone_no': '9987654321',
            'name': 'newkitchen'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CustomUser.objects.count(), 2)

    def test_register_repeated(self):
        url = reverse('accounts:adminuser')
        data = {
            'email': 'testuser@gmail.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': self.role_admin,
            'phone_no': '1234567890',
            'name': 'testuser'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_login(self):
        url = reverse('accounts:login')
        data = {
            'email': 'testuser@gmail.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin_report:admin_home'))

    def test_login_invalid(self):
        url = reverse('accounts:login')
        data = {
            'email': 'testuser@gmail.com',
            'password': 'wrongpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(url, reverse('accounts:login'))

    def test_logout(self):
        url = reverse('accounts:logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:login'))