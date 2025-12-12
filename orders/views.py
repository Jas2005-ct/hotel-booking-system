from django.shortcuts import render
from orders.models import *
from django.views.generic import ListView, DetailView
from django.views import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

class CartCreateView(View):
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