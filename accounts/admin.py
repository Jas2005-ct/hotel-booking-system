from django.contrib import admin
from django.contrib.sessions.models import Session
# Register your models here.
from accounts.models import *

admin.site.register(CustomUser)
admin.site.register(Menu)
admin.site.register(TableLayout)

class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'expire_date')
    readonly_fields = ('session_key', 'expire_date')

    def decoded_data(self, obj):
        return obj.get_decoded()

    decoded_data.short_description = 'Session Data'


admin.site.register(Session, SessionAdmin)
