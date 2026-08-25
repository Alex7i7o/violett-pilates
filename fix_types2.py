# -*- coding: utf-8 -*-
import sys

# 2. AlumnosAdmin
with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("(a: import('../../lib/adminApi').UsuarioAdmin)", "(a: UsuarioAdmin)")
if "import type { UsuarioAdmin }" not in c:
    c = c.replace("import { api } from '../../lib/api';", "import { api } from '../../lib/api';\nimport type { UsuarioAdmin } from '../../lib/adminApi';")

with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

# 3. ProfesoresAdmin
with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("(p: import('../../lib/adminApi').Profesor)", "(p: Profesor)")
if "import type { Profesor }" not in c:
    c = c.replace("import { adminApi } from '../../lib/adminApi';", "import { adminApi } from '../../lib/adminApi';\nimport type { Profesor } from '../../lib/adminApi';")

with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done Types 2")
