from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    def check(user):
        if user.is_authenticated and user.groups.filter(name__in=allowed_roles).exists():
            return True
        return PermissionDenied
    return check
    