from django.db.models.expressions import OuterRef
from django.shortcuts import render
from orders.models import *
from django.views.generic import ListView, DetailView
from django.views import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin,PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from orders.forms import OrderForm
from django.db.models import Prefetch
from orders.tasks import order_confirmation_email
from django.contrib import messages
from django.shortcuts import redirect
from common.mixins import RoleRequiredMixin


def orders(request):
    orders = order_items.objects.filter(order = OuterRef('pk')).select_related('menu')
    for i in orders:
        print(i.cart_user.user.name)
        print(i.order.waiter.user.name)