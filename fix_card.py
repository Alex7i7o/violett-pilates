with open('frontend/src/components/ui/Card.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "initial={{ opacity: 0, y: 10 }}\n      animate={{ opacity: 1, y: 0 }}\n      transition={{ duration: 0.3 }}",
    "/* Inherits variants from parent */"
)

with open('frontend/src/components/ui/Card.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Card updated')
