from django.contrib import admin
from .models import WebhookEndpoint, WebhookLog, Exchange

# Register your models here.
admin.site.register(Exchange)
