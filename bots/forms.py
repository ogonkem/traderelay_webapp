import json
from django import forms
from .models import *

class ExchangeForm(forms.ModelForm):
    class Meta:
        model = Exchange
        fields = ['name', 'exchange_type', 'credentials']
        widgets = {
            'credentials': forms.Textarea(attrs={
                'class': 'form-control-traderelay',
                'rows': 6,
                'placeholder': '{"api_key": "your-key", "api_secret": "your-secret"} OR {"api_key": "your-key"}'
            }),
            'exchange_type': forms.Select(attrs={
                'class': 'form-control-traderelay',
                'placeholder': 'Select Exchange'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control-traderelay',
                'placeholder': 'e.g., Binance Main Account'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If this is an update (instance exists and has a pk), disable exchange_type
        if self.instance and self.instance.pk:
            self.fields['exchange_type'].disabled = True
            self.fields['exchange_type'].widget.attrs['readonly'] = True
            self.fields['exchange_type'].help_text = "Exchange type cannot be changed after creation."
        
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control-traderelay')

    def clean_credentials(self):
        credentials = self.cleaned_data.get('credentials')
        if isinstance(credentials, str):
            try:
                # Validate and return re-serialized JSON string
                parsed = json.loads(credentials)
                return json.dumps(parsed)
            except json.JSONDecodeError:
                raise forms.ValidationError("Please enter valid JSON for credentials.")
        return credentials

    def clean_exchange_type(self):
        exchange_type = self.cleaned_data.get('exchange_type')
        if exchange_type not in [choice[0] for choice in Exchange.EXCHANGE_CHOICES[1:]]:
            raise forms.ValidationError("Invalid exchange type.")
        return exchange_type
    
class BotForm(forms.ModelForm):
    class Meta:
        model = Bot
        fields = ['name', 'exchange', 'webhook', 'description', 'position_size']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control-traderelay',
                'placeholder': 'e.g., My Bot'
            }),
            'exchange': forms.Select(attrs={
                'class': 'form-control-traderelay',
                'placeholder': 'Select Exchange'
            }),
            'webhook': forms.Select(attrs={
                'class': 'form-control-traderelay',
                'placeholder': 'Select Webhook'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control-traderelay',
                'placeholder': 'Describe your bot strategy...',
                'rows': 2
            }),
            'position_size': forms.NumberInput(attrs={
                'class': 'form-control-traderelay',
                'placeholder': 'e.g., 100.00',
                'step': '0.01',
                'min': '0.01'
            }),
        }
        
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set user for filtering
        self.user = user
        
        # Filter exchanges and webhooks to only show user's own
        if user:
            self.fields['exchange'].queryset = Exchange.objects.filter(user=user)
            self.fields['webhook'].queryset = WebhookEndpoint.objects.filter(user=user)
            
        # If this is an update (instance exists and has a pk), disable exchange and webhook
        if self.instance and self.instance.pk:
            self.fields['exchange'].disabled = True
            self.fields['exchange'].widget.attrs['readonly'] = True
            self.fields['exchange'].help_text = "Exchange cannot be changed after creation."
            self.fields['webhook'].disabled = True
            self.fields['webhook'].widget.attrs['readonly'] = True
            self.fields['webhook'].help_text = "Webhook cannot be changed after creation."

        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control-traderelay')
    
    def clean(self):
        cleaned_data = super().clean()
        exchange = cleaned_data.get('exchange')
        webhook = cleaned_data.get('webhook')
    
        # Check if both exchange and webhook are provided
        if exchange and webhook:
            # Check if this combination already exists for this user
            existing_bot_query = Bot.objects.filter(
                user=self.user,
                exchange=exchange,
                webhook=webhook
            )
            
            # IMPORTANT: Exclude the current instance if we're updating
            if self.instance and self.instance.pk:
                existing_bot_query = existing_bot_query.exclude(pk=self.instance.pk)
            
            existing_bot = existing_bot_query.first()
        
            if existing_bot:
                raise forms.ValidationError(
                    f"A bot with this exchange and webhook combination already exists: {existing_bot.name}"
                )
    
        return cleaned_data
    
    def clean_exchange(self):
        exchange = self.cleaned_data.get('exchange')
        if exchange and self.user and exchange.user != self.user:
            raise forms.ValidationError("You can only use your own exchanges.")
        return exchange
    
    def clean_webhook(self):
        webhook = self.cleaned_data.get('webhook')
        if webhook and self.user and webhook.user != self.user:
            raise forms.ValidationError("You can only use your own webhooks.")
        return webhook
        
