from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from accounts.models import CustomUser,Menu,TableLayout
from accounts.forms import (CustomUserForm,MenuForm,TableLayoutForm,LoginForm)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse,JsonResponse
from django.views import View
from django.views.generic import CreateView,UpdateView,DeleteView
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.core.mail import send_mail
from table_reservation.tasks import send_welcome_email
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin
from common.decorators import role_required


class AdminUserView(CreateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'adminuserform.html'
    success_url = '/accounts/'
    
    def form_valid(self,form):
        user = form.save(commit=False)
        user.role = "admin"
        user.set_password(form.cleaned_data.get('password'))
        user = form.save()
        group = Group.objects.get(name="admin")
        user.groups.add(group)
        login(self.request,user)
        return redirect('accounts:management')
        

class WaiterUserView(CreateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'waiteruserform.html'
    success_url = '/accounts/'
    
    def form_valid(self,form):
        user = form.save(commit=False)
        user.role = "waiter"
        user.set_password(form.cleaned_data.get('password'))
        user = form.save()
        group = Group.objects.get(name='waiter')
        user.groups.add(group)
        login(self.request,user)
        return redirect('accounts:management')

class KitchenUserView(CreateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'kitchenuserform.html'
    success_url = '/orders/kitchen-staff/'
    
    def form_valid(self,form):
        user = form.save(commit=False)
        user.role = "kitchen_staff"
        user.set_password(form.cleaned_data.get('password'))
        user = form.save()
        login(self.request,user)
        return redirect('orders:kitchen-staff')


class GuestUserView(CreateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'guestuserform.html'
    success_url = '/table_reservation/'

    def form_valid(self,form):
        user = form.save(commit=False)
        user.role = "guest"
        user.set_password(form.cleaned_data.get('password'))
        user = form.save()
        send_welcome_email.delay(user.id)
        group = Group.objects.get(name='guest')
        user.groups.add(group)
        return super().form_valid(form)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request,user)
                if user.role == 'admin' or user.role=='waiter':
                    return redirect('accounts:management')
                if user.role == 'guest':
                    return redirect('table_reservation:guesthome')
                if user.role == 'kitchen_staff':
                    return redirect('orders:kitchen-staff')
                return JsonResponse({'status': 'False','message':'Unauthorized access'})
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')   

@login_required
@user_passes_test(role_required(['admin','waiter']))
def ManagementView(request):
    menus = Menu.objects.all()
    tables = TableLayout.objects.all()
    context = {
        'menus':menus,
        'tables':tables
    }
    return render(request,'accounts_home.html',context)


class MenuCreate(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = Menu
    form_class = MenuForm
    template_name = 'menucreateform.html'
    success_url = reverse_lazy('accounts:management')
    permission_required = 'accounts.add_menu'

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return super().form_valid(form)

class MenuUpdate(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = Menu
    form_class = MenuForm
    template_name = 'menucreateform.html'
    success_url = reverse_lazy('accounts:management')
    permission_required = 'accounts.change_menu'

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return super().form_valid(form)

class MenuDelete(LoginRequiredMixin,PermissionRequiredMixin,View):
    permission_required = 'accounts.delete_menu'
    def post(self,request,pk):
        try:
            obj = Menu.objects.get(pk=pk)
            obj.delete()
            return JsonResponse({'status':'success'})
        except:
            return JsonResponse({'status':'failed'})

class TableCreate(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    model = TableLayout
    form_class = TableLayoutForm
    template_name = 'tablesetform.html'
    success_url = reverse_lazy('accounts:management')  
    permission_required = 'accounts.add_tablelayout'

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return super().form_valid(form)


class TableUpdate(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    model = TableLayout
    form_class = TableLayoutForm
    template_name = 'tablesetform.html'
    success_url = reverse_lazy('accounts:management')
    permission_required = 'accounts.change_tablelayout'

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return super().form_valid(form)


class TableDelete(View):
    def post(self,request,pk):
        try:
            obj = TableLayout.objects.get(pk=pk)
            obj.delete()
            return JsonResponse({'status':'success'})
        except:
            return JsonResponse({'status':'failed'})

class TableStatus(LoginRequiredMixin,PermissionRequiredMixin,View):
    permission_required = 'accounts.change_tablelayout'
    def post(self,request,pk):
        try:
            obj = TableLayout.objects.get(pk=pk)
            status = request.POST.get('status')
            if status=='available':
                obj.available = True
            else:
                obj.available = False
            obj.save()
            return JsonResponse({'status':'success'})
        except:
            return JsonResponse({'status':'failed'})

    

