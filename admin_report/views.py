from django.shortcuts import render
from accounts.models import *
from table_reservation.models import *
from orders.models import *
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin

class AdminHomeView(LoginRequiredMixin,View):
    # permission_required = 'admin_report.admin_home'
    def get(self, request):
        from django.db.models import Sum, Count

        # Fetch active table assignments
        tables_assigned = TableAssign.objects.select_related('tabereservation__table', 'waiter').filter(completed=False)
        # Fix: Field name is 'tabereservation', not 'TableReservation'
        
        all_orders = order.objects.all().order_by('-order_date')
        
        # Calculate stats
        total_revenue = all_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_orders_count = all_orders.count()
        
        # Active tables: assigned but not completed
        active_tables_count = TableAssign.objects.filter(assigned=True, completed=False).count()
        
        # Recent orders (limit to 10 for display)
        recent_orders = all_orders[:10]
        
        context = {
            'tables': tables_assigned,
            'recent_orders': recent_orders,
            'total_revenue': total_revenue,
            'total_orders_count': total_orders_count,
            'active_tables_count': active_tables_count,
        }
        
        return render(request, 'admin_home.html', context)
