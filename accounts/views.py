from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from accounts.models import CustomUser, Menu, TableLayout, RoleChoices
from accounts.forms import (CustomUserForm, MenuForm, TableLayoutForm, LoginForm)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse_lazy
from django.core.mail import send_mail
from table_reservation.tasks import send_welcome_email
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from common.decorators import role_required
from common.mixins import RoleRequiredMixin


class BaseUserRegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserForm
    success_url = '/accounts/'
    user_role = None
    user_group_name = None
    success_redirect_url = None

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = self.user_role
        user.set_password(form.cleaned_data.get('password'))
        user = form.save()
        if self.user_group_name:
            group, _ = Group.objects.get_or_create(name=self.user_group_name)
            user.groups.add(group)
        login(self.request, user)
        return redirect(self.success_redirect_url)


class AdminUserView(BaseUserRegisterView):
    template_name = 'adminuserform.html'
    user_role = RoleChoices.ADMIN
    user_group_name = 'admin'
    success_redirect_url = 'admin_report:admin_home'


class WaiterUserView(BaseUserRegisterView):
    template_name = 'waiteruserform.html'
    user_role = RoleChoices.WAITER
    user_group_name = 'waiter'
    success_redirect_url = 'accounts:management'


class KitchenUserView(BaseUserRegisterView):
    template_name = 'kitchenuserform.html'
    user_role = RoleChoices.KITCHEN_STAFF
    success_redirect_url = 'orders:kitchen-staff'


class GuestUserView(BaseUserRegisterView):
    template_name = 'guestuserform.html'
    user_role = RoleChoices.GUEST
    user_group_name = 'guest'
    success_redirect_url = 'table_reservation:guesthome'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = RoleChoices.GUEST
        user.set_password(form.cleaned_data.get('password'))
        user = form.save()
        send_welcome_email.delay(user.id)
        group, _ = Group.objects.get_or_create(name='guest')
        user.groups.add(group)
        login(self.request, user)
        return redirect('table_reservation:guesthome')

def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request,user)
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                if user.role==RoleChoices.ADMIN:
                    return redirect('admin_report:admin_home')
                if user.role==RoleChoices.WAITER:
                    return redirect('accounts:management')
                if user.role == RoleChoices.GUEST:
                    return redirect('table_reservation:guesthome')
                if user.role == RoleChoices.KITCHEN_STAFF:
                    return redirect('orders:kitchen-staff')
                return JsonResponse({'status': 'False','message':'Unauthorized access'})
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'next_url': next_url})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')   

@login_required
@user_passes_test(role_required([RoleChoices.ADMIN, RoleChoices.WAITER]))
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
            return JsonResponse({'status':'True','message':'Menu deleted successfully'})
        except Menu.DoesNotExist:
            return JsonResponse({'status':'False','message':'Menu not found'})
        except Exception:
            return JsonResponse({'status':'False','message':'Menu not deleted'})

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


class TableDelete(LoginRequiredMixin,RoleRequiredMixin,View):
    required_role = ['admin']
    def post(self,request,pk):
        try:
            obj = TableLayout.objects.get(pk=pk)
            obj.delete()
            return JsonResponse({'status':'True','message':'Table deleted successfully'})
        except TableLayout.DoesNotExist:
            return JsonResponse({'status':'False','message':'Table not found'})
        except Exception:
            return JsonResponse({'status':'False','message':'Table not deleted'})

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
        except TableLayout.DoesNotExist:
            return JsonResponse({'status':'failed','message':'Table not found'})
        except Exception:
            return JsonResponse({'status':'failed'})

    

