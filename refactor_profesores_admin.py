import re

with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

imports = """import { ProfesorForm, type ProfesorFormData } from '../../components/admin/ProfesorForm';\n"""
content = content.replace("import { Modal } from '../../components/ui/Modal';", imports + "import { Modal } from '../../components/ui/Modal';")

handle_submit = """  const handleSubmit = async (data: ProfesorFormData) => {
    try {
      if (editId) {
        await api.put(`/admin/profesores/${editId}/`, data);
        toast.success('Profesor actualizado');
      } else {
        await api.post('/admin/profesores/', data);
        toast.success('Profesor creado');
      }
      setShowModal(false);
      fetchData();
    } catch (e) {
      console.error(e);
      toast.error('Error al guardar el profesor');
    }
  }"""

content = re.sub(
    r'const handleSubmit = async \(e: React.FormEvent\) => \{[\s\S]*?\}\n  \}',
    handle_submit,
    content
)

# Replace inline state
content = re.sub(r'const \[nombre, setNombre\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[email, setEmail\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[telefono, setTelefono\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[color, setColor\] = useState\(\'#6d28d9\'\);\n', '', content)

# Replace form
form_regex = r'<form onSubmit=\{handleSubmit\} className="space-y-4">[\s\S]*?<\/form>'
replacement = """{editId ? (
          <ProfesorForm 
            initialData={{ nombre: profesores.find(p => p.id === editId)?.nombre || '', email: profesores.find(p => p.id === editId)?.email || '', telefono: profesores.find(p => p.id === editId)?.telefono || '', color: profesores.find(p => p.id === editId)?.color || '#6d28d9' }} 
            onSubmit={handleSubmit} 
            onCancel={() => setShowModal(false)} 
            isSubmitting={false} 
            submitLabel="Actualizar Profesor" 
          />
        ) : (
          <ProfesorForm 
            onSubmit={handleSubmit} 
            onCancel={() => setShowModal(false)} 
            isSubmitting={false} 
            submitLabel="Crear Profesor" 
          />
        )}"""
content = re.sub(form_regex, replacement, content)

# But wait, editId logic was using states in handleEdit.
handle_edit_replacement = """  const handleEdit = (p: any) => {
    setEditId(p.id);
    setShowModal(true);
  }"""
content = re.sub(r'const handleEdit = \(p: any\) => \{[\s\S]*?\}\n', handle_edit_replacement + "\n", content)

with open('frontend/src/pages/admin/ProfesoresAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("ProfesoresAdmin.tsx refactored")
