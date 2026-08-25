with open('core/views.py', 'r', encoding='utf-8') as f:
    c = f.read()

if 'import datetime' not in c:
    c = c.replace('from django.utils import timezone', 'from django.utils import timezone\nimport datetime')
    with open('core/views.py', 'w', encoding='utf-8') as f:
        f.write(c)

print("datetime fixed")
