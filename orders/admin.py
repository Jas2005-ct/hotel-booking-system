from django.contrib import admin

# Register your models here.
from orders.models import *

admin.site.register(Cart_User)
admin.site.register(Cart_Items)
admin.site.register(order)
admin.site.register(order_items)
