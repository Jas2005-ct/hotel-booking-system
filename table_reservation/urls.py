from django.urls import path
from table_reservation.views import GuestView,TableReserverView,TableReservedView,TableAssignView,TableUnassignView

app_name = 'table_reservation'

urlpatterns = [
    path('',GuestView,name='guesthome'),
    path('table_book_form/',TableReserverView,name='table_book_form'),
    path('table_reserved/',TableReservedView.as_view(),name='table_reserved'),
    path('table_assign/',TableAssignView.as_view(),name='table_assign'),
    path('table_unassign/',TableUnassignView.as_view(),name='table_unassign')
]   