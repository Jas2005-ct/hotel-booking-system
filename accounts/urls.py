from django.urls import path
from accounts.views import (AdminUserView,
WaiterUserView,
GuestUserView,
KitchenUserView,
ManagementView,
login_view,
logout_view,
MenuCreate,
TableCreate,
MenuDelete,
TableDelete,
TableStatus,
MenuUpdate,
TableUpdate,



)

app_name = 'accounts'
urlpatterns =[
    path('adminuser/',AdminUserView.as_view(),name='adminuser'),
    path('waiteruser/',WaiterUserView.as_view(),name='waiteruser'),
    path('guestuser/',GuestUserView.as_view(),name='guestuser'),
    path('kitchenuser/',KitchenUserView.as_view(),name='kitchenuser'),
    path('login/',login_view,name='login'),
    path('logout/',logout_view,name='logout'),
    path('menucreate/',MenuCreate.as_view(),name='menucreate'),
    path('menuupdate/<int:pk>/',MenuUpdate.as_view(),name='menuupdate'),
    path('tablecreate/',TableCreate.as_view(),name='tablecreate'),
    path('tableupdate/<int:pk>/',TableUpdate.as_view(),name='tableupdate'),
    path('menudelete/<int:pk>/',MenuDelete.as_view(),name='menudelete'),
    path('tabledelete/<int:pk>/',TableDelete.as_view(),name='tabledelete'),
    path('tablestatus/<int:pk>/',TableStatus.as_view(),name='tablestatus'),
    path('',ManagementView,name='management'),
    
]