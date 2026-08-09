from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser, Menu
from orders.models import Cart_User, Cart_Items, Order, OrderItem
from unittest.mock import patch

class CartCreateViewTest(TestCase):
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

    def test_cart_create_view(self):
        response = self.client.get(reverse('orders:cart-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart_sidebar.html')
        self.assertEqual(len(response.context['cart_items']), 1)
        self.assertEqual(response.context['total_amount'], 10.0)

    def test_cart_add_item(self):
        menu2 = Menu.objects.create(name='Test Menu 2', price=20.0, description='Desc 2')
        response = self.client.post(reverse('orders:cart-create'), {'menu_id': menu2.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(Cart_Items.objects.filter(cart_user=self.cart_user, menu=menu2).exists())

    def test_cart_update_view(self):
        response = self.client.post(reverse('orders:update_cart'), {'action': 'increase', 'menu_id': self.menu.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['message'], 'Cart updated successfully')
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)

    @patch('orders.views.order_confirmation_email.delay')
    def test_after_checkout_delete_cart_items(self, mock_email):
        data = {
            'vehicle_number': 'TN01AB1234',
            'pickup_time': '12:00:00'
        }
        
        response = self.client.post(reverse('orders:checkout'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        cart_items_exists = Cart_Items.objects.filter(cart_user=self.cart_user).exists()
        self.assertFalse(cart_items_exists)

    @patch('orders.views.order_confirmation_email.delay')
    def test_cart_items_after_order_creation(self, mock_email):
        data = {
            'vehicle_number': 'TN01AB1234',
            'pickup_time': '12:00:00'
        }
        
        response = self.client.post(reverse('orders:checkout'), data)
        self.assertEqual(response.status_code, 200)
        
        created_order = Order.objects.get(cart_user=self.cart_user)
        self.assertEqual(created_order.total_amount, 10.0)
        self.assertEqual(created_order.vehicle_number, 'TN01AB1234')
        self.assertTrue(OrderItem.objects.filter(order=created_order, menu=self.menu).exists())
        self.assertEqual(OrderItem.objects.get(order=created_order, menu=self.menu).quantity, 1)

    def test_cart_increase_decrease(self):
        self.client.post(reverse('orders:update_cart'), {'action': 'increase', 'menu_id': self.menu.id})
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)
        
        self.client.post(reverse('orders:update_cart'), {'action': 'decrease', 'menu_id': self.menu.id})
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 1)

    def test_cart_delete(self):
        response = self.client.post(reverse('orders:update_cart'), {'action': 'decrease', 'menu_id': self.menu.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Cart_Items.objects.filter(id=self.cart_item.id).exists())

    