from django.urls import path
from .views import CheckoutView
from .views_webhooks import MercadoPagoWebhookView

urlpatterns = [
    path('pagos/checkout/', CheckoutView.as_view(), name='pagos-checkout'),
    path('pagos/webhook/mercadopago/', MercadoPagoWebhookView.as_view(), name='pagos-webhook-mp'),
]
