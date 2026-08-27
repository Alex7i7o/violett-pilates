import re

with open('frontend/src/components/dashboard/ClientProfileHeader.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
content = content.replace("import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'", "import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'\nimport { Button } from '../ui/Button'\nimport { PlanSelectionModal } from './PlanSelectionModal'\nimport { useState } from 'react'")

# Add state
state_code = "  const [isPlanModalOpen, setIsPlanModalOpen] = useState(false);\n\n  return ("
content = content.replace("  return (", state_code)

# Add button
old_plan_card = """          <Card className="bg-gradient-to-br from-violett-900 to-violett-700 text-white border-none shadow-glass">
            <CardHeader>
              <CardTitle className="text-white/90 text-lg">Mi Plan Actual</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{profile.activePlan}</p>
              {profile.remainingClasses === 0 && profile.activePlan !== "Sin plan activo" ? (
                <p className="text-red-200 mt-2 text-sm font-semibold">
                  Plan agotado. Renovar el {formatExpirationDate(profile.expirationDate)}
                </p>
              ) : (
                <p className="text-violett-200 mt-2 text-sm">Válido hasta el {formatExpirationDate(profile.expirationDate)}</p>
              )}
            </CardContent>
          </Card>"""

new_plan_card = """          <Card className="bg-gradient-to-br from-violett-900 to-violett-700 text-white border-none shadow-glass">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-white/90 text-lg">Mi Plan Actual</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{profile.activePlan}</p>
              {profile.remainingClasses === 0 && profile.activePlan !== "Sin plan activo" ? (
                <p className="text-red-200 mt-2 text-sm font-semibold">
                  Plan agotado. Renovar el {formatExpirationDate(profile.expirationDate)}
                </p>
              ) : (
                <p className="text-violett-200 mt-2 text-sm">Válido hasta el {formatExpirationDate(profile.expirationDate)}</p>
              )}
              
              <Button 
                variant="outline" 
                className="mt-4 w-full bg-white/10 border-white/20 hover:bg-white/20 text-white"
                onClick={() => setIsPlanModalOpen(true)}
              >
                {profile.activePlan === "Sin plan activo" ? "Adquirir un Plan" : "Cambiar / Renovar Plan"}
              </Button>
            </CardContent>
          </Card>"""

content = content.replace(old_plan_card, new_plan_card)

# Inject modal
modal_code = """      <PlanSelectionModal 
        isOpen={isPlanModalOpen} 
        onClose={() => setIsPlanModalOpen(false)} 
        currentPlan={profile.activePlan}
      />
    </div>"""

content = content.replace("    </div>", modal_code)

with open('frontend/src/components/dashboard/ClientProfileHeader.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Header modified")
