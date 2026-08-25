import os

with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    "import { Badge } from '../components/ui/Badge'",
    "import { Badge } from '../components/ui/Badge'\nimport { Button } from '../components/ui/Button'"
)

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Import added")
