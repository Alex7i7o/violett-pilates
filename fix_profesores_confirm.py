import re

with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'^(import .*?;?\n)', r'\1import { ConfirmModal } from "../../components/ui/ConfirmModal";\n', c, count=1)

c = c.replace(
    'const [telefono, setTelefono] = useState(\'\');',
    'const [telefono, setTelefono] = useState(\'\');\n  const [profesorToDelete, setProfesorToDelete] = useState<string | null>(null);'
)

c = re.sub(
    r'const handleDelete = async \(id: string\) => \{\n\s*if \(\!confirm[^\n]+\n',
    '''const handleDelete = async (id: string) => {
    try {
      await deleteAdminProfesor(id);
      fetchData();
    } catch (e) {
      toast.error("Error eliminando profesor")
    }
  }

  const promptDelete = (id: string) => {
    setProfesorToDelete(id);
  }
''', c
)

c = c.replace('onClick={() => handleDelete(p.id)}', 'onClick={() => promptDelete(p.id)}')

modal_jsx = '''      <ConfirmModal
        isOpen={!!profesorToDelete}
        onClose={() => setProfesorToDelete(null)}
        onConfirm={() => {
          if (profesorToDelete) handleDelete(profesorToDelete);
        }}
        title="Eliminar Profesor"
        message="\u00bfSeguro que deseas eliminar a este profesor?\n\nEsta acci\u00f3n no se puede deshacer."
        confirmText="Eliminar"
        isDestructive={true}
      />
    </div>
  );
}'''
c = re.sub(r'</div>\s*\);\s*\}', modal_jsx, c)

with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)
print("ProfesoresAdmin fixed")
