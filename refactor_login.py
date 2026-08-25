# -*- coding: utf-8 -*-
import sys

with open('frontend/src/pages/Login.tsx', 'r', encoding='latin-1') as f:
    c = f.read()

c = c.replace("import { motion, AnimatePresence } from 'framer-motion';", 
  "import { motion, AnimatePresence } from 'framer-motion';\nimport { InputField } from '../components/ui/InputField';\nimport { SelectField } from '../components/ui/SelectField';")

# Register Forms
c = c.replace('''<div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold mb-1 text-foreground">Nombre</label>
                    <input type="text" required value={regNombre} onChange={e=>setRegNombre(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold mb-1 text-foreground">Apellido</label>
                    <input type="text" required value={regApellido} onChange={e=>setRegApellido(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
                  </div>
                </div>''', '''<div className="grid grid-cols-2 gap-4">
                  <InputField label="Nombre" required value={regNombre} onChange={e=>setRegNombre(e.target.value)} />
                  <InputField label="Apellido" required value={regApellido} onChange={e=>setRegApellido(e.target.value)} />
                </div>''')

c = c.replace('''<div>
                  <label className="block text-sm font-semibold mb-1 text-foreground">Email</label>
                  <input type="email" required value={regEmail} onChange={e=>setRegEmail(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
                </div>''', '<InputField label="Email" type="email" required value={regEmail} onChange={e=>setRegEmail(e.target.value)} />')

c = c.replace('''<div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold mb-1 text-foreground">Teléfono</label>
                    <input type="tel" required value={regTelefono} onChange={e=>setRegTelefono(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold mb-1 text-foreground">Fecha Nacimiento</label>
                    <input type="date" required value={regFechaNacimiento} onChange={e=>setRegFechaNacimiento(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white" />
                  </div>
                </div>''', '''<div className="grid grid-cols-2 gap-4">
                  <InputField label="Teléfono" type="tel" required value={regTelefono} onChange={e=>setRegTelefono(e.target.value)} />
                  <InputField label="Fecha Nacimiento" type="date" required value={regFechaNacimiento} onChange={e=>setRegFechaNacimiento(e.target.value)} />
                </div>''')

c = c.replace('''<div>
                  <label className="block text-sm font-semibold mb-1 text-foreground">Sexo</label>
                  <select required value={regSexo} onChange={e=>setRegSexo(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white">
                    <option value="">Seleccionar</option>
                    <option value="F">Femenino</option>
                    <option value="M">Masculino</option>
                    <option value="O">Otro</option>
                    <option value="N">Prefiero no decirlo</option>
                  </select>
                </div>''', '''<SelectField label="Sexo" required value={regSexo} onChange={e=>setRegSexo(e.target.value)} options={[{value:'F',label:'Femenino'},{value:'M',label:'Masculino'},{value:'O',label:'Otro'},{value:'N',label:'Prefiero no decirlo'}]} />''')

c = c.replace('''<div>
                  <label className="block text-sm font-semibold mb-1 text-foreground">Contrase\xf1a</label>
                  <input type="password" required value={regPassword} onChange={e=>setRegPassword(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
                </div>''', '<InputField label="Contraseña" type="password" required value={regPassword} onChange={e=>setRegPassword(e.target.value)} />')

c = c.replace('''<div>
                <label className="block text-sm font-semibold mb-1 text-foreground">Email</label>
                <input type="email" required value={email} onChange={e=>setEmail(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" placeholder="tu@email.com" />
              </div>''', '<InputField label="Email" type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="tu@email.com" />')

c = c.replace('''<div>
                <label className="block text-sm font-semibold mb-1 text-foreground">Contrase\xf1a</label>
                <input type="password" required value={password} onChange={e=>setPassword(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" placeholder="••••••••" />
              </div>''', '<InputField label="Contraseña" type="password" required value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" />')


with open('frontend/src/pages/Login.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Done Refactoring Login")
