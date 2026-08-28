import os
import re

# Fix AgendaAdmin.tsx
with open('frontend/src/pages/admin/AgendaAdmin.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('description=', 'message=')
with open('frontend/src/pages/admin/AgendaAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

# Fix AlumnosAdmin.tsx
with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('fetchData()', 'fetchAlumnos()')
with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

# Fix ForgotPassword.tsx and ResetPassword.tsx
for filepath in ['frontend/src/pages/ForgotPassword.tsx', 'frontend/src/pages/ResetPassword.tsx']:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # In FeedbackButton, we pass status. But status can be 'error'.
    # FeedbackButton prop only accepts idle, loading, success.
    # We can cast it or change the component state.
    # Actually, FeedbackButton just needs status={status === 'error' ? 'idle' : status}
    content = content.replace('status={status}', "status={status === 'error' ? 'idle' : status}")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Fix ProfesorTabHoy.tsx: 'reservas_list' does not exist on type 'ClaseProfesor'
with open('frontend/src/types/profesor.ts', 'r', encoding='utf-8') as f:
    content = f.read()
if "reservas_list?:" not in content:
    content = content.replace('reservas: number;', 'reservas: number;\n  reservas_list?: any[];')
    with open('frontend/src/types/profesor.ts', 'w', encoding='utf-8') as f:
        f.write(content)

print("Fixed TS errors")
