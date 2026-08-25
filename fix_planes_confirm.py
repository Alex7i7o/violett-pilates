import re

with open('frontend/src/pages/admin/PlanesAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'^(import .*?;?\n)', r'\1import { ConfirmModal } from "../../components/ui/ConfirmModal";\n', c, count=1)

c = c.replace(
    'const [precio, setPrecio] = useState(0);',
    'const [precio, setPrecio] = useState(0);\n  const [planToDelete, setPlanToDelete] = useState<string | null>(null);'
)

c = re.sub(
    r'const handleDelete = async \(id: string\) => \{\n\s*if \(\!confirm[^\n]+\n',
    '''const handleDelete = async (id: string) => {
    try {
      await api.delete(/admin/planes//);
      fetchPlanes();
    } catch (e) {
      toast.error("Error al eliminar")
    }
  }

  const promptDelete = (id: string) => {
    setPlanToDelete(id);
  }
''', c
)

c = c.replace('onClick={() => handleDelete(plan.id)}', 'onClick={() => promptDelete(plan.id)}')

modal_jsx = '''      <ConfirmModal
        isOpen={!!planToDelete}
        onClose={() => setPlanToDelete(null)}
        onConfirm={() => {
          if (planToDelete) handleDelete(planToDelete);
        }}
        title="Eliminar Plan"
        message="\u00bfEst\u00e1s seguro de que quieres eliminar este plan?\n\nEsta acci\u00f3n no se puede deshacer."
        confirmText="Eliminar"
        isDestructive={true}
      />
    </div>
  );
}'''
c = re.sub(r'</div>\s*\);\s*\}', modal_jsx, c)

with open('frontend/src/pages/admin/PlanesAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)
print("PlanesAdmin fixed")
