import re

with open('core/views_webhooks.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = "from django.utils import timezone\n" + content
content = content.replace("timezone.now() if 'timezone' in globals() else dateutil.parser.isoparse(\"2026-01-01T00:00:00Z\")", "timezone.now()")

with open('core/views_webhooks.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed webhook")
