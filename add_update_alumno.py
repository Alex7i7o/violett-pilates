import re

with open('frontend/src/lib/adminApi.ts', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = """
export const updateAdminAlumno = async (id: string, data: Partial<UsuarioAdmin>): Promise<UsuarioAdmin> => {
  const res = await api.put(`/admin/usuarios/${id}/`, data);
  return res.data;
};
"""

content = content + new_func

with open('frontend/src/lib/adminApi.ts', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added updateAdminAlumno")
