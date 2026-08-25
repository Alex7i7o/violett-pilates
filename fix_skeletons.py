import re

# 1. BookingGrid
with open('frontend/src/components/booking/BookingGrid.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'^(import .*?;?\n)', r'\1import { Skeleton } from "../ui/Skeleton";\n', c, count=1)
c = c.replace('return <div className="p-8 text-center text-muted">Cargando agenda...</div>', 
'''return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    )''')
with open('frontend/src/components/booking/BookingGrid.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

# 2. ProfesorDashboard
with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'^(import .*?;?\n)', r'\1import { Skeleton } from "../../components/ui/Skeleton";\n', c, count=1)
c = c.replace('if (loading) return <p className="text-muted p-4">Cargando panel...</p>;',
'''if (loading) return (
    <div className="p-8 space-y-6">
      <Skeleton className="h-12 w-1/4 mb-8" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    </div>
  );''')
with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

# 3. AgendaAdmin
with open('frontend/src/pages/admin/AgendaAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'^(import .*?;?\n)', r'\1import { Skeleton } from "../../components/ui/Skeleton";\n', c, count=1)
c = c.replace('<p className="text-muted py-4">Cargando turnos...</p>',
'''<div className="space-y-4 mt-4">
            {[1,2,3,4].map(i => <Skeleton key={i} className="h-16 w-full" />)}
          </div>''')
with open('frontend/src/pages/admin/AgendaAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done with skeletons")
