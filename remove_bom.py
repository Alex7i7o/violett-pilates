with open("core/views_webhooks.py", "rb") as f:
    content = f.read()

if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]

with open("core/views_webhooks.py", "wb") as f:
    f.write(content)
print("Removed BOM")
