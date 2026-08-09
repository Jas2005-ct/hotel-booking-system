from celery import shared_task
import time
from datetime import datetime
from orders.models import Order, OrderItem, Cart_User
from accounts.models import CustomUser
from project_files import settings
from django.core.mail import send_mail,EmailMultiAlternatives
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import timezone

@shared_task
def order_confirmation_email(user_id):
    user = CustomUser.objects.get(id=user_id)
    cart_user = Cart_User.objects.get(user=user)
    orders = Order.objects.filter(cart_user=cart_user).prefetch_related('order_items').order_by('-pickup_time').first()
    mail_subject = "Thank For Your Order..!!"
    html_content = render_to_string('order_confirmation.html',{'user':user,'orders':orders})
    message = EmailMultiAlternatives(
        mail_subject,
        html_content,
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    message.attach_alternative(html_content,"text/html")
    message.send()

    return f'Remainder sent successfully'
