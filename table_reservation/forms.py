from table_reservation.models import TableReservation
from django import forms
from django.utils import timezone
from datetime import timedelta

class TableReservationForm(forms.ModelForm):
    duration = forms.IntegerField(min_value=15,max_value=90)
    class Meta:
        model = TableReservation
        fields = ['duration','time_schedule']
        widgets = {
            'time_schedule': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean_time_schedule(self):
        time_schedule = self.cleaned_data.get('time_schedule')
        now = timezone.now()
        one_hour_from_now = now + timedelta(hours=1)
        if time_schedule < now:
            raise forms.ValidationError("You can't book a table for a past time.")
        if time_schedule < one_hour_from_now:
            raise forms.ValidationError("You can't book a table for less than an hour.")
        return time_schedule
    
    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if duration < 15 or duration > 90:
            raise forms.ValidationError("Duration must be at least 15 minutes and less than 90 minutes.")
        return timedelta(minutes=duration)


    

