from django.test import TestCase
from orders.models import order,order_items,Cart_Items,Cart_User,order_kitchen_staff
from accounts.models import CustomUser,Menu
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from unittest.mock import patch


class OrderTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com', 
            password='testpass', 
            name='Test User', 
            phone_no=1234567890, 
            role='guest'
        )
        self.client.login(email='testuser@example.com', password='testpass')
        
        self.cart_user = Cart_User.objects.create(user=self.user)
        
        self.menu = Menu.objects.create(
            name='Test Menu', 
            price=10.0, 
            description='Test Description'
        )
        
        self.cart_item = Cart_Items.objects.create(
            cart_user=self.cart_user, 
            menu=self.menu, 
            quantity=1
        )

    def test_create_order(self):
        data = {
            'vehicle_number': 'TN01AB1234',
            'pickup_time': '12:00:00'
        }
        with patch('orders.tasks.order_confirmation_email.delay') as mock_email:
             response = self.client.post(reverse('orders:checkout'), data)
             self.assertEqual(response.status_code, 200)
             self.assertTrue(response.json()['success'])
             self.assertTrue(order.objects.filter(cart_user=self.cart_user).exists())
             self.assertEqual(order.objects.get(cart_user=self.cart_user).total_amount, 10.0)
             self.assertEqual(order.objects.get(cart_user=self.cart_user).vehicle_number, 'TN01AB1234')
             self.assertEqual(order.objects.get(cart_user=self.cart_user).pickup_time, datetime.strptime('12:00:00', '%H:%M:%S').time())

    def test_order_kitchen_staff_view(self):
        kitchen_user = CustomUser.objects.create_user(
            email='kitchen@example.com', password='testpass', name='Kitchen Staff', phone_no=9876543210, role='kitchen_staff'
        )
        self.client.login(email='kitchen@example.com', password='testpass')
        current_time = timezone.localtime().time()
        new_order = order.objects.create(
            cart_user=self.cart_user,
            total_amount=10.0,
            vehicle_number='TN01AB1234',
            pickup_time=(timezone.localtime() + timedelta(hours=1)).time()
        )
        order_items.objects.create(cart_user=self.cart_user, order=new_order, menu=self.menu, quantity=1)
        response = self.client.get(reverse('orders:kitchen-staff'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'kitchen_staff.html')
        self.assertEqual(len(response.context['orders']), 1)
        self.assertEqual(response.context['orders'][0].total_amount, 10.0)
        self.assertEqual(response.context['orders'][0].vehicle_number, 'TN01AB1234')
        self.assertEqual(response.context['orders'][0].pickup_time, new_order.pickup_time)

    def test_order_waiter_complete(self):
        waiter_user = CustomUser.objects.create_user(
            email='waiter@example.com', password='testpass', name='Waiter', phone_no=1122334455, role='waiter'
        )
        self.client.login(email='waiter@example.com', password='testpass')
        new_order = order.objects.create(
             cart_user=self.cart_user,
             total_amount=10.0,
             vehicle_number='TN01AB1234',
             pickup_time='12:00:00',
             status='ready'
        )

        response = self.client.post(reverse('orders:service-staff'), {'id': new_order.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        new_order.refresh_from_db()
        self.assertEqual(new_order.status, 'completed')
        self.assertEqual(new_order.waiter, waiter_user)

    def test_order_history_in_guest_home(self):
        new_order = order.objects.create(
             cart_user=self.cart_user,
             total_amount=10.0,
             vehicle_number='TN01AB1234',
             pickup_time='12:00:00',
             status='completed'
        )
        
        response = self.client.get(reverse('orders:order-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order_list.html')
        self.assertEqual(len(response.context['orders']), 1)
        self.assertEqual(response.context['orders'][0].total_amount, 10.0)
        self.assertEqual(response.context['orders'][0].vehicle_number, 'TN01AB1234')
        self.assertEqual(response.context['orders'][0].status, 'completed')

    def test_order_history_in_kitchen_staff(self):
        kitchen_user = CustomUser.objects.create_user(
            email='kitchen_history@example.com', password='testpass', name='Kitchen Staff', phone_no=9876543211, role='kitchen_staff'
        )
        self.client.login(email='kitchen_history@example.com', password='testpass')
        new_order = order.objects.create(
             cart_user=self.cart_user,
             total_amount=10.0,
             vehicle_number='TN01AB1234',
             pickup_time='12:00:00',
             status='completed'
        )
        # Create relation for history
        order_kitchen_staff.objects.create(order=new_order, kitchen_staff=kitchen_user)
        
        response = self.client.get(reverse('orders:kitchen-staff'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'kitchen_staff.html')
        self.assertEqual(len(response.context['past_orders']), 1)
        self.assertEqual(response.context['past_orders'][0].order.total_amount, 10.0)
        self.assertEqual(response.context['past_orders'][0].order.vehicle_number, 'TN01AB1234')
        self.assertEqual(response.context['past_orders'][0].order.status, 'completed')

    
    def test_kitchen_page_show_past_order_of_current_user(self):
        kitchen_user = CustomUser.objects.create_user(
            email='kitchen@example.com', password='testpass', name='Kitchen Staff', phone_no=9876543210, role='kitchen_staff'
        )
        self.client.login(email='kitchen@example.com', password='testpass')
        new_order = order.objects.create(
             cart_user=self.cart_user,
             total_amount=10.0,
             vehicle_number='TN01AB1234',
             pickup_time='12:00:00',
             status='ready'
        )
        order_kitchen_staff.objects.create(order=new_order, kitchen_staff=kitchen_user)
        response = self.client.get(reverse('orders:kitchen-staff'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'kitchen_staff.html')
        self.assertEqual(len(response.context['order_taken']), 1)
        self.assertEqual(response.context['order_taken'][0].order.total_amount, 10.0)
        self.assertEqual(response.context['order_taken'][0].order.vehicle_number, 'TN01AB1234')
        self.assertEqual(response.context['order_taken'][0].order.status, 'ready')

    def test_unable_to_place_order_if_no_vehicle_number(self):
        self.client.login(email='testuser@example.com', password='testpass')
        response = self.client.post(reverse('orders:checkout'), {'pickup_time': '12:00:00'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], 'Invalid form data')

    def test_unable_to_place_order_if_no_pickup_time(self):
        self.client.login(email='testuser@example.com', password='testpass')
        response = self.client.post(reverse('orders:checkout'), {'vehicle_number': 'TN01AB1234'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], 'Invalid form data')
    
    def test_unable_to_place_order_if_no_cart_items(self):
        self.cart_item.delete()
        self.client.login(email='testuser@example.com', password='testpass')
        response = self.client.post(reverse('orders:checkout'), {'vehicle_number': 'TN01AB1234', 'pickup_time': '12:00:00'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], 'Cart is empty')

    def test_guest_page_show_its_own_orders(self):
        new_order = order.objects.create(
             cart_user=self.cart_user,
             total_amount=10.0,
             vehicle_number='TN01AB1234',
             pickup_time='12:00:00',
             status='completed'
        )
        
        response = self.client.get(reverse('orders:order-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order_list.html')
        self.assertEqual(len(response.context['orders']), 1)
        self.assertEqual(response.context['orders'][0].total_amount, 10.0)
        self.assertEqual(response.context['orders'][0].vehicle_number, 'TN01AB1234')
        self.assertEqual(response.context['orders'][0].status, 'completed')


    
    