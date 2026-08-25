# -*- coding: utf-8 -*-
import sys

with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("import { Badge } from '../../components/ui/Badge';", 
  "import { Badge } from '../../components/ui/Badge';\nimport { InputField } from '../../components/ui/InputField';\nimport { SelectField } from '../../components/ui/SelectField';")

# 1. Search fields
c = c.replace('''<input 
            type="text"
            placeholder="Buscar por nombre, apellido o teléfono..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 p-3 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 shadow-sm"
          />''', '<InputField placeholder="Buscar por nombre, apellido o teléfono..." value={search} onChange={(e) => setSearch(e.target.value)} />')

c = c.replace('''<input 
              type="number"
              placeholder="Min"
              value={minAge}
              onChange={(e) => setMinAge(e.target.value)}
              className="w-20 p-3 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 shadow-sm"
            />''', '<InputField type="number" placeholder="Min" value={minAge} onChange={(e) => setMinAge(e.target.value)} />')

c = c.replace('''<input 
              type="number"
              placeholder="Max"
              value={maxAge}
              onChange={(e) => setMaxAge(e.target.value)}
              className="w-20 p-3 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 shadow-sm"
            />''', '<InputField type="number" placeholder="Max" value={maxAge} onChange={(e) => setMaxAge(e.target.value)} />')

# 2. Form fields
c = c.replace('''<div>
                <label className="block text-sm font-semibold mb-1 text-foreground">Nombre</label>
                <input type="text" required value={newNombre} onChange={e=>setNewNombre(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
              </div>''', '<InputField label="Nombre" required value={newNombre} onChange={e=>setNewNombre(e.target.value)} />')

c = c.replace('''<div>
                <label className="block text-sm font-semibold mb-1 text-foreground">Apellido</label>
                <input type="text" required value={newApellido} onChange={e=>setNewApellido(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
              </div>''', '<InputField label="Apellido" required value={newApellido} onChange={e=>setNewApellido(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Email</label>
              <input type="email" required value={newEmail} onChange={e=>setNewEmail(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>''', '<InputField label="Email" type="email" required value={newEmail} onChange={e=>setNewEmail(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Teléfono</label>
              <input type="tel" value={newTelefono} onChange={e=>setNewTelefono(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>''', '<InputField label="Teléfono" type="tel" value={newTelefono} onChange={e=>setNewTelefono(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Fecha Nacimiento</label>
              <input type="date" value={newFechaNacimiento} onChange={e=>setNewFechaNacimiento(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white" />
            </div>''', '<InputField label="Fecha Nacimiento" type="date" value={newFechaNacimiento} onChange={e=>setNewFechaNacimiento(e.target.value)} />')

c = c.replace('''<div>
            <label className="block text-sm font-semibold mb-1 text-foreground">Sexo</label>
            <select value={newSexo} onChange={e=>setNewSexo(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white">
              <option value="">Seleccionar</option>
              <option value="F">Femenino</option>
              <option value="M">Masculino</option>
              <option value="O">Otro</option>
              <option value="N">Prefiero no decirlo</option>
            </select>
          </div>''', '''<SelectField label="Sexo" value={newSexo} onChange={e=>setNewSexo(e.target.value)} options={[{value:'F',label:'Femenino'},{value:'M',label:'Masculino'},{value:'O',label:'Otro'},{value:'N',label:'Prefiero no decirlo'}]} />''')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Contacto Emergencia</label>
              <input type="text" value={newContacto} onChange={e=>setNewContacto(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>''', '<InputField label="Contacto Emergencia" value={newContacto} onChange={e=>setNewContacto(e.target.value)} />')

c = c.replace('''<div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Notas Médicas</label>
              <textarea value={newNotas} onChange={e=>setNewNotas(e.target.value)} rows={2} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>''', '<InputField label="Notas Médicas" multiline rows={2} value={newNotas} onChange={e=>setNewNotas(e.target.value)} />')

with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done Refactoring AlumnosAdmin")
