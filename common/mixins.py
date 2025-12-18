from django.core.exceptions import PermissionDenied


class RoleRequiredMixin:
    required_role = []
    def dispatch(self, request, *args, **kwargs):
        print(self.required_role)
        if not request.user.role in self.required_role:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)