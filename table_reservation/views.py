from django.shortcuts import render
from accounts.models import CustomUser,TableLayout
from table_reservation.forms import TableReservationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse,JsonResponse
from django.views import View
from django.views.generic import CreateView,UpdateView,DeleteView
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from accounts.models import Menu,TableLayout
from table_reservation.models import TableReservation,TableAssign
import json
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef,Subquery


@login_required(login_url='/accounts/login/')
@user_passes_test(lambda u: u.role == 'guest', login_url='/accounts/login/')
def GuestView(request):
    menu = Menu.objects.all()
    tables = TableLayout.objects.filter(available=True)
    context = {
        'menus':menu,
        'tables':tables
    }
    return render(request,'guest_home.html',context)


def TableReserverView(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            form = TableReservationForm(data)
            if form.is_valid():
                reserve = form.save(commit=False)
                reserve.user = request.user
                table_no = data.get('table_no')
                try:
                    table = TableLayout.objects.get(table_no=table_no)
                    reserve.table = table
                    reserve.save()
                    table.available = False
                    table.save()
                    return JsonResponse({'success':True,'message':'Table Reserved Successfully'})
                except TableLayout.DoesNotExist:
                    return JsonResponse({'success':False,'message':'Table Not Reserved'})
            else:
                return JsonResponse({'success':False,'message':form.errors.as_text()})

        except json.JSONDecodeError:
            return JsonResponse({'success':False,'message':'Invalid JSON Data'})
        except Exception as e:
            return JsonResponse({'success':False,'message':str(e)})
    else:
        form = TableReservationForm()
        return render(request,'table_book_form.html',{'form':form})

class TableReservedView(LoginRequiredMixin,View):
    def get(self,request):
        reserved = TableReservation.objects.filter(time_schedule__gte=timezone.now()).select_related('table')
        assigned_status = TableAssign.objects.filter(tabereservation__in=OuterRef('pk'),assigned=True)
        waiter_name = TableAssign.objects.filter(tabereservation__in=OuterRef('pk'),assigned=True).values('waiter__name')[:1]
        reserved = reserved.annotate(assigned=Exists(assigned_status),waiter_name=Subquery(waiter_name))
        context = {
            'table':reserved
        }
        return render(request,'table_reserved.html',context)

class TableAssignView(LoginRequiredMixin,View):
    def post(self,request):
        try:
            waiter = request.user
            table = request.POST.get('pk')
            try:
                assign = TableAssign.objects.create(tabereservation=TableReservation.objects.get(pk=table),waiter=waiter,assigned=True)
                return JsonResponse({'success':True,'message':'Table Assigned Successfully'})
            except TableReservation.DoesNotExist:
                return JsonResponse({'success':False,'message':'Table Not Found'})
            except Exception as e:
                return JsonResponse({'success':False,'message':str(e)})
        except Exception as e:
            return JsonResponse({'success':False,'message':str(e)})