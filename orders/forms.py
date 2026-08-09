from django.forms import ModelForm
from orders.models import Order
from django import forms
class OrderForm(ModelForm):
    pickup_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}), required=True)
    class Meta:
        model = Order
        fields = ['pickup_time','vehicle_number']

