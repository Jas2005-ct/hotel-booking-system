from celery import shared_task
import time
from datetime import datetime
from table_reservation.models import TableReservation
from accounts.models import CustomUser
from project_files import settings
from django.core.mail import send_mail,EmailMultiAlternatives
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import timezone

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
def table_reservation_guest(user_id,time_schedules):
    now = timezone.now()
    user = CustomUser.objects.get(id=user_id)
    mail_subject = "Thank For Your reservation..!!"
    html_content = render_to_string('table_reservation_mail.html',{'user':user,'time_schedule':time_schedules})
    message = EmailMultiAlternatives(
        mail_subject,
        html_content,
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    message.attach_alternative(html_content,"text/html")
    message.send()

    return f'Remainder sent successfully'
