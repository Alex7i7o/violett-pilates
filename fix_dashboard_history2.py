import os

with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Add button above BookingGrid
c = c.replace(
    '''      {/* Grilla de Reservas */}
      <div className="pt-4 border-t border-violett-100">
        {!showHistory ? (''',
    '''      {/* Grilla de Reservas */}
      <div className="pt-4 border-t border-violett-100">
        <div className="flex justify-end mb-4">
          <Button variant="outline" size="sm" onClick={toggleHistory}>
            {showHistory ? "Ver Agenda Disponible" : "Ver clases a las que asistí"}
          </Button>
        </div>
        {!showHistory ? ('''
)

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(c)

print("Dashboard history button fixed")
