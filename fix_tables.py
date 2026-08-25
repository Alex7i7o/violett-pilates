import os

files = [
    'frontend/src/pages/admin/AlumnosAdmin.tsx',
    'frontend/src/pages/admin/ProfesoresAdmin.tsx',
    'frontend/src/pages/admin/PlanesAdmin.tsx',
    'frontend/src/pages/admin/PlantillasAdmin.tsx'
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple replace: <table className="w-full ..."> wrapper
    # Often it is <div className="border rounded-xl ..."> or similar. Let's look for <table and wrap it if not wrapped.
    # Actually, Shadcn tables might already be wrapped in something, or we can just replace <table with <div className="overflow-x-auto w-full"><table and </table> with </table></div>
    
    # Shadcn tables are usually: 
    # <div className="overflow-hidden rounded-xl border border-violett-100 bg-white shadow-sm">
    # Let's change overflow-hidden to overflow-x-auto
    
    content = content.replace('overflow-hidden rounded-xl', 'overflow-x-auto rounded-xl')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Tables fixed")
