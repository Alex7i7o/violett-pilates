import re

with open('core/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Import the view
if 'CrearResenaView' not in content:
    content = re.sub(
        r'(from \.views import.*?)(?=\n)',
        r'\1, CrearResenaView',
        content,
        count=1
    )
    
    # Add the URL pattern
    content = re.sub(
        r'(urlpatterns = \[)(.*?)(\n\])',
        r"\1\2\n    path('resenas/', CrearResenaView.as_view(), name='crear-resena'),\3",
        content,
        flags=re.DOTALL
    )

    with open('core/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("URL added")
else:
    print("URL already exists")
