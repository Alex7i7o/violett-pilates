import os

def remove_blur(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace initial blur
    content = content.replace("filter: 'blur(4px)'", "")
    content = content.replace("filter: 'blur(0px)', ", "")
    # Clean up any leftover commas if it was at the end or something
    content = content.replace("initial={{ opacity: 0, y: 10,  }}", "initial={{ opacity: 0, y: 10 }}")
    content = content.replace("animate={{ opacity: 1, y: 0, transition", "animate={{ opacity: 1, y: 0, transition")
    content = content.replace("exit={{ opacity: 0, , transition", "exit={{ opacity: 0, transition")
    content = content.replace("exit={{ opacity: 0,  transition", "exit={{ opacity: 0, transition")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

remove_blur('frontend/src/layouts/AdminLayout.tsx')
remove_blur('frontend/src/layouts/ProfesorLayout.tsx')
remove_blur('frontend/src/App.tsx')

print('Blur removed from page transitions')
