from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import uuid

class UserProfile(models.Model):
    """Extended user profile with trading-specific information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('inactive', 'Inactive'),
        ],
        default='pending'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    max_webhooks = models.IntegerField(default=10)
    max_daily_trades = models.IntegerField(default=1000)
    total_trades = models.IntegerField(default=0)
    successful_trades = models.IntegerField(default=0)
    last_trade_at = models.DateTimeField(null=True, blank=True)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.status}"

class UserInvitation(models.Model):
    """Model for managing team invitations"""
    invitation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('expired', 'Expired'),
        ],
        default='pending'
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('trader', 'Trader'),
        ],
        default='trader'
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Invitation for {self.email} - {self.status}"

# Create your models here.
