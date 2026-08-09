from django.forms import ModelForm
from accounts.models import CustomUser,Menu,TableLayout
from django.contrib.auth.models import Group
from django import forms

class CustomUserForm(ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['name','email','phone_no','password','confirm_password' ]
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean_phone_no(self):
        phone_no = str(self.cleaned_data.get('phone_no'))
        if len(phone_no) != 10:
            raise forms.ValidationError("Phone number must be 10 digits")
        elif CustomUser.objects.filter(phone_no=phone_no).exists():
            raise forms.ValidationError("Phone number already exists")
        return phone_no

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if any(char in "!@#$%^&*()_+={}[]|:;'<>,./?" for char in name):
             raise forms.ValidationError("Name cannot contain special characters")
        return name
    
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class MenuForm(ModelForm):
    class Meta:
        model = Menu
        fields = ['name','price','description','images','food_type','food_category']

class TableLayoutForm(ModelForm):
    class Meta:
        model = TableLayout
        fields = ['table_no','floor_no','Location','capacity','available',]
    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity < 1 or capacity > 15:
            raise forms.ValidationError("Capacity must be between 1 and 15")
        return capacity
