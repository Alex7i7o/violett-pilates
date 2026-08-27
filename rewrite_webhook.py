with open('core/views_webhooks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Strip BOM characters if they exist in the string
content = content.replace('\ufeff', '')
content = content.replace('\xef\xbb\xbf', '')

with open('core/views_webhooks.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Rewrote webhook clean")
