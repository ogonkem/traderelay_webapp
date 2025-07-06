# models.py
from django.db import models
from django.contrib.auth.models import User
import uuid
import secrets
import string
from django.urls import reverse
from django.conf import settings

class WebhookEndpoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    webhook_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    webhook_key = models.CharField(max_length=64, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    
    # Simple tracking
    total_requests = models.IntegerField(default=0)
    last_request_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.webhook_key:
            self.webhook_key = self.generate_webhook_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_webhook_key():
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))
    
    @property
    def webhook_url(self):

        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        return f"{base_url}/webhooks/{self.webhook_id}/{self.webhook_key}/"
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"

class WebhookLog(models.Model):
    webhook = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE)
    payload = models.JSONField()
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.webhook.name} - {self.created_at}"

class Exchange(models.Model):
    EXCHANGE_CHOICES = [
        ("", "Select Exchange"),
        ("bybit", "Bybit"),
        ("binance", "Binance"),
        ("gateio", "Gateio"),
        # ("mexc", "MEXC"),
        # ("kucoin", "KuCoin"),
        # ("coinbase", "Coinbase"),
        # ("okx", "OKX"),
        # ("crypto_com", "Crypto.com"),
        # ("other", "Other"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    exchange_type = models.CharField(max_length=32, choices=EXCHANGE_CHOICES)
    credentials = models.JSONField(help_text="API credentials (key, secret, passphrase, etc)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_credential(self, key):
        return self.credentials.get(key)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class ExchangeLog(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    payload = models.JSONField()
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True) 
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.exchange.name} - {self.created_at}"

class Bot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    webhook = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    symbol = models.CharField(max_length=100, blank=True, null=True)
    position_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
class BotLog(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    payload = models.JSONField()
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


