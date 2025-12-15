from django.db import models

# Create your models here.
from accounts.models import CustomUser,Menu


class Cart_User(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    def __str__(self):
        return f'{self.user.id}-{self.user.name}'

class Cart_Items(models.Model):
    cart_user = models.ForeignKey(Cart_User,on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    
    def __str__(self):
        return f'{self.menu.name} - {self.quantity}'

    @property
    def total_price(self):
        return self.menu.price * self.quantity

class order(models.Model):
    status_choice = (
        ('progress','progress'),
        ('ready','ready'),
        ('completed','completed'),
        ('cancelled','cancelled')
    )
    cart_user = models.ForeignKey(Cart_User,on_delete=models.CASCADE)
    kitchen_staff = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='kitchen_staff',null=True,blank=True)
    waiter = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='waiter',null=True,blank=True)
    total_amount = models.IntegerField()
    order_date = models.DateTimeField(auto_now_add=True)
    pickup_time = models.TimeField(blank=True,null=True)
    vechile_number = models.CharField(max_length=100)
    status = models.CharField(max_length=100,choices=status_choice,default='progress')
    
    def __str__(self):
        return f'{self.id} - {self.cart_user.user.id}'
    
class order_items(models.Model):
    cart_user = models.ForeignKey(Cart_User,on_delete=models.CASCADE)
    order = models.ForeignKey(order,on_delete=models.CASCADE,related_name='order_items')
    menu = models.ForeignKey(Menu,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    
    def __str__(self):
        return f'{self.order.id} - {self.menu.name} - {self.quantity}'

class order_kitchen_staff(models.Model):
    order = models.OneToOneField(order,on_delete=models.CASCADE)
    kitchen_staff = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.order.id} - {self.kitchen_staff.name}'