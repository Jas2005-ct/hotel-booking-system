from django.template.loader import render_to_string
from django.shortcuts import render
from accounts.models import CustomUser, TableLayout, Menu, RoleChoices
from table_reservation.forms import TableReservationForm
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from table_reservation.models import TableReservation, TableAssign
import json
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from datetime import timedelta, datetime
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Exists, OuterRef, Subquery
from table_reservation.tasks import table_reservation_guest, reminder_before_one_hour
from common.decorators import role_required
@login_required(login_url='/accounts/login/')
@user_passes_test(lambda u: u.role == RoleChoices.GUEST, login_url='/accounts/login/')
def GuestView(request):
    menu = Menu.objects.all()
    waiter_name = TableAssign.objects.filter(tabereservation=OuterRef('pk')).order_by('-id').values('waiter__name')[:1]
    waiter_phone = TableAssign.objects.filter(tabereservation=OuterRef('pk')).order_by('-id').values('waiter__phone_no')[:1]
    is_assigned = TableAssign.objects.filter(tabereservation=OuterRef('pk'), assigned=True)
    is_completed = TableAssign.objects.filter(tabereservation=OuterRef('pk'), completed=True)
    reservations = TableReservation.objects.filter(user=request.user).select_related('table').annotate(
        waiter_name=Subquery(waiter_name),
        waiter_phone=Subquery(waiter_phone),
        assigned=Exists(is_assigned),
        completed=Exists(is_completed)
    )
    upcoming_reservations = reservations.filter(
        time_schedule__gte=timezone.now().date(),
        completed=False
    ).order_by('time_schedule', 'start_time')
    past_reservations = reservations.filter(
        completed=True
    ).union(
        reservations.filter(time_schedule__lt=timezone.now().date())
    ).order_by('-time_schedule', '-start_time')

    context = {
        'menus': menu,
        'upcoming_reservations': upcoming_reservations,
        'past_reservations': past_reservations,
    }
    

    return render(request, 'guest_home.html', context)

@login_required(login_url='/accounts/login/')
@permission_required('table_reservation.add_tablereservation', raise_exception=True)
def TableReserverView(request):
    if request.method == 'POST':
        try:
            form = TableReservationForm(request.POST)
            if not form.is_valid():
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                },status=400)
            seat = int(form.cleaned_data['seat'])
            now = timezone.now() 
            today = now.date()
            now_one_hour = now + timedelta(minutes=90)
            current_time_schedule = form.cleaned_data['time_schedule']
            current_start_time = form.cleaned_data['start_time']
            start_dt = datetime.combine(current_time_schedule, current_start_time)
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
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
                if today == current_time_schedule and now <= start_dt <= now_one_hour :
                    table_no.available = False
                    table_no.save()
                table_reservation_guest.delay(created.id)
                return JsonResponse({'success':True,'message':'Table Reserved Successfully'})
            except Exception as e:
                return JsonResponse({'success':False,'message':str(e)})
        except Exception as e:
            return JsonResponse({'success':False,'message':str(e)})
    else:
        form = TableReservationForm()
        return render(request,'table_book_form.html',{'form':form})

class TableReservedView(LoginRequiredMixin,PermissionRequiredMixin, View):
    permission_required = ('table_reservation.view_tablereservation')
    def get(self, request):
        date = timezone.now().date()
        waiter_name = TableAssign.objects.filter(
            tabereservation=OuterRef('pk')
        ).order_by('-id').values('waiter__name')[:1]

        

        waiter_id = TableAssign.objects.filter(tabereservation = OuterRef('pk')).order_by('-id').values('waiter__id')[:1]
        
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
            waiter_id=Subquery(waiter_id),
            assigned=Exists(is_assigned),
            completed=Exists(is_completed)
        )
        upcoming_reservations = reservations.filter(time_schedule__gte=date,completed=False).order_by('-time_schedule','-start_time')
        
        past_reservations = reservations.filter(completed=True).order_by('-time_schedule','-start_time')
        table_res = TableAssign.objects.select_related('tabereservation','waiter').order_by('-id') 
        context = {
            'upcoming_reservations': upcoming_reservations,
            'past_reservations': past_reservations,
            'table_res':table_res
        }
        return render(request, 'table_reserved.html', context)

class TableAssignView(LoginRequiredMixin,PermissionRequiredMixin, View):
    permission_required = ('table_reservation.change_tableassign')
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

class TableUnassignView(LoginRequiredMixin,PermissionRequiredMixin, View):
    permission_required = 'table_reservation.change_tableassign'
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
            table_layout = assignment.tabereservation.table
            table_layout.available = True
            table_layout.save()
            assignment.completed = True
            assignment.assigned = False
            assignment.save()
            
            return JsonResponse({'success': True, 'message': 'Table checked out Successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

class DeleteTableReservation(LoginRequiredMixin, View):
    def post(self, request):
        try:
            table_reservation_id = request.POST.get('pk')
            user = request.user
            try:
                reservation = TableReservation.objects.get(pk=table_reservation_id)
                if reservation.user != user and user.role != 'admin':
                    return JsonResponse({'success': False, 'message': 'You are not authorized to delete this reservation'})
            except TableReservation.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Table reservation not found'})
            now = timezone.now()
            booking_dt = datetime.combine(reservation.time_schedule, reservation.start_time)
            if timezone.is_naive(booking_dt):
                booking_dt = timezone.make_aware(booking_dt, timezone.get_current_timezone())
            if booking_dt < now:
                 return JsonResponse({'success': False, 'message': 'Cannot delete past reservations'})
            is_assigned = TableAssign.objects.filter(tabereservation=reservation, assigned=True).exists()
            if is_assigned:
                time_remaining = booking_dt - now
                if time_remaining < timedelta(hours=2):
                    return JsonResponse({
                        'success': False, 
                        'message': 'Cannot delete confirmed reservation less than 2 hours before start.'
                    })
            reservation.delete()
            reservation.table.available = True
            reservation.table.save()
            
            return JsonResponse({'success': True, 'message': 'Reservation deleted successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})