import sys

# 1. Update useBookings.ts
with open('frontend/src/hooks/useBookings.ts', 'r', encoding='utf-8') as f:
    c = f.read()
if 'allowsRecurring: boolean' not in c:
    c = c.replace('isRecurring: boolean', 'isRecurring: boolean\n  allowsRecurring: boolean')
    with open('frontend/src/hooks/useBookings.ts', 'w', encoding='utf-8') as f:
        f.write(c)


# 2. Update BookingGrid.tsx
with open('frontend/src/components/booking/BookingGrid.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

target_header = '''                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-xl">{turno.time}</CardTitle>
                          <p className="text-sm font-medium text-violett-600 mt-1">{turno.classType}</p>
                        </div>
                        {turno.isBookedByMe && <Badge variant="secondary">Mi Reserva</Badge>}
                        {!turno.isBookedByMe && turno.availableSpots === 0 && <Badge variant="destructive">Lleno</Badge>}
                      </div>'''

replacement_header = '''                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-xl">{turno.time}</CardTitle>
                          <p className="text-sm font-medium text-violett-600 mt-1">{turno.classType}</p>
                        </div>
                        <div className="flex flex-col gap-1 items-end">
                          {turno.allowsRecurring ? <Badge variant="primary" className="bg-violett-100 text-violett-800">Fija Semanal</Badge> : <Badge variant="outline" className="border-gray-300 text-gray-500">Puntual</Badge>}
                          {turno.isBookedByMe && <Badge variant="secondary">Mi Reserva</Badge>}
                          {!turno.isBookedByMe && turno.availableSpots === 0 && <Badge variant="destructive">Lleno</Badge>}
                        </div>
                      </div>'''

if target_header in c:
    c = c.replace(target_header, replacement_header)
    with open('frontend/src/components/booking/BookingGrid.tsx', 'w', encoding='utf-8') as f:
        f.write(c)


# 3. Update BookingModal.tsx
with open('frontend/src/components/booking/BookingModal.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

target_modal = '''        <p className="text-muted text-sm">
          ¿Cómo te gustaría reservar este turno? Puedes anotarte solo para este día, o fijar este horario todas las semanas.
        </p>

        <div className="flex flex-col gap-3">
          <Button onClick={() => onConfirm(turno.id, false)} className="w-full">
            Reserva Puntual (Solo esta clase)
          </Button>
          <Button onClick={() => onConfirm(turno.id, true)} variant="outline" className="w-full">
            Reserva Recurrente (Fijo semanal)
          </Button>
        </div>'''

replacement_modal = '''        <p className="text-muted text-sm">
          {turno.allowsRecurring 
            ? '¿Cómo te gustaría reservar este turno? Puedes anotarte solo para este día, o fijar este horario todas las semanas.' 
            : 'Esta clase es puntual. Solo puedes reservar para esta fecha específica.'}
        </p>

        <div className="flex flex-col gap-3">
          <Button onClick={() => onConfirm(turno.id, false)} className="w-full">
            Reserva Puntual (Solo esta clase)
          </Button>
          {turno.allowsRecurring && (
            <Button onClick={() => onConfirm(turno.id, true)} variant="outline" className="w-full">
              Reserva Recurrente (Fijo semanal)
            </Button>
          )}
        </div>'''

# Deal with weird encoding like Cmo just in case
import re
c = re.sub(r'<p className="text-muted text-sm">[\s\S]*?</div>', replacement_modal, c)

with open('frontend/src/components/booking/BookingModal.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done")
