import re

with open('frontend/src/pages/admin/PlantillasAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'^(import .*?;?\n)', r'\1import { ConfirmModal } from "../../components/ui/ConfirmModal";\n', c, count=1)

c = c.replace(
    'const [cupoMaximo, setCupoMaximo] = useState(8);',
    'const [cupoMaximo, setCupoMaximo] = useState(8);\n  const [plantillaToDelete, setPlantillaToDelete] = useState<string | null>(null);'
)

c = re.sub(
    r'const handleDelete = async \(id: string\) => \{\n\s*if \(\!confirm[^\n]+\n',
    '''const handleDelete = async (id: string) => {
    try {
      await api.delete(/admin/plantillas//);
      fetchPlantillas();
    } catch (e) {
      toast.error("Error eliminando plantilla")
    }
  }

  const promptDelete = (id: string) => {
    setPlantillaToDelete(id);
  }
''', c
)

c = c.replace('onClick={() => handleDelete(p.id)}', 'onClick={() => promptDelete(p.id)}')

modal_jsx = '''      <ConfirmModal
        isOpen={!!plantillaToDelete}
        onClose={() => setPlantillaToDelete(null)}
        onConfirm={() => {
          if (plantillaToDelete) handleDelete(plantillaToDelete);
        }}
        title="Eliminar Esquema Semanal"
        message="\u00bfSeguro que deseas eliminar este esquema?\n\nLos turnos ya generados seguir\u00e1n existiendo, pero no se generar\u00e1n nuevos aut\u00f3maticamente."
        confirmText="Eliminar"
        isDestructive={true}
      />
    </div>
  );
}'''
c = re.sub(r'</div>\s*\);\s*\}', modal_jsx, c)

with open('frontend/src/pages/admin/PlantillasAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)
print("PlantillasAdmin fixed")
