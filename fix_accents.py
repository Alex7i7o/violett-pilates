# -*- coding: utf-8 -*-
import sys

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('Confirmas tomar este horario fijo semanal para todas las fechas futuras?', '¿Confirmas tomar este horario fijo semanal para todas las fechas futuras?')
c = c.replace('Si, tomar horario', 'Sí, tomar horario')

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done")
