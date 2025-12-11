from django.contrib import admin

# Register your models here.
from table_reservation.models import TableReservation,TableAssign

admin.site.register(TableReservation)
admin.site.register(TableAssign)
