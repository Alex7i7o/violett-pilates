with open('frontend/src/lib/api.ts', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "console.error('Session expired. Please log in again.');",
    "console.error('Session expired. Please log in again.');\n        window.location.href = '/';"
)

with open('frontend/src/lib/api.ts', 'w', encoding='utf-8') as f:
    f.write(content)
print('api.ts fixed')
