import sys

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add state variables for modal
state_marker = "const [bolsaTab, setBolsaTab] = useState<'SUELTOS' | 'FIJOS'>('SUELTOS');"
state_injection = """
  // Plantilla Modal state
  const [showConfirmPlantilla, setShowConfirmPlantilla] = useState(false);
  const [selectedPlantillaId, setSelectedPlantillaId] = useState<string | null>(null);
  const [assigningPlantilla, setAssigningPlantilla] = useState(false);
"""
c = c.replace(state_marker, state_marker + "\n" + state_injection)

# 2. Add handleAssignPlantilla function definition
func_marker = "const handleAssignClase = async (id: string) => {"
func_injection = """
  const handleAssignPlantilla = (id: string) => {
    setSelectedPlantillaId(id);
    setShowConfirmPlantilla(true);
  };

  const confirmAssignPlantilla = async () => {
    if (!selectedPlantillaId) return;
    setAssigningPlantilla(true);
    try {
      await api.post(/profesor/plantillas//assign/);
      alert('Horario fijo asignado con exito. Ahora aparecera en tu calendario.');
      setShowConfirmPlantilla(false);
      setSelectedPlantillaId(null);
      fetchDashboard();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error asignando plantilla');
    } finally {
      setAssigningPlantilla(false);
    }
  };

"""
c = c.replace(func_marker, func_injection + func_marker)

# 3. Add Modal at the end of return() before </motion.div>
modal_marker = "</motion.div>"
modal_injection = """
      {/* Confirm Plantilla Modal */}
      {showConfirmPlantilla && (
        <Modal onClose={() => setShowConfirmPlantilla(false)}>
          <div className="p-6">
            <h2 className="text-2xl font-bold text-violett-900 mb-4">Confirmar Horario Fijo</h2>
            <p className="text-foreground mb-6">Confirmas tomar este horario fijo semanal para todas las fechas futuras?</p>
            <div className="flex gap-4 mt-6">
              <Button variant="outline" className="w-full" onClick={() => setShowConfirmPlantilla(false)}>Cancelar</Button>
              <Button className="w-full" onClick={confirmAssignPlantilla} disabled={assigningPlantilla}>
                {assigningPlantilla ? 'Asignando...' : 'Si, tomar horario'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
"""
c = c.replace(modal_marker, modal_injection + modal_marker)

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done")
