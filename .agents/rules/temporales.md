---
description: Regla estricta sobre el uso de la carpeta temporales para archivos basura y scripts de prueba.
trigger: always_on
---

# Uso Estricto de la Carpeta 'temporales'

1. **Nunca crees archivos basura en la raíz**: Todos los scripts de prueba (	est.js, patch.py, etc.), archivos de log temporales o scripts de migración descartables **DEBEN** crearse exclusivamente dentro del directorio 	emporales/ en la raíz del proyecto.
2. **Mantenimiento**: La carpeta 	emporales/ es para archivos de un solo uso. Si notas que la carpeta empieza a llenarse de scripts o archivos que ya no tienen utilidad para el estado actual de la tarea, tienes permiso explícito para vaciarla o borrar dichos archivos.
3. **No ensuciar el proyecto**: El objetivo de esta regla es mantener la raíz del repositorio y las carpetas de código fuente siempre limpias y ordenadas.
