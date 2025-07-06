# webhooks/urls.py
from django.urls import path
from . import views

app_name = 'bots'

urlpatterns = [
    # Public webhook endpoint - no auth required
    path('<uuid:webhook_id>/<str:webhook_key>/', views.webhook_handler, name='webhook_handler'),
    
    # webhooks urls
    path('webhooks/', views.webhook_list, name='webhook_list'),
    path('create_webhook/', views.create_webhook, name='create_webhook'),
    path('<int:pk>/delete_webhook/', views.delete_webhook, name='delete_webhook'),
    path('<int:pk>/webhook_logs/', views.webhook_logs, name='webhook_logs'),
    
    # exchanges urls
    path('exchanges/', views.exchange_list, name='exchange_list'),
    path('create_exchange/', views.create_exchange, name='create_exchange'),
    path('<int:pk>/exchange_logs/', views.exchange_logs, name='exchange_logs'),
    path('<int:pk>/update_exchange/', views.update_exchange, name='update_exchange'),
    path('<int:pk>/delete_exchange/', views.delete_exchange, name='delete_exchange'),
    
    # bots urls
    path('bots/', views.bot_list, name='bot_list'),
    path('create_bot/', views.create_bot, name='create_bot'),
    path('<int:pk>/delete_bot/', views.delete_bot, name='delete_bot'),
    path('<int:pk>/bot_logs/', views.bot_logs, name='bot_logs'),
    path('<int:pk>/update_bot/', views.update_bot, name='update_bot'),
]

# In your main urls.py, add:
# path('bots/', include('bots.urls'))