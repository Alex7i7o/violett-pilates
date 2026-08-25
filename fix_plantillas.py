import re

with open('frontend/src/pages/admin/PlantillasAdmin.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add state variable
if 'const [plantillaToDelete' not in content:
    content = content.replace(
        "const [loading, setLoading] = useState(true);",
        "const [loading, setLoading] = useState(true);\n  const [plantillaToDelete, setPlantillaToDelete] = useState<string | null>(null);"
    )

# 2. Extract ConfirmModal
modal_regex = r"(\s+<ConfirmModal\s+isOpen=\{!!plantillaToDelete\}[\s\S]*?isDestructive=\{true\}\s+/>\n)"
match = re.search(modal_regex, content)
if match:
    modal_str = match.group(1)
    # Remove it from inside the map
    content = content.replace(modal_str, "")
    
    # Place it before the closing motion.div
    content = content.replace(
        "    </motion.div>",
        f"{modal_str}    </motion.div>"
    )

with open('frontend/src/pages/admin/PlantillasAdmin.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed PlantillasAdmin')
