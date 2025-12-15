from django.forms import ModelForm
from orders.models import order
from django import forms
class OrderForm(ModelForm):
    class Meta:
        model = order
        fields = ['pickup_time','vechile_number']

        widgets = {
            'pickup_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            )
        }
