import React, { useState } from 'react';
import { Badge } from '../ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { PlanSelectionModal } from './PlanSelectionModal';
import { type ClientProfile } from '../../hooks/useClientProfile';

interface ClientProfileHeaderProps {
  profile: ClientProfile;
}

export function ClientProfileHeader({ profile }: ClientProfileHeaderProps) {
  const [isPlanModalOpen, setIsPlanModalOpen] = useState(false);

  const formatExpirationDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    try {
      const datePart = dateStr.split('T')[0];
      const [year, month, day] = datePart.split('-').map(Number);
      const date = new Date(year, month - 1, day);
      if (isNaN(date.getTime())) return 'N/A';
      return new Intl.DateTimeFormat('es-AR', { day: 'numeric', month: 'long', year: 'numeric' }).format(date);
    } catch(e) {
      return 'N/A';
    }
  };

  return (
    <>
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Hola, {profile.name}</h1>
          <p className="text-muted mt-1">Bienvenida de nuevo a Violett Pilates.</p>
        </div>
        <Badge variant={profile.daysUntilExpiration < 7 ? "destructive" : "secondary"} className="text-sm px-4 py-1">
          Vence en {profile.daysUntilExpiration} días
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-gradient-to-br from-violett-900 to-violett-700 text-white border-none shadow-glass">
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
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg text-muted">Clases Disponibles</CardTitle>
          </CardHeader>
          <CardContent className="flex items-baseline gap-2">
            <span className="text-4xl font-bold text-violett-900">{profile.remainingClasses}</span>
            <span className="text-muted font-medium">de {profile.totalClasses}</span>
          </CardContent>
        </Card>
      </div>
      
      <PlanSelectionModal 
        isOpen={isPlanModalOpen} 
        onClose={() => setIsPlanModalOpen(false)} 
        currentPlan={profile.activePlan}
      />
    </>
  );
}
