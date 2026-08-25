const fs = require('fs');
const file = 'frontend/src/pages/profesor/ProfesorDashboard.tsx';
let c = fs.readFileSync(file, 'utf8');

const newLogic = 
  const [showPast, setShowPast] = useState(false);

  if (loading) return <p className="text-muted p-4">Cargando panel...</p>;
  if (!data) return <p className="text-muted p-4">Error cargando el panel.</p>;

  // Filter turnos_hoy
  const now = new Date();
  const currentHHMM = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
  
  const upcomingHoy = data.turnos_hoy.filter((t: any) => t.hora_fin.slice(0,5) >= currentHHMM);
  const pastHoy = data.turnos_hoy.filter((t: any) => t.hora_fin.slice(0,5) < currentHHMM);
  
  const displayHoy = showPast ? [...upcomingHoy, ...pastHoy].sort((a: any, b: any) => a.hora_inicio.localeCompare(b.hora_inicio)) : upcomingHoy;

  return (
;

c = c.replace(/  if \(loading\) return[\s\S]*?return \(/, newLogic);

const oldSection = /<section>\s*<h3 className="text-xl font-bold text-foreground mb-4">Clases de Hoy<\/h3>[\s\S]*?<\/section>/;

const newSection = \          <section>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-foreground">Clases de Hoy</h3>
              {pastHoy.length > 0 && (
                <Button variant="outline" size="sm" onClick={() => setShowPast(!showPast)}>
                  {showPast ? 'Ocultar clases dadas' : 'Ver clases dadas'}
                </Button>
              )}
            </div>
            
            {displayHoy.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted">
                  No tienes más clases para hoy.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                <AnimatePresence>
                  {displayHoy.map((t: any) => {
                    const isPast = t.hora_fin.slice(0,5) < currentHHMM;
                    return (
                      <motion.div key={t.id} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                        <Card className={\\\order-l-4 \\\\\\}>
                          <CardContent className="flex justify-between items-center p-4">
                            <div>
                              <p className="font-bold text-foreground text-lg">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)}</p>
                              <p className={\\\\\\ font-medium\\\}>{t.clase_nombre}</p>
                            </div>
                            <Badge variant="default" className={\\\\\\ border-none\\\}>
                              {isPast ? 'Dada' : \\\\\\ cupos libres\\\}
                            </Badge>
                          </CardContent>
                        </Card>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            )}
          </section>\;

c = c.replace(oldSection, newSection);
fs.writeFileSync(file, c);
console.log('Done!');
