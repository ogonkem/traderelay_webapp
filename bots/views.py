# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import logging
from .models import *
from django.contrib.auth.decorators import login_required
from .forms import *
from .trading import process_trading_signal

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_handler(request, webhook_id, webhook_key):
    """Handle incoming webhook from TradingView"""
    try:
        # Find the webhook endpoint
        webhook = get_object_or_404(
            WebhookEndpoint, 
            webhook_id=webhook_id, 
            webhook_key=webhook_key,
            is_active=True
        )
        
        # Parse JSON payload
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            WebhookLog.objects.create(
                webhook=webhook,
                payload={},
                success=False,
                error_message="Invalid JSON payload"
            )
            return HttpResponseBadRequest("Invalid JSON")
        
        # Update webhook stats
        webhook.total_requests += 1
        webhook.last_request_at = timezone.now()
        webhook.save()
        
        # Log the request
        log = WebhookLog.objects.create(
            webhook=webhook,
            payload=payload,
            success=True
        )
        
        # Process the trading signal here
        try:
            process_trading_signal(payload, webhook)
            print(f"[Alert Received] {webhook.name}: {payload}")
            return HttpResponse("OK", status=200)
            
        except Exception as e:
            log.success = False
            log.error_message = str(e)
            log.save()
            logger.error(f"Error processing signal: {e}")
            return HttpResponse(f"Error: {e}", status=500)
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return HttpResponseBadRequest(f"Error: {e}")

@login_required
def webhook_list(request):
    """List user's webhooks"""
    webhooks = WebhookEndpoint.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'webhooks/list.html', {'webhooks': webhooks})

@login_required
def create_webhook(request):
    """Create new webhook"""
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            webhook = WebhookEndpoint.objects.create(
                user=request.user,
                name=name
            )
            messages.success(request, f'Webhook "{name}" created successfully!')
            return redirect('bots:webhook_list')
        else:
            messages.error(request, 'Name is required')
    
    return render(request, 'webhooks/create.html')

@login_required
def delete_webhook(request, pk):
    """Delete webhook"""
    webhook = get_object_or_404(WebhookEndpoint, pk=pk, user=request.user)
    
    if request.method == 'POST':
        name = webhook.name
        webhook.delete()
        messages.success(request, f'Webhook "{name}" deleted successfully!')
        return redirect('bots:webhook_list')
    
    return render(request, 'webhooks/delete.html', {'webhook': webhook})

@login_required
def webhook_logs(request, pk):
    """View webhook logs"""
    webhook = get_object_or_404(WebhookEndpoint, pk=pk, user=request.user)
    logs = WebhookLog.objects.filter(webhook=webhook).order_by('-created_at')[:50]
    
    return render(request, 'webhooks/logs.html', {
        'webhook': webhook,
        'logs': logs
    })

@login_required
def exchange_list(request):
    exchanges = Exchange.objects.filter(user=request.user)
    return render(request, 'exchanges/list.html', {'exchanges': exchanges})

@login_required
def create_exchange(request):
    if request.method == 'POST':
        form = ExchangeForm(request.POST)
        if form.is_valid():
            exchange = form.save(commit=False)
            exchange.user = request.user
            exchange.save()
            return redirect('bots:exchange_list')
    else:
        form = ExchangeForm()
    return render(request, 'exchanges/create.html', {'form': form})

@login_required
def exchange_logs(request, pk):
    exchange = get_object_or_404(Exchange, pk=pk, user=request.user)
    logs = ExchangeLog.objects.filter(exchange=exchange).order_by('-created_at')[:50]
    
    return render(request, 'exchanges/logs.html', {
        'exchange': exchange, 
        'logs': logs
    })     


@login_required
def update_exchange(request, pk):
    exchange = get_object_or_404(Exchange, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExchangeForm(request.POST, instance=exchange)
        if form.is_valid():
            form.save()
            return redirect('bots:exchange_list')
    else:
        form = ExchangeForm(instance=exchange)
    return render(request, 'exchanges/create.html', {'form': form, 'exchange': exchange})

@login_required
def delete_exchange(request, pk):
    exchange = get_object_or_404(Exchange, pk=pk, user=request.user)
    if request.method == 'POST':
        exchange.delete()
        messages.success(request, f'Exchange "{exchange.name}" deleted successfully!')
        return redirect('bots:exchange_list')
    return render(request, 'exchanges/delete.html', {'exchange': exchange})

@login_required
def bot_list(request):
    bots = Bot.objects.filter(user=request.user)
    return render(request, 'bots/list.html', {'bots': bots})

@login_required
def create_bot(request):
    if request.method == 'POST':
        form = BotForm(request.POST, user=request.user)
        if form.is_valid():
            bot = form.save(commit=False)
            bot.user = request.user
            bot.save()
            messages.success(request, f'Bot "{bot.name}" created successfully!')
            return redirect('bots:bot_list')
    else:
        form = BotForm(user=request.user)
    return render(request, 'bots/create.html', {'form': form})  

@login_required
def delete_bot(request, pk):
    bot = get_object_or_404(Bot, pk=pk, user=request.user)
    if request.method == 'POST':
        bot.delete()
        messages.success(request, f'Bot "{bot.name}" deleted successfully!')
        return redirect('bots:bot_list')
    return render(request, 'bots/delete.html', {'bot': bot})

@login_required
def bot_logs(request, pk):
    bot = get_object_or_404(Bot, pk=pk, user=request.user)
    logs = BotLog.objects.filter(bot=bot).order_by('-created_at')[:50]
    return render(request, 'bots/logs.html', {'bot': bot, 'logs': logs})

@login_required
def update_bot(request, pk):
    bot = get_object_or_404(Bot, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BotForm(request.POST, instance=bot, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bot "{bot.name}" updated successfully!')
            return redirect('bots:bot_list')
    else:
        form = BotForm(instance=bot, user=request.user)
    return render(request, 'bots/create.html', {'form': form, 'bot': bot})

