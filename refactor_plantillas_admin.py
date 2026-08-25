import re
with open('frontend/src/pages/admin/PlantillasAdmin.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

imports = """import { PlantillaForm, type PlantillaFormData } from '../../components/admin/PlantillaForm';\n"""
content = content.replace("import { ConfirmModal } from '../../components/ui/ConfirmModal';", imports + "import { ConfirmModal } from '../../components/ui/ConfirmModal';")

handle_submit = """  const handleCreate = async (data: PlantillaFormData) => {
    try {
      if (editId) {
        await api.put(`/admin/plantillas/${editId}/`, data);
        toast.success('Horario actualizado');
      } else {
        await api.post('/admin/plantillas/', data);
        toast.success('Horario creado exitosamente');
      }
      setIsModalOpen(false);
      fetchData();
    } catch (e) {
      console.error(e);
      toast.error('Error al guardar el horario');
    }
  }"""
content = re.sub(r'const handleCreate = async \(e: React.FormEvent\) => \{[\s\S]*?\}\n  \}', handle_submit, content)

# Remove inline states
content = re.sub(r'const \[formData, setFormData\] = useState\(\{[\s\S]*?\}\);\n', '', content)

# Replace handleEdit
content = re.sub(r'const handleEdit = \(p: any\) => \{[\s\S]*?\}\n', """  const handleEdit = (p: any) => {
    setEditId(p.id);
    setIsModalOpen(true);
  }
""", content)

content = re.sub(r'const handleOpenNew = \(\) => \{[\s\S]*?\}\n', """  const handleOpenNew = () => {
    setEditId(null);
    setIsModalOpen(true);
  }
""", content)

form_regex = r'<form onSubmit=\{handleCreate\} className="space-y-4">[\s\S]*?<\/form>'
replacement = """{editId ? (
          <PlantillaForm 
            initialData={{ 
              dia_semana: plantillas.find(p => p.id === editId)?.dia_semana.toString() || '1', 
              hora_inicio: plantillas.find(p => p.id === editId)?.hora_inicio || '09:00', 
              hora_fin: plantillas.find(p => p.id === editId)?.hora_fin || '10:00', 
              clase_nombre: plantillas.find(p => p.id === editId)?.clase_nombre || 'Mat Pilates', 
              profesor_id: plantillas.find(p => p.id === editId)?.profesor || '' 
            }}
            profesores={profesores}
            onSubmit={handleCreate} 
            onCancel={() => setIsModalOpen(false)} 
            isSubmitting={false} 
          />
        ) : (
          <PlantillaForm 
            profesores={profesores}
            onSubmit={handleCreate} 
            onCancel={() => setIsModalOpen(false)} 
            isSubmitting={false} 
          />
        )}"""
content = re.sub(form_regex, replacement, content)

with open('frontend/src/pages/admin/PlantillasAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("PlantillasAdmin.tsx refactored")
