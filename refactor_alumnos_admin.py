import re

with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
imports = """import { AlumnoForm, type AlumnoFormData } from '../../components/admin/AlumnoForm';\n"""
content = content.replace("import { Modal } from '../../components/ui/Modal';", imports + "import { Modal } from '../../components/ui/Modal';")

# Replace handleCreateAlumno
handle_create = """  const handleCreateAlumno = async (data: AlumnoFormData) => {
    setCreating(true);
    try {
      await api.post('/admin/alumnos/', data);
      toast.success('Alumna creada exitosamente');
      fetchData();
      setShowNewModal(false);
    } catch (e: any) {
      console.error(e);
      toast.error('Error al crear alumna. ' + (e.response?.data?.detail || ''));
    } finally {
      setCreating(false);
    }
  }"""
content = re.sub(
    r'const handleCreateAlumno = async \(e: React.FormEvent\) => \{[\s\S]*?\}\n  \}',
    handle_create,
    content
)

# Remove the inline state for new alumno
content = re.sub(r'const \[newNombre, setNewNombre\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[newEmail, setNewEmail\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[newTelefono, setNewTelefono\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[newPlan, setNewPlan\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[newClasesExtra, setNewClasesExtra\] = useState\(0\);\n', '', content)
content = re.sub(r'const \[newFechaVenc, setNewFechaVenc\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[newNotas, setNewNotas\] = useState\(\'\'\);\n', '', content)

# Replace the form inside the Modal
form_regex = r'<form onSubmit=\{handleCreateAlumno\} className="space-y-4">[\s\S]*?<\/form>'
replacement = """<AlumnoForm 
          planes={planes} 
          onSubmit={handleCreateAlumno} 
          onCancel={() => setShowNewModal(false)} 
          isSubmitting={creating} 
          submitLabel="Crear Alumna" 
        />"""

content = re.sub(form_regex, replacement, content)

with open('frontend/src/pages/admin/AlumnosAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("AlumnosAdmin.tsx refactored")
