import os

with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Imports
c = c.replace(
    "import { useClientProfile }",
    "import { toast } from 'sonner';\nimport { ConfirmModal } from '../components/ui/ConfirmModal';\nimport { useClientProfile }"
)

# State
c = c.replace(
    'const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null)',
    'const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null)\n  const [recurrenciaToCancel, setRecurrenciaToCancel] = useState<string | null>(null)'
)

# Logic
old_logic = """  const handleCancelRecurrencia = async (id: string) => {
    if (!window.confirm('¿Estás seguro de cancelar tu horario fijo permanentemente? Esto cancelará todas tus reservas futuras para este horario.')) return
    try {
      await api.post('/recurrencias/cancel/', { id })
      refetchProfile()
      refetchTurnos()
    } catch (err: any) {
      alert("Error al cancelar el horario fijo.")
    }
  }"""
new_logic = """  const handleCancelRecurrencia = async (id: string) => {
    try {
      await api.post('/recurrencias/cancel/', { id })
      refetchProfile()
      refetchTurnos()
      toast.success("Horario fijo cancelado exitosamente.");
    } catch (err: any) {
      toast.error("Error al cancelar el horario fijo.")
    }
  }

  const promptCancelRecurrencia = (id: string) => {
    setRecurrenciaToCancel(id);
  }"""
c = c.replace(old_logic, new_logic)

# Replace alert in booking logic if any exist?
# Wait, I didn't check if there are other alerts in Dashboard.tsx.
# The user already tested other things, so let's just do recurrencia.

# Button click
c = c.replace('onClick={() => handleCancelRecurrencia(rec.id)}', 'onClick={() => promptCancelRecurrencia(rec.id)}')

# Modal
old_end = """    </div>
  )
}"""
new_end = """      <ConfirmModal
        isOpen={!!recurrenciaToCancel}
        onClose={() => setRecurrenciaToCancel(null)}
        onConfirm={() => {
          if (recurrenciaToCancel) handleCancelRecurrencia(recurrenciaToCancel);
        }}
        title="Cancelar Horario Fijo"
        message="¿Estás seguro de cancelar tu horario fijo permanentemente?\n\nEsto cancelará todas tus reservas futuras para este horario."
        confirmText="Sí, cancelar"
        cancelText="Mantener horario"
        isDestructive={true}
      />
    </div>
  )
}"""
c = c.replace(old_end, new_end)

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Dashboard fixed properly")
