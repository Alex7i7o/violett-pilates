import re

with open('core/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
content = content.replace("from .admin_views import (", "from .views_webhooks import MercadoPagoWebhookView\nfrom .admin_views import (")

# Add to urlpatterns
new_url = "    path('webhooks/mercadopago/', MercadoPagoWebhookView.as_view(), name='webhook_mp'),\n"
content = content.replace("urlpatterns = [", f"urlpatterns = [\n{new_url}")

with open('core/urls.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added webhook URL")
