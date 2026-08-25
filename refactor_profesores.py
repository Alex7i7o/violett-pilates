# -*- coding: utf-8 -*-
import sys
import re

with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("import { Badge } from '../../components/ui/Badge';", 
  "import { Badge } from '../../components/ui/Badge';\nimport { InputField } from '../../components/ui/InputField';\nimport { SelectField } from '../../components/ui/SelectField';")

# Profesores Admin Forms
c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1">Nombre</label>
              <input type="text" required value={nombre} onChange={e=>setNombre(e.target.value)} className="w-full p-2 border rounded-xl" />
            </div>''', '<InputField label="Nombre" required value={nombre} onChange={e=>setNombre(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1">Apellido</label>
              <input type="text" required value={apellido} onChange={e=>setApellido(e.target.value)} className="w-full p-2 border rounded-xl" />
            </div>''', '<InputField label="Apellido" required value={apellido} onChange={e=>setApellido(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1">Teléfono</label>
              <input type="tel" value={telefono} onChange={e=>setTelefono(e.target.value)} className="w-full p-2 border rounded-xl" />
            </div>''', '<InputField label="Teléfono" type="tel" value={telefono} onChange={e=>setTelefono(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1">Email</label>
              <input type="email" value={email} onChange={e=>setEmail(e.target.value)} className="w-full p-2 border rounded-xl" />
            </div>''', '<InputField label="Email" type="email" value={email} onChange={e=>setEmail(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1">Fecha Nacimiento</label>
              <input type="date" value={fechaNacimiento} onChange={e=>setFechaNacimiento(e.target.value)} className="w-full p-2 border rounded-xl" />
            </div>''', '<InputField label="Fecha Nacimiento" type="date" value={fechaNacimiento} onChange={e=>setFechaNacimiento(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1">Sexo</label>
              <select value={sexo} onChange={e=>setSexo(e.target.value)} className="w-full p-2 border rounded-xl bg-white">
                <option value="">Seleccionar</option>
                <option value="F">Femenino</option>
                <option value="M">Masculino</option>
                <option value="O">Otro</option>
                <option value="N">Prefiero no decirlo</option>
              </select>
            </div>''', '''<SelectField label="Sexo" value={sexo} onChange={e=>setSexo(e.target.value)} options={[{value:'F',label:'Femenino'},{value:'M',label:'Masculino'},{value:'O',label:'Otro'},{value:'N',label:'Prefiero no decirlo'}]} />''')

c = c.replace('''<div>
            <label className="block text-sm font-semibold mb-1">Especialidad</label>
            <input type="text" value={especialidad} onChange={e=>setEspecialidad(e.target.value)} className="w-full p-2 border rounded-xl" />
          </div>''', '<InputField label="Especialidad" value={especialidad} onChange={e=>setEspecialidad(e.target.value)} />')

c = c.replace('''<div>
            <label className="block text-sm font-semibold mb-1">Color Identificador</label>
            <input type="color" value={color} onChange={e=>setColor(e.target.value)} className="w-full p-1 border rounded-xl h-10" />
          </div>''', '<InputField label="Color Identificador" type="color" value={color} onChange={e=>setColor(e.target.value)} className="h-10 p-1" />')

with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done Refactoring ProfesoresAdmin")
