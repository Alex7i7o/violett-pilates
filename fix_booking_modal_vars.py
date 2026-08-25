import re

with open('frontend/src/components/booking/BookingModal.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('turno.date', 'displayTurno.date')
content = content.replace('turno.time', 'displayTurno.time')
content = content.replace('turno.classType', 'displayTurno.classType')
content = content.replace('turno.allowsRecurring', 'displayTurno.allowsRecurring')
content = content.replace('turno.id', 'displayTurno.id')

with open('frontend/src/components/booking/BookingModal.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("BookingModal variables updated")
