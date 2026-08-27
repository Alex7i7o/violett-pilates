import re

with open('frontend/src/pages/Login.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("No tengo cuenta, registrarme", "Registrarme")

with open('frontend/src/pages/Login.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed Login.tsx comma")
