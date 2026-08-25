import os

def fix_file(path, token_to_find, new_str):
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    if token_to_find in c:
        start_idx = c.find(token_to_find)
        if start_idx != -1:
            end_idx = c.find('};', start_idx) + 2
            if end_idx != -1:
                chunk_to_replace = c[start_idx:end_idx]
                c = c.replace(chunk_to_replace, new_str)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(c)
                print("Fixed", path)

# PlanesAdmin
fix_file(
    'frontend/src/pages/admin/PlanesAdmin.tsx',
    'const handleDelete = async (id: string) => {',
    '''const handleDelete = async (id: string) => {
    try {
      await api.delete(`/admin/planes/${id}/`);
      fetchPlanes();
    } catch (e) {
      toast.error("Error al eliminar")
    }
  };'''
)

# PlantillasAdmin
fix_file(
    'frontend/src/pages/admin/PlantillasAdmin.tsx',
    'const handleDelete = async (id: string) => {',
    '''const handleDelete = async (id: string) => {
    try {
      await api.delete(`/admin/plantillas/${id}/`);
      fetchPlantillas();
    } catch (e) {
      toast.error("Error eliminando plantilla")
    }
  };'''
)

# ProfesoresAdmin
fix_file(
    'frontend/src/pages/admin/ProfesoresAdmin.tsx',
    'const handleDelete = async (id: string) => {',
    '''const handleDelete = async (id: string) => {
    try {
      await deleteAdminProfesor(id);
      fetchData();
    } catch (e) {
      toast.error("Error eliminando profesor")
    }
  };'''
)

# ProfesorDashboard
fix_file(
    'frontend/src/pages/profesor/ProfesorDashboard.tsx',
    'const handleAssign = async (turnoId: string) => {',
    '''const handleAssign = async (turnoId: string) => {
    try {
      await api.post(`/profesor/turnos/${turnoId}/assign/`);
      toast.success('¡Clase asignada exitosamente!')
      fetchDashboard();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Error asignando la clase')
    }
  };'''
)

