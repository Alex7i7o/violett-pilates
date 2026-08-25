import re

with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Import ConfirmModal
c = re.sub(r'^(import .*?;?\n)', r'\1import { ConfirmModal } from "../components/ui/ConfirmModal";\n', c, count=1)

# State
c = c.replace(
    'const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null)',
    'const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null)\n  const [recurrenciaToCancel, setRecurrenciaToCancel] = useState<string | null>(null)'
)

# Function
c = re.sub(
    r'const handleCancelRecurrencia = async \(id: string\) => \{\n\s*if \(\!window\.confirm[^\n]+\n',
    '''const handleCancelRecurrencia = async (id: string) => {
    try {
      await api.post('/recurrencias/cancel/', { id })
      refetchProfile()
      refetchTurnos()
    } catch (err: any) {
      toast.error("Error al cancelar el horario fijo.")
    }
  }

  const promptCancelRecurrencia = (id: string) => {
    setRecurrenciaToCancel(id)
  }
''', c
)

# Button click
c = c.replace('onClick={() => handleCancelRecurrencia(r.id)}', 'onClick={() => promptCancelRecurrencia(r.id)}')

# Modal rendering
modal_jsx = '''      <ConfirmModal
        isOpen={!!recurrenciaToCancel}
        onClose={() => setRecurrenciaToCancel(null)}
        onConfirm={() => {
          if (recurrenciaToCancel) handleCancelRecurrencia(recurrenciaToCancel);
        }}
        title="Cancelar Horario Fijo"
        message="\u00bfEst\u00e1s seguro de cancelar tu horario fijo permanentemente?\n\nEsto cancelar\u00e1 todas tus reservas futuras para este horario."
        confirmText="Sí, cancelar"
        cancelText="Mantener horario"
        isDestructive={true}
      />
    </div>
  )
}'''
c = re.sub(r'</div>\s*\)\s*\}', modal_jsx, c)

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Dashboard fixed")
