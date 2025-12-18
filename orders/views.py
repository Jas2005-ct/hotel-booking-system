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
# Create your views here.

class CartCreateView(LoginRequiredMixin,UserPassesTestMixin,View):
    def test_func(self):
        return self.request.user.role == 'guest'
    def get(self, request):
        cart_user,created = Cart_User.objects.get_or_create(user=request.user)  
        if created:
            cart_user.save()
        cart_items = Cart_Items.objects.filter(cart_user=cart_user).select_related('menu')
        total_amount = sum(item.total_price for item in cart_items)
        # for i in cart_items:
        #     print(i.menu.name)
        return render(request, 'cart_sidebar.html', {'cart_items': cart_items,'total_amount':total_amount}) 

    def post(self,request):
        try:
            user = request.user
            menu_id = request.POST.get('menu_id')
            menu = Menu.objects.get(id=menu_id)
            cart_user,created = Cart_User.objects.get_or_create(user=user)  
            if created:
                cart_user.save()
            if Cart_Items.objects.filter(cart_user=cart_user,menu=menu).exists():
                cart_items = Cart_Items.objects.get(cart_user=cart_user,menu=menu)
                cart_items.quantity += 1
                cart_items.save()
                return JsonResponse({'success': True, 'message': 'Item added to cart successfully'}) 
            cart_items = Cart_Items.objects.create(cart_user=cart_user,menu=menu,quantity=1)
            cart_items.save()
            return JsonResponse({'success': True, 'message': 'Item added to cart successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
@csrf_exempt
@login_required
@user_passes_test(lambda u: u.role == 'guest')
def update_cart(request):
    if request.method != 'POST':
        return JsonResponse({'success':False,'message':'Invalid request method'})
    user = request.user
    action = request.POST.get('action')
    menu_id = request.POST.get('menu_id')

    if not menu_id:
        return JsonResponse({'success':False,'message':'Menu id is required'})
    try:
        menu = Menu.objects.get(id=menu_id)
        cart_user = Cart_User.objects.get(user=user)
    except Exception as e:
        return JsonResponse({'success':False,'message':str(e)})

    cart_items = Cart_Items.objects.get(cart_user=cart_user,menu=menu)
    if action == 'increase':
        cart_items.quantity += 1
        cart_items.save()
    if action == 'decrease':
        cart_items.quantity -= 1
        cart_items.save()
    if cart_items.quantity == 0:
        cart_items.delete()
    return JsonResponse({'success': True, 'message': 'Cart updated successfully'})  


class OrderCreateView(LoginRequiredMixin,UserPassesTestMixin,View):
    def test_func(self):
        return self.request.user.role == 'guest'
    def post(self,request):
        try:
            form = OrderForm(request.POST)
            if not form.is_valid():
                return JsonResponse({'success': False, 'message': 'Invalid form data'})
            vechile_number = form.cleaned_data['vechile_number']
            pickup_time = form.cleaned_data['pickup_time']
            user = request.user
            cart_user = Cart_User.objects.get(user=user)
            cart_items = Cart_Items.objects.filter(cart_user=cart_user)
            if not cart_items:
                return JsonResponse({'success': False, 'message': 'Cart is empty'})
            total_amount = sum(item.total_price for item in cart_items)
            date = datetime.now()
            ordered = order.objects.create(cart_user=cart_user,total_amount=total_amount,vechile_number=vechile_number,pickup_time=pickup_time)
            try:
                for i in cart_items:
                    order_items.objects.create(cart_user=cart_user,order=ordered,menu=i.menu,quantity=i.quantity)
                cart_items.delete()
                order_confirmation_email.delay(user.id)
            except Exception as e:
                print('here')
                return JsonResponse({'success': False, 'message': str(e)})
            # print("order successfullyy placed")
            return JsonResponse({'success': True, 'message': 'Order created successfully'})
        except Cart_Items.DoesNotExist:
            print('cart here')
            return JsonResponse({'success': False, 'message': 'Cart items not found'})
        except Exception as e:
            print('no here',e)
            return JsonResponse({'success': False, 'message': str(e)})

    def get(self,request):
        form = OrderForm()
        return render(request,'orderform.html',{'form':form})

class OrderListView(LoginRequiredMixin,View): 
    def get(self,request):
        user = request.user
        # print(user.id)
        if user.role == 'guest':
            try:
                cart_user = Cart_User.objects.get(user=user)
            except Cart_User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Cart user not found'})
            try:
                orders = order.objects.filter(cart_user=cart_user).prefetch_related('order_items').order_by('-pickup_time')
                tot = 0
                for i in orders:
                    tot += i.total_amount
                # print(tot)
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        elif user.role == 'waiter':
            try:
                orders = order.objects.filter(status='ready').prefetch_related('order_items').order_by('-pickup_time')
                tot = 0
                for i in orders:
                    tot += i.total_amount
                # print(tot)
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        return render(request,'order_list.html',{'orders':orders})

class KitchenStaffView(LoginRequiredMixin,UserPassesTestMixin,View):
    def test_func(self):
        return self.request.user.role == 'kitchen_staff'
    def get(self,request):
        current_time = timezone.localtime().time()
        now = timezone.now()
        user = request.user
        orders = order.objects.filter(pickup_time__gte=current_time,created_at__date=now.date()).exclude(status='completed').prefetch_related(Prefetch('order_items',queryset=order_items.objects.select_related('menu'))).prefetch_related('order_kitchen_staff').order_by('-pickup_time')
        order_taken = order_kitchen_staff.objects.filter(kitchen_staff=user).select_related('order').order_by('-order__pickup_time')
        past_orders = order_kitchen_staff.objects.filter(created_at__lt=now,order__status='completed',kitchen_staff=user).select_related('order__cart_user__user').prefetch_related('order__order_items__menu')
        return render(request,'kitchen_staff.html',{'orders':orders,'order_taken':order_taken,'past_orders':past_orders})
    
    def post(self,request):
        user = request.user
        order_id = request.POST.get('order_id')
        try:     
            orders = order.objects.get(id=order_id)
        except order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'})
        try:
            order_kitchen_staff.objects.create(order=orders,kitchen_staff=user)
            orders.kitchen_staff = user
            orders.status = 'ready'
            orders.save()
            # print(f'order created to kitchen')
        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'message': 'Order not found'})
        return JsonResponse({'success': True, 'message': 'Order ready successfully'})

class ServiceStaffView(LoginRequiredMixin,UserPassesTestMixin,View):
    def test_func(self):
        return self.request.user.role == 'waiter'
    def post(self,request):
        id = request.POST.get('id')
        # print(id)
        orders = order.objects.get(id=id)
        orders.status = 'completed'
        orders.waiter = request.user
        orders.save()
        return JsonResponse({'success': True, 'message': 'Order completed successfully'})
