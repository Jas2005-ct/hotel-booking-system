from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import TableReservation

class TableReservationForm(forms.ModelForm):
    class Meta:
        model = TableReservation
        fields = ['seat', 'time_schedule', 'start_time']
        widgets = {
            'time_schedule': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_seat(self):
        seat = self.cleaned_data.get('seat')
        if seat is None:
            raise forms.ValidationError("Seat is required.")
        if seat < 1:
            raise forms.ValidationError("Seat must be greater than 0.")
        return seat

    def clean_time_schedule(self):
        time_schedule = self.cleaned_data.get('time_schedule')
        if not time_schedule:
            raise forms.ValidationError("Date is required.")

        today = timezone.now().date()
        if time_schedule < today:
            raise forms.ValidationError("You can't book a table for a past date.")

        return time_schedule

    def clean_start_time(self):
        st_time = self.cleaned_data.get('start_time')
        time_sch = self.cleaned_data.get('time_schedule')

        if not st_time or not time_sch:
            return st_time

        now = timezone.now()
        selected_dt = timezone.make_aware(
            datetime.combine(time_sch, st_time)
        )

        if selected_dt < now:
            raise forms.ValidationError("You can't book a table in the past.")



        return st_time
