from django.db import models

# Create your models here.
from accounts.models import CustomUser,TableLayout

class TableReservation(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    table = models.ForeignKey(TableLayout,on_delete=models.CASCADE)
    duration = models.DurationField()
    time_schedule = models.DateTimeField()
    
    def __str__(self):
        return f"{self.user.name} - {self.table.table_no}"

class TableAssign(models.Model):
    tabereservation = models.ForeignKey(TableReservation,on_delete=models.CASCADE)
    waiter = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    assigned = models.BooleanField(default=False)
    
    
    
    def __str__(self):
        return f"{self.tabereservation.user.name} - {self.tabereservation.table.table_no} - {self.waiter.name}"

# class Cart_User(models.Model):
#     user = models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    
#     def __str__(self):
#         return self.user.name

# class CartItem(models.Model):
#     cart_user = models.ForeignKey(Cart_User,on_delete=models.CASCADE)
#     menu = models.ForeignKey(Menu,on_delete=models.CASCADE)
#     quantity = models.IntegerField(default=1)
    
#     def __str__(self):
#         return self.menu.name 

# class OrderMenu(models.Model):
#     user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
#     cart_items = models.ForeignKey(CartItem,on_delete=models.CASCADE)
#     total_price = models.DecimalField(max_digits=10,decimal_places=2)
#     order_time = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):  
#         return f"{self.user.name} - {self.cart_items.menu.name} - {self.cart_items.quantity}"
    
#     def get_total_price(self):
#         total_price = 0
#         for i in self.cart_items:
#             total_price += i.menu.price * i.quantity
#         return total_price
    
#     def save(self, *args, **kwargs):
#         self.total_price = self.get_total_price()
#         super().save(*args, **kwargs)
