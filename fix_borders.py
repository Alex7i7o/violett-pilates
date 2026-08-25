# -*- coding: utf-8 -*-
import re

def remove_borders(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Dashboard.tsx
    content = content.replace('className="border-l-4 border-l-violett-700 bg-violett-50/50"', 'className="bg-violett-50/50 relative overflow-hidden"')
    content = content.replace('className="min-w-[280px] snap-start border-l-4 border-l-violett-500"', 'className="min-w-[280px] snap-start relative overflow-hidden"')
    content = content.replace('className="border-l-4 border-l-violett-500 opacity-80"', 'className="opacity-80 relative overflow-hidden bg-gray-50/50"')
    
    # ProfesorDashboard.tsx
    content = content.replace('className={`border-l-4 ${isPast ? \'border-l-gray-400 opacity-60\' : \'border-l-violett-600\'}`}', 'className={`relative overflow-hidden ${isPast ? \'opacity-60 bg-gray-50/50\' : \'\'}`}')
    content = content.replace('className="border-l-4 border-l-violett-600"', 'className="relative overflow-hidden"')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

remove_borders('frontend/src/pages/Dashboard.tsx')
remove_borders('frontend/src/pages/profesor/ProfesorDashboard.tsx')
print("Borders removed")
