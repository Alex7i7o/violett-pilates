# -*- coding: utf-8 -*-
def insert_modal(filepath, state_var, title, message):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modal_code = f'''      <ConfirmModal
        isOpen={{!!{state_var}}}
        onClose={{() => set{state_var[0].upper() + state_var[1:]}(null)}}
        onConfirm={{() => {{
          if ({state_var}) handleDelete({state_var});
        }}}}
        title="{title}"
        message="{message}"
        confirmText="Eliminar"
        isDestructive={{true}}
      />
'''
    if '<ConfirmModal' not in content:
        content = content.replace("    </motion.div>", f"{modal_code}    </motion.div>")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")

insert_modal(
    'frontend/src/pages/admin/PlanesAdmin.tsx', 
    'planToDelete', 
    'Eliminar Plan', 
    'Seguro que deseas eliminar este plan?'
)

insert_modal(
    'frontend/src/pages/admin/ProfesoresAdmin.tsx', 
    'profesorToDelete', 
    'Eliminar Profesor', 
    'Seguro que deseas eliminar este profesor? Se reasignarán sus clases.'
)
