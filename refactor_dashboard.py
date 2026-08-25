import re

with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports
imports = """import { ClientProfileHeader } from '../components/dashboard/ClientProfileHeader'
import { ClientRecurringClasses } from '../components/dashboard/ClientRecurringClasses'
import { ClientUpcomingClasses } from '../components/dashboard/ClientUpcomingClasses'
"""
content = content.replace("import { ReviewForm }", imports + "import { ReviewForm }")

# Replace formatUpcomingDate
content = re.sub(r'const formatUpcomingDate = \(dateStr: string\) => \{.*?\n.*?return.*?\}\n', '', content, flags=re.DOTALL)

# Replace formatExpirationDate
content = re.sub(r'const formatExpirationDate = \(dateStr: string\) => \{.*?\n.*?return.*?\}\n', '', content, flags=re.DOTALL)

# Remove myUpcomingBookings definition
content = content.replace("const myUpcomingBookings = turnos.filter(t => t.isBookedByMe)\n\n", "")

# Replace the sections using more robust regex
content = re.sub(
    r'\{\/\* Header Profile \*\/\}[\s\S]*?\{\/\* Mi Horario Fijo \*\/\}',
    '<ClientProfileHeader profile={profile} />\n\n      {/* Mi Horario Fijo */}',
    content
)

content = re.sub(
    r'\{\/\* Mi Horario Fijo \*\/\}[\s\S]*?\{\/\* Mis Pr.ximas Clases Confirmadas \*\/\}',
    '<ClientRecurringClasses recurrencias={profile.recurrencias} onCancelClick={promptCancelRecurrencia} />\n\n      {/* Mis Proximas Clases Confirmadas */}',
    content
)

content = re.sub(
    r'\{\/\* Mis Proximas Clases Confirmadas \*\/\}[\s\S]*?\{\/\* Grilla de Reservas \*\/\}',
    '<ClientUpcomingClasses turnos={turnos} onCancelClick={setSelectedTurnoToCancel} />\n\n      {/* Grilla de Reservas */}',
    content
)

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Dashboard.tsx refactored")
