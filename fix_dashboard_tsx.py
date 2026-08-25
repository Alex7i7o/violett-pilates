import re

with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# I will replace the BookingGrid closing tag with the correct ternary operation.
c = re.sub(
    r'onCancel=\{handleCancel\}\s*/>\s*</div>',
    '''onCancel={handleCancel}
        />
        ) : (
          <div className="space-y-4">
            {historialLoading ? (
               <div className="text-center text-muted py-8">Cargando historial...</div>
            ) : historial.length === 0 ? (
               <div className="text-center text-muted py-8">No has asistido a clases este mes aún.</div>
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
        )}
      </div>''',
    c
)

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Dashboard TSX fixed")
