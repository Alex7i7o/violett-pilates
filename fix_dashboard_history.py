import os

with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Add state and fetch for history
c = c.replace(
    'const [recurrenciaToCancel, setRecurrenciaToCancel] = useState<string | null>(null)',
    '''const [recurrenciaToCancel, setRecurrenciaToCancel] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [historial, setHistorial] = useState<any[]>([]);
  const [historialLoading, setHistorialLoading] = useState(false);

  const fetchHistorial = async () => {
    if (historial.length > 0) return;
    try {
      setHistorialLoading(true);
      const res = await api.get('/reservas/historial/');
      setHistorial(res.data);
    } catch (e) {
      toast.error('Error cargando historial');
    } finally {
      setHistorialLoading(false);
    }
  };

  const toggleHistory = () => {
    if (!showHistory) fetchHistorial();
    setShowHistory(!showHistory);
  };
'''
)

# Replace the "Agenda Disponible" section to include the toggle button and the list
agenda_title_old = '<h2 className="text-2xl font-semibold text-violett-900">Agenda Disponible</h2>'
agenda_title_new = '''<div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-violett-900">
          {showHistory ? "Clases Asistidas (Este Mes)" : "Agenda Disponible"}
        </h2>
        <Button variant="outline" size="sm" onClick={toggleHistory}>
          {showHistory ? "Ver Agenda" : "Ver mi historial"}
        </Button>
      </div>'''

# We need to wrap the BookingGrid with conditional rendering
c = c.replace(
    '<BookingGrid',
    '{!showHistory ? (\n        <BookingGrid'
)
c = c.replace(
    'onCancel={handleCancel}\n      />',
    '''onCancel={handleCancel}\n      />\n      ) : (
        <div className="space-y-4">
          {historialLoading ? (
             <div className="text-center text-muted py-8">Cargando historial...</div>
          ) : historial.length === 0 ? (
             <div className="text-center text-muted py-8">No has asistido a clases este mes a\u00fan.</div>
          ) : (
             <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
               {historial.map((h: any) => (
                 <Card key={h.id} className="border-l-4 border-l-violett-500 opacity-80">
                   <CardContent className="p-4">
                     <p className="font-bold text-foreground text-lg">{h.fecha}</p>
                     <p className="text-sm text-muted mb-2">{h.hora_inicio} - {h.hora_fin}</p>
                     <div className="flex justify-between items-end">
                       <p className="text-violett-900 font-medium">{h.clase_nombre}</p>
                       <Badge variant="secondary" className="bg-gray-100 text-gray-700">{h.estado_reserva}</Badge>
                     </div>
                   </CardContent>
                 </Card>
               ))}
             </div>
          )}
        </div>
      )}'''
)

c = c.replace(agenda_title_old, agenda_title_new)

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Dashboard history added")
