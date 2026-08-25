# -*- coding: utf-8 -*-
import re

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

if "const [activeTab, setActiveTab] = useState('hoy');" not in content:
    content = content.replace(
        "const [showPast, setShowPast] = useState(false);",
        "const [showPast, setShowPast] = useState(false);\n  const [activeTab, setActiveTab] = useState('hoy');"
    )

hoy_match = re.search(r'(<section>\s*<div className="flex justify-between items-center mb-4">\s*<h3 className="text-xl font-bold text-foreground">Clases de Hoy</h3>.*?</section>)', content, re.DOTALL)
hoy_section = hoy_match.group(1) if hoy_match else ""

mes_match = re.search(r'(<section className="mt-8">\s*<h3 className="text-xl font-bold text-foreground mb-4">Clases Dictadas en el Mes</h3>.*?</section>)', content, re.DOTALL)
mes_section = mes_match.group(1) if mes_match else ""

proximos_match = re.search(r'(<section>\s*<h3 className="text-xl font-bold text-foreground mb-4">Pr.*?ximos D.*?as</h3>.*?</section>)', content, re.DOTALL)
proximos_section = proximos_match.group(1) if proximos_match else ""

recurrentes_match = re.search(r'(<section>\s*<h3 className="text-xl font-bold text-foreground mb-4">Mis Clases Recurrentes</h3>.*?</section>)', content, re.DOTALL)
recurrentes_section = recurrentes_match.group(1) if recurrentes_match else ""

# Remove old sections
content = content.replace(hoy_section, "").replace(mes_section, "").replace(proximos_section, "").replace(recurrentes_section, "")

header_regex = r'\{/\* Header & Stats \*/\}.*?<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">'
old_header_match = re.search(header_regex, content, re.DOTALL)

if old_header_match:
    new_header = '''{/* Header & Stats */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-violett-900 mb-6">Hola, Profesor</h2>
          
          {/* Apple-style Segmented Control for Tabs */}
          <div className="flex bg-violett-100/50 p-1 rounded-2xl w-fit relative z-10 overflow-x-auto max-w-full">
            {['hoy', 'mes', 'proximos', 'recurrentes'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={elative px-4 py-2.5 text-sm font-semibold rounded-xl transition-colors whitespace-nowrap }
              >
                {activeTab === tab && (
                  <motion.div
                    layoutId="profesorTab"
                    className="absolute inset-0 bg-white rounded-xl shadow-sm z-0"
                    transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                  />
                )}
                <span className="relative z-10">
                  {tab === 'hoy' && 'Clases de Hoy'}
                  {tab === 'mes' && 'Dictadas en el Mes'}
                  {tab === 'proximos' && 'Próximos Días'}
                  {tab === 'recurrentes' && 'Mis Clases Recurrentes'}
                </span>
              </button>
            ))}
          </div>
        </div>
        
        <Button variant="outline" size="sm" onClick={() => setShowPasswordModal(true)} className="ml-4 shrink-0">
          Contraseña
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">'''
    content = content.replace(old_header_match.group(0), new_header)

new_left_column = '''        {/* Left Column: Contenido por Tab */}
        <div className="lg:col-span-2 space-y-6">
          <AnimatePresence mode="wait">
            {activeTab === 'hoy' && (
              <motion.div key="hoy" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
                ''' + hoy_section + '''
              </motion.div>
            )}
            
            {activeTab === 'mes' && (
              <motion.div key="mes" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
                <div className="bg-white border border-violett-100 px-6 py-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
                  <div>
                    <h3 className="text-lg font-bold text-violett-900 mb-3">Filtro de Historial</h3>
                    <div className="flex items-center gap-3">
                      <select 
                        className="border border-violett-200 rounded-xl px-3 py-2 text-sm bg-white text-violett-900 focus:outline-none focus:ring-2 focus:ring-violett-500"
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(Number(e.target.value))}
                      >
                        {Array.from({ length: 12 }, (_, i) => (
                          <option key={i+1} value={i+1}>
                            {new Date(2000, i).toLocaleString('es-ES', { month: 'long' }).replace(/^\w/, c => c.toUpperCase())}
                          </option>
                        ))}
                      </select>
                      <select 
                        className="border border-violett-200 rounded-xl px-3 py-2 text-sm bg-white text-violett-900 focus:outline-none focus:ring-2 focus:ring-violett-500"
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(Number(e.target.value))}
                      >
                        {[new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1].map(y => (
                          <option key={y} value={y}>{y}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  <div className="bg-violett-50 px-5 py-3 rounded-xl flex items-center gap-4">
                    <div className="w-10 h-10 bg-violett-900 rounded-full flex items-center justify-center text-white text-lg font-bold shadow-soft">
                      {data.horas_mes}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-violett-900 uppercase tracking-wider">Clases Dictadas</p>
                      <p className="text-xs text-violett-600">En este mes</p>
                    </div>
                  </div>
                </div>
                ''' + mes_section.replace('<section className="mt-8">', '<section>') + '''
              </motion.div>
            )}

            {activeTab === 'proximos' && (
              <motion.div key="proximos" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
                ''' + proximos_section + '''
              </motion.div>
            )}

            {activeTab === 'recurrentes' && (
              <motion.div key="recurrentes" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
                ''' + recurrentes_section + '''
              </motion.div>
            )}
          </AnimatePresence>
        </div>'''

left_col_regex = r'<div className="lg:col-span-2 space-y-8">[\s\S]*?</div>\s*(?={/\* Right Column: Bolsa de Trabajo \*/})'
left_match = re.search(left_col_regex, content)
if left_match:
    content = content.replace(left_match.group(0), new_left_column + "\n\n")

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done refactoring')
