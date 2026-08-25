import re
with open('frontend/src/pages/admin/PlanesAdmin.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

imports = """import { PlanForm, type PlanFormData } from '../../components/admin/PlanForm';\n"""
content = content.replace("import { ConfirmModal } from '../../components/ui/ConfirmModal';", imports + "import { ConfirmModal } from '../../components/ui/ConfirmModal';")

handle_submit = """  const handleSubmit = async (data: PlanFormData) => {
    try {
      if (editId) {
        await api.put(`/admin/planes/${editId}/`, data);
        toast.success('Plan actualizado');
      } else {
        await api.post('/admin/planes/', data);
        toast.success('Plan creado');
      }
      handleCancel();
      fetchData();
    } catch (e) {
      console.error(e);
      toast.error('Error al guardar el plan');
    }
  }"""
content = re.sub(r'const handleSubmit = async \(e: React.FormEvent\) => \{[\s\S]*?\}\n  \}', handle_submit, content)

content = re.sub(r'const \[nombre, setNombre\] = useState\(\'\'\);\n', '', content)
content = re.sub(r'const \[clases, setClases\] = useState\(0\);\n', '', content)
content = re.sub(r'const \[precio, setPrecio\] = useState\(0\);\n', '', content)

content = re.sub(r'const handleEdit = \(p: any\) => \{[\s\S]*?\}\n', """  const handleEdit = (p: any) => {
    setEditId(p.id);
  }
""", content)

content = re.sub(r'const handleCancel = \(\) => \{[\s\S]*?\}\n', """  const handleCancel = () => {
    setEditId(null);
  }
""", content)

form_regex = r'<form onSubmit=\{handleSubmit\} className="grid grid-cols-1 md:grid-cols-4 gap-4">[\s\S]*?<\/form>'
replacement = """<PlanForm 
            initialData={editId ? { nombre: planes.find(p => p.id === editId)?.nombre || '', clases_por_mes: planes.find(p => p.id === editId)?.clases_por_mes || 0, precio: planes.find(p => p.id === editId)?.precio || 0 } : null} 
            onSubmit={handleSubmit} 
            onCancel={handleCancel} 
            isEditing={!!editId} 
          />"""
content = re.sub(form_regex, replacement, content)

with open('frontend/src/pages/admin/PlanesAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("PlanesAdmin.tsx refactored")
