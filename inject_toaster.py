import sys

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

import re
if 'Toaster' not in c:
    c = re.sub(r'^(import .*?;?\n)', r'\1import { Toaster } from "sonner";\n', c, count=1)
    
    # inject into App component
    app_comp = '''function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" richColors />
      <AppRoutes />
    </BrowserRouter>
  )
}'''
    c = re.sub(r'function App\(\) \{\s*return \(\s*<BrowserRouter>\s*<AppRoutes />\s*</BrowserRouter>\s*\)\s*\}', app_comp, c)
    
    with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
        f.write(c)
