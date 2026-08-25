# -*- coding: utf-8 -*-
with open('frontend/src/layouts/AdminLayout.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '<aside className="w-64 bg-card border-r border-violett-100 flex flex-col">',
    '<aside className="w-64 bg-card border-r border-violett-100 flex flex-col sticky top-0 h-screen overflow-y-auto custom-scrollbar">'
)

with open('frontend/src/layouts/AdminLayout.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Aside updated")
