with open('frontend/src/pages/Dashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure motion is imported
if 'import { motion } from' not in content:
    content = content.replace("import { Card", "import { motion } from 'framer-motion'\nimport { Card")

# History section stagger
history_start = '''<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {historial.map((h: any) => (
                    <Card key={h.id} className="border-l-4 border-l-violett-500 opacity-80">'''

new_history_start = '''<motion.div 
                    variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.05 } } }}
                    initial="hidden" animate="show"
                    className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
                  >
                  {historial.map((h: any) => (
                    <motion.div key={h.id} variants={{ hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0, transition: { type: "spring", duration: 0.4, bounce: 0.1 } } }}>
                    <Card className="border-l-4 border-l-violett-500 opacity-80 h-full">'''

history_end = '''</CardContent>
                    </Card>
                  ))}
                </div>'''

new_history_end = '''</CardContent>
                    </Card>
                    </motion.div>
                  ))}
                </motion.div>'''

content = content.replace(history_start, new_history_start).replace(history_end, new_history_end)

# Upcoming bookings stagger
upcoming_start = '''<div className="flex gap-3 overflow-x-auto pb-4 snap-x">
              {myUpcomingBookings.map(turno => (
                <Card key={turno.id} className="min-w-[280px] snap-start border-l-4 border-l-violett-500">'''

new_upcoming_start = '''<motion.div 
                variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.05 } } }}
                initial="hidden" animate="show"
                className="flex gap-3 overflow-x-auto pb-4 snap-x"
              >
              {myUpcomingBookings.map(turno => (
                <motion.div key={turno.id} variants={{ hidden: { opacity: 0, scale: 0.95 }, show: { opacity: 1, scale: 1, transition: { type: "spring", duration: 0.4, bounce: 0.1 } } }}>
                <Card className="min-w-[280px] h-full snap-start border-l-4 border-l-violett-500">'''

upcoming_end = '''</CardContent>
                </Card>
              ))}
            </div>'''

new_upcoming_end = '''</CardContent>
                </Card>
                </motion.div>
              ))}
            </motion.div>'''

content = content.replace(upcoming_start, new_upcoming_start).replace(upcoming_end, new_upcoming_end)

with open('frontend/src/pages/Dashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Stagger added to Dashboard")
