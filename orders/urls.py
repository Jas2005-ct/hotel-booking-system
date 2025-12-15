from django.urls import path
from orders.views import *
from django.views import View

app_name = 'orders'

urlpatterns = [
    path('cart-create/', CartCreateView.as_view(), name='cart-create'),
    path('update_cart/', update_cart, name='update_cart'),
    path('checkout/', OrderCreateView.as_view(), name='checkout'),
    path('order-list/', OrderListView.as_view(), name='order-list'),
    path('kitchen-staff/', KitchenStaffView.as_view(), name='kitchen-staff'),
    path('service-staff/', ServiceStaffView.as_view(), name='service-staff'),
]