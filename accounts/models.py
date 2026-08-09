from django.db import models
from django.core.validators import RegexValidator

# Create your models here.
from django.contrib.auth.models import AbstractUser, BaseUserManager

class RoleChoices(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    KITCHEN_STAFF = 'kitchen_staff', 'Kitchen Staff'
    WAITER = 'waiter', 'Waiter'
    GUEST = 'guest', 'Guest'

class CustomManager(BaseUserManager):
    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError("Email Must Need!!")
        email = self.normalize_email(email)
        user = self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save()
        return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', RoleChoices.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    phone_regex = RegexValidator(
        regex=r'^\+?[\d\s\-]{7,20}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 20 digits allowed."
    )
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    phone_no = models.CharField(max_length=20, validators=[phone_regex])
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name','phone_no']
    objects = CustomManager()

    def __str__(self):
        return self.email
    
class Menu(models.Model):
    food_type_choice = (
        ('veg','veg'),
        ('non-veg','non-veg'),
    )
    food_category = (
        ('starters','starters'),
        ('main_course','main_course'),
        ('dessert','dessert'),
        ('side_dish','side_dish'),
        ('indian','indian'),
        ('chinese','chinese'),
        ('italian','italian'),
        ('japanese','japanese'),
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    images = models.ImageField(upload_to='menu_images/',null=True,blank=True,default='images/default.jpg')
    food_type = models.CharField(max_length=100,choices=food_type_choice,null=True,blank=True)
    food_category = models.CharField(max_length=100,choices=food_category,null=True,blank=True)
    

    def __str__(self):
        return self.name

class TableLayout(models.Model):
    Location_choice = (
        ('Window_side','Window_side'),
        ('roof_top','roof_top'),
        ('indoor','indoor'),
        ('outdoor','outdoor'),
        ('suit_space','suit_space')
    )
    table_no = models.AutoField(primary_key=True)
    floor_no = models.IntegerField()
    Location = models.CharField(max_length=100,choices=Location_choice)
    capacity = models.IntegerField()
    available = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.table_no} - {self.capacity} - {self.available} - {self.Location}'