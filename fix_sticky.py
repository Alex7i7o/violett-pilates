with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '''        {/* Right Column: Bolsa de Trabajo */}
        <div className="space-y-8">''',
    '''        {/* Right Column: Bolsa de Trabajo */}
        <div className="space-y-8 lg:sticky lg:top-24 h-[calc(100vh-8rem)] overflow-y-auto pr-2">'''
)

with open('frontend/src/pages/profesor/ProfesorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('ProfesorDashboard updated')
