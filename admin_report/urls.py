from django.urls import path
from admin_report.views import *

app_name = 'admin_report'

urlpatterns = [
    path('', AdminHomeView.as_view(), name='admin_home'),
    path('order-list/', order_list, name='order_list'),
    path('order-list-data/', OrderListView.as_view(), name='order_list_data'),
    path('order-detail/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('table-list/',TableList.as_view(),name='table_list'),
    path('table-list-data/',TableListView.as_view(),name='table_list_data'),
]