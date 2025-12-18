from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    def check(user):
        if user.is_authenticated and user.role in allowed_roles:
            return True
        raise PermissionDenied
    return check
    