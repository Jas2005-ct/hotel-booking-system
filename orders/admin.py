from django.contrib import admin

# Register your models here.
from orders.models import Cart_User, Cart_Items, Order, OrderItem, OrderKitchenStaff

admin.site.register(Cart_User)
admin.site.register(Cart_Items)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderKitchenStaff)
