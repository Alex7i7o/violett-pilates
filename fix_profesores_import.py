with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

import re
if 'InputField' not in c:
    c = re.sub(r'^(import .*?;?\n)', r'\1import { InputField } from "../../components/ui/InputField";\nimport { SelectField } from "../../components/ui/SelectField";\n', c, count=1)
    with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'w', encoding='utf-8') as f:
        f.write(c)

print("Profesores fixed")
