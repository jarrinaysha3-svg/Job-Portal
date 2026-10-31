from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .models import ProfileModel


def employer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        is_employer = ProfileModel.objects.filter(user=request.user, role='employer').exists()
        if not is_employer:
            messages.warning(request, 'Only employers can access this page.')
            return redirect('home_view')
        return view_func(request, *args, **kwargs)
    return wrapper


def seeker_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        is_seeker = ProfileModel.objects.filter(user=request.user, role='seeker').exists()
        if not is_seeker:
            messages.warning(request, 'Only job seekers can access this page.')
            return redirect('home_view')
        return view_func(request, *args, **kwargs)
    return wrapper