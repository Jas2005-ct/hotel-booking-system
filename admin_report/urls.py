from django.urls import path
from admin_report.views import *

app_name = 'admin_report'

urlpatterns = [
    path('', AdminHomeView.as_view(), name='admin_home'),
]