from celery import shared_task
import time
from datetime import datetime,timedelta
from table_reservation.models import TableReservation, TableAssign
from accounts.models import CustomUser
from project_files import settings
from django.core.mail import send_mail,EmailMultiAlternatives
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q,F,OuterRef,Subquery

@shared_task
def send_welcome_email(user_id):
    user = CustomUser.objects.get(id=user_id)
    mail_subject = 'Welcome to our Hotel Management System'
    html_content = render_to_string('welcome_email.html', {'user': user})
    message = EmailMultiAlternatives(
        mail_subject,
        html_content,
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    message.attach_alternative(html_content, "text/html")
    message.send()

    return f'Email sent successfully to {user.email}'




@shared_task
def table_reservation_guest(reservation_id):
    reservation = TableReservation.objects.get(id=reservation_id)
    user = reservation.user
    time_schedule = reservation.time_schedule
    mail_subject = "Thank For Your reservation..!!"
    html_content = render_to_string('table_reservation_mail.html',{'user':user,'time_schedule':time_schedule})
    message = EmailMultiAlternatives(
        mail_subject,
        html_content,
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    message.attach_alternative(html_content,"text/html")
    message.send()

    return f'Remainder sent successfully'

@shared_task
def reminder_before_one_hour():
    now = timezone.localtime()
    one_hour_later = now + timedelta(hours=1)
    waiter_n = TableAssign.objects.filter(tabereservation=OuterRef('pk')).values('waiter__name')[:1]
    waiter_p = TableAssign.objects.filter(tabereservation=OuterRef('pk')).values('waiter__phone_no')[:1]
    reservation = TableReservation.objects.filter(
        time_schedule=one_hour_later.date(),
        start_time__hour=one_hour_later.time().hour,
        start_time__minute=one_hour_later.time().minute
    ).annotate(
        waiter_name=Subquery(waiter_n),
        waiter_phone=Subquery(waiter_p)
    )


    for r in reservation:
        user = r.user
        waiter = r.waiter_name or 'unassigned'
        waiter_phone = r.waiter_phone or 'unassigned'
        mail_subject = "Gentle Reminder"
        html_content = render_to_string('table_reservation_remainder_mail.html',{'user':user,'waiter':waiter,'waiter_phone':waiter_phone,'reservation':r})
        message = EmailMultiAlternatives(
            mail_subject,
            html_content,
            settings.EMAIL_HOST_USER,
            [user.email]
        )
        message.attach_alternative(html_content,"text/html")
        message.send()
    return "Reminder sent successfully"


@shared_task
def change_table_status():
    today = timezone.now().date()
    now_time = timezone.now().time()
    one_hour_later = timezone.now() + timedelta(minutes=90)
    one_hour_later_time = one_hour_later.time()
    reservations = TableReservation.objects.filter(
        time_schedule=today,
        start_time__gte=now_time,
        start_time__lte=one_hour_later_time
    ).select_related('table')

    for r in reservations:
        table = r.table
        if table.available:
            table.available = False
            table.save()

    return "Table status updated successfully"
