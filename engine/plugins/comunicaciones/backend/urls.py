from django.urls import path
from .views import WhatsAppWebhookView

urlpatterns = [
    path('webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('webhook', WhatsAppWebhookView.as_view()),
    path('whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook_alias'),
    path('whatsapp/webhook', WhatsAppWebhookView.as_view()),
    path('comunicaciones/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_comunicaciones_webhook'),
    path('comunicaciones/webhook', WhatsAppWebhookView.as_view()),
    path('comunicaciones/whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_full_webhook'),
    path('comunicaciones/whatsapp/webhook', WhatsAppWebhookView.as_view()),
]
