from django.contrib import admin
from .models import UserProfile, UserInvitation

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'max_webhooks', 'max_daily_trades', 'last_active')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('last_active', 'last_trade_at')

@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'invited_by', 'status', 'role', 'created_at', 'expires_at')
    list_filter = ('status', 'role')
    search_fields = ('email', 'invited_by__email')
    readonly_fields = ('invitation_id', 'created_at')

# Register your models here.
