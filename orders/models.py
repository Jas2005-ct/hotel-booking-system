from django.db import models

# Create your models here.
from accounts.models import CustomUser,Menu


class Cart_User(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    def __str__(self):
        return self.user.name

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
    cart_user = models.ForeignKey(Cart_User,on_delete=models.CASCADE)
    total_amount = models.IntegerField()
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100,default='ready')
    
    def __str__(self):
        return self.cart_user.user.name
    
class order_items(models.Model):
    order = models.ForeignKey(order,on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    
    def __str__(self):
        return f'{self.menu.name} - {self.quantity}'