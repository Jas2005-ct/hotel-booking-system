from django.template.loader import render_to_string
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
from django.core.exceptions import ValidationError,ObjectDoesNotExist
from datetime import timedelta,datetime
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef,Subquery


@login_required(login_url='/accounts/login/')
@user_passes_test(lambda u: u.role == 'guest', login_url='/accounts/login/')
def GuestView(request):
    menu = Menu.objects.all()
    tables = TableReservation.objects.filter(user=request.user).select_related('table')
    tables_assigned = TableAssign.objects.filter(tabereservation__user=request.user).first()
    context = {
        'menus':menu,
        'tables':tables,
        'tables_assigned':tables_assigned
    }
    return render(request,'guest_home.html',context)


def TableReserverView(request):
    if request.method == 'POST':
        try:
            form = TableReservationForm(request.POST)
            if not form.is_valid():
                return JsonResponse({
                    'success': False,
                    'message': render_to_string(
                        'table_book_form.html',
                        {'form': form},
                        request=request
                    )
                })
            seat = int(form.cleaned_data['seat'])
            current_time_schedule = form.cleaned_data['time_schedule']
            current_start_time = form.cleaned_data['start_time']
            start_dt = datetime.combine(current_time_schedule, current_start_time)
            duration = timedelta(minutes=90)    
            current_end_time = start_dt + duration
            matched_table = TableLayout.objects.filter(capacity__gte=seat)
            confict_table = TableReservation.objects.filter(time_schedule=current_time_schedule,start_time__lte=current_end_time,end_time__gte=current_start_time).values_list('table_id',flat=True)
            available_tab = matched_table.exclude(table_no__in=confict_table)
            if not available_tab.exists():
                return JsonResponse({'success':False,'message':'No available table for the selected time'})
            try:
                table_no = available_tab.first()
                created = TableReservation.objects.create(user=request.user,table=table_no,seat=seat,duration=duration,time_schedule=current_time_schedule,start_time=current_start_time,end_time=current_end_time)
                table_no.availabe=False
                table_no.save()
                print(created)
                return JsonResponse({'success':True,'message':'Table Reserved Successfully'})
            except Exception as e:
                return JsonResponse({'success':False,'message':str(e)})
        except Exception as e:
            return JsonResponse({'success':False,'message':str(e)})
    else:
        form = TableReservationForm()
        return render(request,'table_book_form.html',{'form':form})

class TableReservedView(LoginRequiredMixin, View):
    def get(self, request):
        date = timezone.now().date()
        waiter_name = TableAssign.objects.filter(
            tabereservation=OuterRef('pk')
        ).order_by('-id').values('waiter__name')[:1]
        
        is_assigned = TableAssign.objects.filter(
            tabereservation=OuterRef('pk'),
            assigned=True
        )
        is_completed = TableAssign.objects.filter(
            tabereservation=OuterRef('pk'),
            completed=True
        )
        reservations = TableReservation.objects.select_related('table', 'user').annotate(
            waiter_name=Subquery(waiter_name),
            assigned=Exists(is_assigned),
            completed=Exists(is_completed)
        )
        upcoming_reservations = reservations.filter(time_schedule__gte=date).order_by('-time_schedule','-start_time')
        
        past_reservations = reservations.filter(time_schedule__lt=date,completed=True).order_by('-time_schedule','-start_time')
        if request.user.role == 'admin':
            table_res = TableAssign.objects.select_related('tabereservation','waiter').order_by('-id')
        else:
            table_res = TableAssign.objects.select_related('tabereservation','waiter').filter(tabereservation__user=request.user).order_by('-id')
        context = {
            'upcoming_reservations': upcoming_reservations,
            'past_reservations': past_reservations,
            'table_res':table_res
        }
        return render(request, 'table_reserved.html', context)

class TableAssignView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            waiter = request.user
            table_id = request.POST.get('pk')
            if TableAssign.objects.filter(tabereservation_id=table_id, assigned=True, completed=True).exists():
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
            
            # Get the active assignment
            try:
                assignment = TableAssign.objects.get(tabereservation_id=table_reservation_id, assigned=True)
            except TableAssign.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Active assignment not found'})
            except TableAssign.MultipleObjectsReturned:
                # Fallback if multiple exist, though shouldn't happen with proper logic
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