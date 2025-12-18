from django.forms import ModelForm
from orders.models import order
from django import forms
class OrderForm(ModelForm):
    pickup_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}), required=True)
    class Meta:
        model = order
        fields = ['pickup_time','vechile_number']

