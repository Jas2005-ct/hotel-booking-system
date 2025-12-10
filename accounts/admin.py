from django.contrib import admin

# Register your models here.
from accounts.models import *

admin.site.register(CustomUser)
admin.site.register(Menu)
admin.site.register(TableLayout)
