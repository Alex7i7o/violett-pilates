import re

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports
imports = """import { ProfesorTabHoy } from '../../components/profesor/ProfesorTabHoy';
import { ProfesorTabMes } from '../../components/profesor/ProfesorTabMes';
import { ProfesorTabProximos } from '../../components/profesor/ProfesorTabProximos';
import { ProfesorTabRecurrentes } from '../../components/profesor/ProfesorTabRecurrentes';
import { ProfesorBolsaTrabajo } from '../../components/profesor/ProfesorBolsaTrabajo';
import { type ProfesorDashboardData } from '../../types/profesor';
"""
content = content.replace("import { ConfirmModal } from '../../components/ui/ConfirmModal';", "import { ConfirmModal } from '../../components/ui/ConfirmModal';\n" + imports)

# Replace <any> with <ProfesorDashboardData | null>
content = content.replace("useState<any>(null)", "useState<ProfesorDashboardData | null>(null)")

# Remove unused const days
content = re.sub(r"const days = \['Lunes',\s*'Martes',\s*'Mi.rcoles',\s*'Jueves',\s*'Viernes',\s*'S.bados',\s*'Domingos'\];\n", "", content)

# Now, we need to replace the huge block inside `<div className="lg:col-span-2 space-y-6">`
# Let's find the AnimatePresence block inside it.

start_tag = "<AnimatePresence mode=\"wait\">"
end_tag = "</AnimatePresence>"

start_idx = content.find(start_tag)
if start_idx != -1:
    # Find matching closing tag for AnimatePresence
    idx = start_idx
    depth = 0
    end_idx = -1
    while idx < len(content):
        if content[idx:idx+len("<AnimatePresence")] == "<AnimatePresence":
            depth += 1
        elif content[idx:idx+len("</AnimatePresence>")] == "</AnimatePresence>":
            depth -= 1
            if depth == 0:
                end_idx = idx + len("</AnimatePresence>")
                break
        idx += 1
    
    if end_idx != -1:
        replacement = """<AnimatePresence mode="wait">
            {activeTab === 'hoy' && <ProfesorTabHoy data={data} formatFecha={formatFecha} />}
            {activeTab === 'mes' && (
              <ProfesorTabMes 
                data={data} 
                selectedMonth={selectedMonth} 
                setSelectedMonth={setSelectedMonth} 
                selectedYear={selectedYear} 
                setSelectedYear={setSelectedYear} 
                formatFecha={formatFecha} 
              />
            )}
            {activeTab === 'proximos' && (
              <ProfesorTabProximos 
                data={data} 
                formatFecha={formatFecha} 
                showPast={showPast} 
                setShowPast={setShowPast} 
              />
            )}
            {activeTab === 'recurrentes' && <ProfesorTabRecurrentes data={data} />}
          </AnimatePresence>"""
        
        content = content[:start_idx] + replacement + content[end_idx:]

# Now replace BolsaTrabajo
bolsa_start = "{/* Right Column: Bolsa de Trabajo */}"
b_start_idx = content.find(bolsa_start)
if b_start_idx != -1:
    b_end_idx = content.find("</div>\n      </div>\n\n      {/* Modals */}")
    
    if b_end_idx != -1:
        replacement_bolsa = """{/* Right Column: Bolsa de Trabajo */}
        <div>
          <ProfesorBolsaTrabajo 
            data={data} 
            setTurnoToAssign={setTurnoToAssign} 
            setPlantillaToAssign={setPlantillaToAssign} 
            formatFecha={formatFecha} 
          />
        </div>
      </div>

      {/* Modals */}"""
        
        content = content[:b_start_idx] + replacement_bolsa + content[b_end_idx + len("</div>\n      </div>\n\n      {/* Modals */}")]

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("ProfesorDashboard.tsx refactored")
