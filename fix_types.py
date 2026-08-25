# -*- coding: utf-8 -*-
import sys
import re

# 1. ProfesorDashboard
with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

types_injection = """
export interface TurnoDisplay {
  id: string;
  hora_inicio: string;
  hora_fin: string;
  clase_nombre: string;
  cupo_actual: number;
}
export interface PlantillaDisplay {
  id: string;
  hora_inicio: string;
  clase_nombre: string;
  dia_semana: number;
}
"""
c = c.replace("import { Modal } from '../../components/ui/Modal';", "import { Modal } from '../../components/ui/Modal';\n" + types_injection)
c = c.replace("(t: any)", "(t: TurnoDisplay)")
c = c.replace("(a: any, b: any)", "(a: TurnoDisplay, b: TurnoDisplay)")
c = c.replace("(p: any)", "(p: PlantillaDisplay)")

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)


# 2. AlumnosAdmin
with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("(a: any)", "(a: import('../../lib/adminApi').UsuarioAdmin)")
with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

# 3. ProfesoresAdmin
with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("(p: any)", "(p: import('../../lib/adminApi').Profesor)")
with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done Types")
