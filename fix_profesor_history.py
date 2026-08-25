import os

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace fetch method
c = c.replace(
    '''  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.get('/profesor/dashboard/');''',
    '''  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/profesor/dashboard/?month=${selectedMonth}&year=${selectedYear}`);'''
)

# Replace useEffect to listen to selectedMonth and selectedYear
c = c.replace(
    '''  useEffect(() => {
    fetchDashboard();
  }, []);''',
    '''  useEffect(() => {
    fetchDashboard();
  }, [selectedMonth, selectedYear]);'''
)

# Add month selector UI next to "Cambiar Contraseña"
old_header = '''          <div className="flex items-center gap-3 mt-1">
            <p className="text-muted">Este es tu resumen de clases</p>
            <Button variant="outline" size="sm" onClick={() => setShowPasswordModal(true)}>
              Cambiar Contraseña
            </Button>
          </div>'''
new_header = '''          <div className="flex items-center gap-3 mt-1">
            <p className="text-muted">Resumen de clases para:</p>
            <select 
              className="border border-violett-200 rounded-md p-1 text-sm bg-white text-violett-900 focus:outline-none"
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
              className="border border-violett-200 rounded-md p-1 text-sm bg-white text-violett-900 focus:outline-none"
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
            >
              {[new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
            <Button variant="outline" size="sm" onClick={() => setShowPasswordModal(true)} className="ml-4">
              Contraseña
            </Button>
          </div>'''
c = c.replace(old_header, new_header)

# Show "turnos_mes_historial" in a new section or replace one of the sections if looking at past months?
# If we look at past month, "Clases de Hoy" and "Próximos Días" and "Mis Clases Recurrentes" might not make sense for the selected month, but they are returned anyway.
# Let's just add a section for "Historial del Mes Seleccionado" below "Clases de Hoy".
new_section = '''          <section className="mt-8">
            <h3 className="text-xl font-bold text-foreground mb-4">Clases Dictadas en el Mes</h3>
            {(!data.turnos_mes_historial || data.turnos_mes_historial.length === 0) ? (
              <Card>
                <CardContent className="py-8 text-center text-muted">
                  No hay clases dictadas en este mes.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {data.turnos_mes_historial.map((t: any) => (
                  <Card key={t.id} className="border-l-4 border-l-violett-600">
                    <CardContent className="flex justify-between items-center p-4">
                      <div>
                        <p className="font-bold text-foreground">{formatFecha(t.fecha)}</p>
                        <p className="text-muted text-sm">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)} hs</p>
                      </div>
                      <div className="text-right">
                        <p className="text-violett-900 font-medium">{t.clase_nombre}</p>
                        <Badge variant="outline" className="mt-1">{t.estado}</Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>

          <section>'''

c = c.replace('          <section>\n            <h3 className="text-xl font-bold text-foreground mb-4">Próximos Días</h3>', new_section + '\n            <h3 className="text-xl font-bold text-foreground mb-4">Próximos Días</h3>')

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Profesor history added")
