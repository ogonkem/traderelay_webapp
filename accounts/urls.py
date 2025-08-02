from django.urls import path
from allauth.account.views import LoginView
from .models import UserProfile
from . import views

app_name = 'accounts'

class CustomLoginView(LoginView):
    template_name = 'accounts/signup.html'  # Use your custom template

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if user.is_authenticated:
            UserProfile.objects.get_or_create(user=user)
        return response

urlpatterns = [
    path('signup/', CustomLoginView.as_view(), name='signup'),
    path('profile/', views.profile_view, name='profile'),
] 