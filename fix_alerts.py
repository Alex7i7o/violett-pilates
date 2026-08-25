import os
import re

files_to_fix = [
    'frontend/src/hooks/useBookings.ts',
    'frontend/src/pages/Dashboard.tsx',
    'frontend/src/pages/admin/AgendaAdmin.tsx',
    'frontend/src/pages/admin/AlumnosAdmin.tsx',
    'frontend/src/pages/admin/PlanesAdmin.tsx',
    'frontend/src/pages/admin/PlantillasAdmin.tsx',
    'frontend/src/pages/admin/ProfesoresAdmin.tsx',
    'frontend/src/pages/profesor/ProfesorDashboard.tsx'
]

for filepath in files_to_fix:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Only proceed if alert( is in file
    if 'alert(' not in content:
        continue
        
    # Add import if missing
    if "from 'sonner'" not in content and 'from "sonner"' not in content:
        # insert after the first import
        content = re.sub(r'^(import .*?;?\n)', r'\1import { toast } from "sonner";\n', content, count=1)
    
    # Heuristics for success vs error
    # If the text inside alert has 'Error', 'No se pudo', it's an error. Otherwise success.
    def repl(m):
        msg = m.group(1)
        lower_msg = msg.lower()
        if 'error' in lower_msg or 'no se pudo' in lower_msg:
            return f'toast.error({msg})'
        else:
            return f'toast.success({msg})'

    content = re.sub(r'alert\((.*?)\);?', repl, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done fixing alerts")
