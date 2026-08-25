import re

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(r'^(import .*?;?\n)', r'\1import { ConfirmModal } from "../../components/ui/ConfirmModal";\n', c, count=1)

c = c.replace(
    'const [assigningPlantilla, setAssigningPlantilla] = useState(false);',
    'const [assigningPlantilla, setAssigningPlantilla] = useState(false);\n  const [turnoToAssign, setTurnoToAssign] = useState<string | null>(null);'
)

c = re.sub(
    r'const handleAssign = async \(turnoId: string\) => \{\n\s*if \(\!confirm[^\n]+\n',
    '''const handleAssign = async (turnoId: string) => {
    try {
      await api.post(/profesor/turnos//assign/);
      toast.success('¡Clase asignada exitosamente!')
      fetchDashboard();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Error asignando la clase')
    }
  };

  const promptAssignTurno = (turnoId: string) => {
    setTurnoToAssign(turnoId);
  }
''', c
)

c = c.replace('onClick={() => handleAssign(t.id)}', 'onClick={() => promptAssignTurno(t.id)}')

# And replace the manual ConfirmPlantilla Modal with the new ConfirmModal
manual_modal_regex = r'<Modal onClose=\{\(\) => setShowConfirmPlantilla\(false\)\}>.*?<\/Modal>'
replacement_modal = '''<ConfirmModal
          isOpen={showConfirmPlantilla}
          onClose={() => setShowConfirmPlantilla(false)}
          onConfirm={confirmAssignPlantilla}
          title="Confirmar Horario Fijo"
          message="\u00bfConfirmas tomar este horario fijo semanal para todas las fechas futuras?"
          confirmText="S\u00ed, tomar horario"
          cancelText="Cancelar"
        />
        
        <ConfirmModal
          isOpen={!!turnoToAssign}
          onClose={() => setTurnoToAssign(null)}
          onConfirm={() => {
            if (turnoToAssign) handleAssign(turnoToAssign);
          }}
          title="Tomar Clase Puntual"
          message="\u00bfEst\u00e1s seguro de que quieres dar esta clase?"
          confirmText="S\u00ed, tomar clase"
        />'''

c = re.sub(manual_modal_regex, replacement_modal, c, flags=re.DOTALL)

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("ProfesorDashboard fixed")
