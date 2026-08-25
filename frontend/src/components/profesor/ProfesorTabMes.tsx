import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { type ProfesorDashboardData } from '../../types/profesor';
import { motion } from 'framer-motion';

interface Props {
  data: ProfesorDashboardData;
  selectedMonth: number;
  setSelectedMonth: (m: number) => void;
  selectedYear: number;
  setSelectedYear: (y: number) => void;
  formatFecha: (f: string) => string;
}

export function ProfesorTabMes({ data, selectedMonth, setSelectedMonth, selectedYear, setSelectedYear, formatFecha }: Props) {
  const months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
  return (
    <motion.div key="mes" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
      <div className="bg-white border border-violett-100 px-6 py-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
        <div className="flex items-center gap-3">
          <select 
            className="border border-violett-200 rounded-xl px-3 py-2 text-sm bg-white text-violett-900 focus:outline-none focus:ring-2 focus:ring-violett-500 font-medium"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(Number(e.target.value))}
          >
            {months.map((m, i) => (
              <option key={m} value={i+1}>{m}</option>
            ))}
          </select>
          <select 
            className="border border-violett-200 rounded-xl px-3 py-2 text-sm bg-white text-violett-900 focus:outline-none focus:ring-2 focus:ring-violett-500 font-medium"
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
          >
            {[new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        
        <div className="bg-violett-50 px-5 py-3 rounded-xl flex items-center gap-4">
          <div className="w-10 h-10 bg-violett-900 rounded-full flex items-center justify-center text-white text-lg font-bold shadow-soft">
            {data.horas_mes}
          </div>
          <div>
            <p className="text-sm font-bold text-violett-900 uppercase tracking-wider">Clases Dictadas</p>
            <p className="text-xs text-violett-600">En este mes</p>
          </div>
        </div>
      </div>
      <section>
        <h3 className="text-xl font-bold text-foreground mb-4">Clases Dictadas en el Mes</h3>
        {(!data.turnos_mes_historial || data.turnos_mes_historial.length === 0) ? (
          <Card>
            <CardContent className="py-8 text-center text-muted">
              No hay clases dictadas en este mes.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {data.turnos_mes_historial.map((t) => (
              <Card key={t.id} className="relative overflow-hidden">
                <CardContent className="flex justify-between items-center p-4">
                  <div>
                    <p className="font-bold text-foreground">{formatFecha(t.fecha)}</p>
                    <p className="text-muted text-sm">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)} hs</p>
                  </div>
                  <div className="text-right">
                    <p className="text-violett-900 font-medium">{t.clase_nombre}</p>
                    <Badge variant="outline" className="mt-1">{t.estado}</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </motion.div>
  );
}
