from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

# Decorator to allow only approved admins (head admin)



def super_or_approved_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            messages.error(request, "You must login first.")
            return redirect('Login')
        
        # Allow if superuser OR approved admin
        if user.is_superuser or (user.user_type == 'Admin' and user.is_approved):
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "You are not allowed to access this page.")
        return redirect('home')
    
    return wrapper

def approved_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('Login')
        if user.user_type != 'Admin':
            messages.error(request, "You are not allowed to access this page.")
            return redirect('home')
        if not user.is_approved:
            messages.error(request, "Your admin account is not approved yet.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

# Decorator for head admin / superuser only
def head_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('Login')
        if not user.is_superuser:
            messages.error(request, "You do not have head admin privileges.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('Login')
        if user.user_type != 'Student':
            messages.error(request, "You are not allowed to access this page.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
