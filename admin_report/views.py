from django.shortcuts import render
from accounts.models import *
from table_reservation.models import *
from orders.models import Order, OrderItem, Cart_User, Cart_Items, OrderKitchenStaff
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum, Count, F, Q, Subquery
from django.db.models import OuterRef, Exists
from ajax_datatable.views import AjaxDatatableView
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest,HttpResponseForbidden

class AdminHomeView(LoginRequiredMixin,View):
    def get(self, request):
        tables_assigned = TableAssign.objects.select_related('tabereservation__table', 'waiter').filter(completed=False)
        all_orders = Order.objects.all().order_by('-created_at')
        total_revenue = all_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_orders_count = all_orders.count()
        today = datetime.now().date()
        orders_today = all_orders.filter(created_at__date=today)
        order_count = orders_today.count()
        status_counts_progress = all_orders.aggregate(p=Count('id', filter=Q(status='progress')))
        status_counts_ready = all_orders.aggregate(ready=Count('id', filter=Q(status='ready')))
        status_counts_completed = all_orders.aggregate(completed=Count('id', filter=Q(status='completed')))
        table_status_available = TableLayout.objects.filter(available=True).count()
        table_status_assigned = TableAssign.objects.filter(assigned=True, completed=False).count()
        table_status_completed_today = TableAssign.objects.filter(completed=True).count() 
        table_reserved_today = TableReservation.objects.filter(created_at__date__lte=today).count()
        
        recent_orders = all_orders[:5]
        top_products = OrderItem.objects.values('menu__name').annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('menu__price'))
        ).order_by('-total_sold')[:3]

        category_sales = OrderItem.objects.values('menu__food_category').annotate(
            count=Count('id'),
            revenue=Sum(F('quantity') * F('menu__price'))
        ).order_by('-revenue')


        cat_sales = OrderItem.objects.values('menu__food_type').annotate(
            count = Count('id')
        ).order_by('-count')

        total_items_sold = sum(item['count'] for item in cat_sales)

        context = {
            'tables': tables_assigned,
            'recent_orders': recent_orders,
            'total_revenue': total_revenue,
            'total_orders_count': total_orders_count,
            'orders_today_count': order_count,
            'status_counts_progress': status_counts_progress,
            'status_counts_ready': status_counts_ready,
            'status_counts_completed': status_counts_completed,
            'tables_available': table_status_available,
            'tables_assigned': table_status_assigned,
            'tables_completed_today': table_status_completed_today,
            'top_products': top_products,
            'category_sales': category_sales,
            'cat_sales': cat_sales,
            'total_items_sold': total_items_sold,
        }
        return render(request, 'admin_home.html', context)

def order_list(request):
    return render(request, 'order_list_admin.html')

class OrderListView(AjaxDatatableView):
    model = Order
    title = 'Order List'
    column_defs = [
        {'name': 'pk','orderable': True,'searchable': True},
        {'name': 'customer','foreign_field':'cart_user__user__name','orderable': True,'searchable': True},
        {'name': 'created_at','orderable': True,'searchable': False},
        {'name': 'total_amount','orderable': True,'searchable': False},
        {'name': 'view','orderable': False,'searchable': False}
    ]
    initial_order =[['created_at', 'desc']]


    def get_initial_queryset(self,request):
        return Order.objects.all().select_related('cart_user__user')

    def filter_queryset(self, params, queryset):
        queryset = super().filter_queryset(params, queryset)
        date_filter = self.request.GET.get('date')
        if date_filter:
            queryset = queryset.filter(order_date__date=date_filter)
        return queryset

    def render_column(self,row,column):
        if column == 'pk':
            return row.pk
        if column == 'customer':
            return row.cart_user.user.name
        if column == 'created_at':
            return row.created_at.strftime('%Y-%m-%d')
        if column == 'view':
            return (
                '<button type="button" '
                'class="btn btn-sm btn-primary" '
                'data-bs-toggle="modal" '
                'data-bs-target="#orderModal" '
                'data-order-id="%s">'
                '<i class="bi bi-eye"></i> View'
                '</button>'
            ) % row.pk
        return super().render_column(row,column) 


class OrderDetailView(View):
    def get(self,request,pk):
        order_instance = Order.objects.select_related('kitchen_staff','waiter').get(pk=pk)
        order_item = OrderItem.objects.filter(order=pk).select_related('menu')
        
        return render(request,'order_detail_admin.html',{'order_item':order_item,'order_det':order_instance}) 

class TableList(View):
    def get(self,request):
        return render(request,'table_list_admin.html')


class TableListView(AjaxDatatableView):  
    model = TableReservation
    title = 'Table List'
    column_defs = [
        {'name':'pk','orderable':True,'searchable':True},
        {'name':'table','foreign_field':'table__table_no','orderable':True,'searchable':True},
        {'name':'user','foreign_field':'user__name','orderable':True,'searchable':True},
        {'name':'time_schedule','orderable':True,'searchable':True},
        {'name':'start_time','orderable':True,'searchable':True},
        {'name':'status','orderable':False,'searchable':False},
        {'name':'waiter','orderable':True,'searchable':False}
    ]
    initial_order =[['pk', 'desc']]
    
    def get_initial_queryset(self,request):
        assigned_tables = TableAssign.objects.filter(tabereservation_id=OuterRef('pk'),assigned=True)
        completed_tables = TableAssign.objects.filter(tabereservation_id=OuterRef('pk'),completed=True)
        waiter_name = TableAssign.objects.filter(tabereservation_id=OuterRef('pk'),assigned=True).values('waiter__name')[:1]
        return TableReservation.objects.annotate(
            assigned=Exists(assigned_tables),
            completed=Exists(completed_tables),
            waiter_name=Subquery(waiter_name)
        )

    def filter_queryset(self,params,queryset):
        status = self.request.GET.get('status')
        date = self.request.GET.get('date')
        if status == 'assigned':
            queryset= queryset.filter(assigned=True)
        if status == 'completed':
            queryset= queryset.filter(completed=True)
        if status == 'not_assigned':
            queryset= queryset.filter(assigned=False)
        if date:
            queryset= queryset.filter(time_schedule=date)
        return queryset


    def render_column(self,row,column):
        if column == 'table':
            return row.table.table_no

        if column == 'waiter':
            if row.assigned == True:
                return row.waiter_name
            else:
                return 'Not Assigned'
        if column == 'status':
            if row.assigned == True: 
                if row.completed == True:
                    return '<span class="badge bg-success">Completed</span>'
                else:
                    return '<span class="badge bg-warning">Assigned</span>'
            else:
                return '<span class="badge bg-danger">Not Assigned</span>'
        return super().render_column(row,column)

class LiveOrderView(View):
    def get(self,request):
        orders = Order.objects.filter(status__in=['progress','ready']).select_related('cart_user__user').prefetch_related('order_items__menu')
        return render(request,'live_order.html',{'orders':orders})
        