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
from table_reservation.tasks import table_reservation_guest


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
            time_sch = data.get('time_schedule')
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
                    table_reservation_guest.delay(request.user.id,time_sch)
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

class TableReservedView(LoginRequiredMixin, View):
    def get(self, request):
        now = timezone.now()
        waiter_name = TableAssign.objects.filter(
            tabereservation=OuterRef('pk')
        ).order_by('-id').values('waiter__name')[:1]
        
        is_assigned = TableAssign.objects.filter(
            tabereservation=OuterRef('pk'),
            assigned=True
        )
        reservations = TableReservation.objects.select_related('table', 'user').annotate(
            waiter_name=Subquery(waiter_name),
            assigned=Exists(is_assigned)
        )
        upcoming_reservations = reservations.filter(time_schedule__gte=now).order_by('time_schedule')
        
        past_reservations = reservations.filter(time_schedule__lt=now).order_by('-time_schedule')
        context = {
            'upcoming_reservations': upcoming_reservations,
            'past_reservations': past_reservations,
        }
        return render(request, 'table_reserved.html', context)

class TableAssignView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            waiter = request.user
            table_id = request.POST.get('pk')
        
            if TableAssign.objects.filter(tabereservation_id=table_id, assigned=True).exists():
                return JsonResponse({'success': False, 'message': 'Table is already assigned'})

            try:
                reservation = TableReservation.objects.get(pk=table_id)
                TableAssign.objects.create(tabereservation=reservation, waiter=waiter, assigned=True)
                return JsonResponse({'success': True, 'message': 'Table Assigned Successfully'})
            except TableReservation.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Table Not Found'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

class TableUnassignView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            waiter = request.user
            table_reservation_id = request.POST.get('pk')
            
            try:
                assignment = TableAssign.objects.get(tabereservation_id=table_reservation_id, assigned=True)
            except TableAssign.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Active assignment not found'})
            except TableAssign.MultipleObjectsReturned:
                assignment = TableAssign.objects.filter(tabereservation_id=table_reservation_id, assigned=True).first()

            if assignment.waiter != waiter:
                return JsonResponse({'success': False, 'message': 'You are not authorized to unassign this table'})
            
            # Update TableLayout availability
            table_layout = assignment.tabereservation.table
            table_layout.available = True
            table_layout.save()
            
            # Update Assignment status
            assignment.assigned = False
            assignment.completed = True
            assignment.save()
            
            return JsonResponse({'success': True, 'message': 'Table checked out Successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})