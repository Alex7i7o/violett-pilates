import React from 'react';
import { Badge } from '../ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { type ClientProfile } from '../../hooks/useClientProfile';

interface ClientProfileHeaderProps {
  profile: ClientProfile;
}

export function ClientProfileHeader({ profile }: ClientProfileHeaderProps) {
  const formatExpirationDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return new Intl.DateTimeFormat('es-AR', { day: 'numeric', month: 'long', year: 'numeric' }).format(date);
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
          <CardHeader>
            <CardTitle className="text-white/90 text-lg">Mi Plan Actual</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{profile.activePlan}</p>
            <p className="text-violett-200 mt-2 text-sm">Válido hasta el {formatExpirationDate(profile.expirationDate)}</p>
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
    </>
  );
}
