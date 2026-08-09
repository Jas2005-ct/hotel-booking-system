from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser, Menu, TableLayout
from orders.models import Order, OrderItem, Cart_User
from table_reservation.models import TableAssign, TableReservation
from admin_report.views import AdminHomeView
from django.utils import timezone
from datetime import timedelta
import datetime

class TestAdminDashboard(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_url = reverse('admin_report:admin_home')
        
        self.admin_user = CustomUser.objects.create_user(
            email='admin@example.com', password='password123', role='admin', name='Admin', phone_no=1234567890
        )
        self.waiter_user = CustomUser.objects.create_user(
            email='waiter@example.com', password='password123', role='waiter', name='Waiter', phone_no=1234567891
        )
        self.guest_user = CustomUser.objects.create_user(
            email='guest@example.com', password='password123', role='guest', name='Guest', phone_no=1234567892
        )
        
        self.menu_item = Menu.objects.create(
            name='Pizza', price=100, food_category='Italian', images='pizza.jpg', description='Tasty'
        )
        
        self.cart_user = Cart_User.objects.create(user=self.guest_user)
        
        self.order1 = Order.objects.create(
            cart_user=self.cart_user,
            total_amount=200,
            status='progress',
            vehicle_number='TN01'
        )
        
        OrderItem.objects.create(
            cart_user=self.cart_user, order=self.order1, menu=self.menu_item, quantity=2
        )
        
        self.order2 = Order.objects.create(
            cart_user=self.cart_user,
            total_amount=100,
            status='ready',
            vehicle_number='TN02'
        )
        OrderItem.objects.create(
            cart_user=self.cart_user, order=self.order2, menu=self.menu_item, quantity=1
        )
        
        # Create Tables
        self.table = TableLayout.objects.create(
            table_no=1, capacity=4, available=True, floor_no=1, Location='indoor'
        )
        
        self.reservation = TableReservation.objects.create(
            user=self.guest_user,
            table=self.table,
            duration=timedelta(hours=1),
            time_schedule=timezone.now().date(),
            start_time=timezone.now().time(),
            seat=4
        )
        
        self.table_assign = TableAssign.objects.create(
            tabereservation=self.reservation,
            waiter=self.waiter_user,
            assigned=True,
            completed=False
        )

    def test_admin_access(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_home.html')

    def test_unauthenticated_access(self):
        response = self.client.get(self.admin_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(response.status_code == 302)

    def test_dashboard_stats(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['total_revenue'], 300)
        self.assertEqual(context['total_orders_count'], 2)
        self.assertEqual(context['status_counts_progress']['p'], 1)
        self.assertEqual(context['status_counts_ready']['ready'], 1)
        self.assertEqual(context['tables_assigned'], 1)
        
    def test_top_products(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.admin_url)
        top_products = response.context['top_products']
        self.assertTrue(len(top_products) > 0)
        self.assertEqual(top_products[0]['menu__name'], 'Pizza')
        self.assertEqual(top_products[0]['total_sold'], 3)

    def test_table_reserved_ajaxdatatable(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_report:table_list'))
        self.assertEqual(response.status_code, 200)

    def test_order_list_admin(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_report:order_list'))
        self.assertEqual(response.status_code, 200)

    def test_live_order_list_admin(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_report:live_order'))
        self.assertEqual(response.status_code, 200)

    def test_order_details_admin(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_report:order_detail', args=[self.order1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order_detail_admin.html')
        self.assertEqual(response.context['order_det'], self.order1)
        self.assertEqual(len(response.context['order_item']), 1) # Only 1 row in order_items for order1

    def test_table_assigned(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 200)
        assigned_tables = response.context['tables']
        self.assertEqual(assigned_tables.count(), 1)
        self.assertEqual(assigned_tables.first(), self.table_assign)
        self.assertEqual(response.context['tables_assigned'], 1)

    def test_all_orders(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_orders_count'], 2)
        self.assertEqual(len(response.context['recent_orders']), 2)

    def test_table_revenue(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_revenue'], 300)

    def test_order_list_template(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_report:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order_list_admin.html')

    def test_table_list_template(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_report:table_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table_list_admin.html')

    def test_order_list_datatable(self):
        self.client.force_login(self.admin_user)
        url = reverse('admin_report:order_list_data')
        data = {'draw': 1, 'start': 0, 'length': 10}
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_table_list_datatable(self):
        self.client.force_login(self.admin_user)
        url = reverse('admin_report:table_list_data')
        data = {'draw': 1, 'start': 0, 'length': 10}
        response = self.client.get(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)