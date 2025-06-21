from django.shortcuts import render, redirect
from django.contrib.auth import logout

def home(request):
    """View for the home page"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    return render(request, 'home.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('home')