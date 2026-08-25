import sys

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

import re
# Remove all injected modals
c = re.sub(r'      \{\/\* Confirm Plantilla Modal \*\/\}[\s\S]*?<\/Modal>\s*\}\)', '', c)

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

c = c.replace('    </motion.div>\n  );\n}', modal_injection + '    </motion.div>\n  );\n}')

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done")
