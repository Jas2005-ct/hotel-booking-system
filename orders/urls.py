from django.urls import path
from orders.views import *
from django.views import View

app_name = 'orders'

urlpatterns = [
    path('cart-create/', CartCreateView.as_view(), name='cart-create'),
    path('update_cart/', update_cart, name='update_cart'),
]