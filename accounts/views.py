from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import UserProfile, UserInvitation
from django.contrib.auth.models import User


@login_required
def profile_view(request):
    """View for user profile"""
    profile = get_object_or_404(UserProfile, user=request.user)
    # Dummy bots data
    bots = [
        {"name": "BTCUSDT Spot Bot", "status": "active", "broker": "Bybit", "total_trades": 12, "pnl": "+$120.00", "win_rate": 75},
        {"name": "ETHUSDT Futures Bot", "status": "paused", "broker": "Binance", "total_trades": 8, "pnl": "-$30.00", "win_rate": 50},
    ]
    create_bot_url = "/bots/create/"  # adjust as needed

    # Calculate usage percentages for progress bars
    max_webhooks = getattr(profile, 'max_webhooks', 0) or 0
    webhooks_used = getattr(profile, 'webhooks_used', 0) or 0
    if max_webhooks:
        webhooks_used_percent = int((webhooks_used / max_webhooks) * 100)
    else:
        webhooks_used_percent = 0

    max_daily_trades = getattr(profile, 'max_daily_trades', 0) or 0
    daily_trades_used = getattr(profile, 'daily_trades_used', 0) or 0
    if max_daily_trades:
        daily_trades_used_percent = int((daily_trades_used / max_daily_trades) * 100)
    else:
        daily_trades_used_percent = 0

    context = {
        'profile': profile,
        'user': request.user,
        'bots': bots,
        'create_bot_url': create_bot_url,
        'webhooks_used_percent': webhooks_used_percent,
        'daily_trades_used_percent': daily_trades_used_percent,
    }
    return render(request, 'accounts/profile.html', context)

