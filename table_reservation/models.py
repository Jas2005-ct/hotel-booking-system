from django.db import models

# Create your models here.
from accounts.models import CustomUser,TableLayout

class TableReservation(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    table = models.ForeignKey(TableLayout,on_delete=models.CASCADE)
    duration = models.DurationField()
    time_schedule = models.DateField(null=True,blank=True)
    start_time = models.TimeField(null=True,blank=True)
    end_time = models.TimeField(null=True,blank=True)
    seat = models.IntegerField(null=True,blank=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.table.table_no}"

class TableAssign(models.Model):
    tabereservation = models.ForeignKey(TableReservation,on_delete=models.CASCADE)
    waiter = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    assigned = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    
    
    
    def __str__(self):
        return f"{self.tabereservation.user.name} - {self.tabereservation.table.table_no} - {self.waiter.name}"

