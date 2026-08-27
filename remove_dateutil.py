import re

with open('core/views_webhooks.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("import dateutil.parser", "from datetime import datetime")
content = content.replace("dateutil.parser.isoparse", "datetime.fromisoformat")

with open('core/views_webhooks.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed dateutil")
