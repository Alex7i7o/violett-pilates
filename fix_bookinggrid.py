import re

with open('frontend/src/components/booking/BookingGrid.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace AnimatePresence mode
content = content.replace('mode="wait"', 'mode="popLayout"')

# Replace the main container motion.div
old_container = '''            <motion.div 
              key={activeDate}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3 }}
              className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
            >'''

new_container = '''            <motion.div 
              key={activeDate}
              variants={{
                hidden: { opacity: 0 },
                show: {
                  opacity: 1,
                  transition: { staggerChildren: 0.05 }
                },
                exit: { opacity: 0, y: -10, transition: { duration: 0.15, ease: "easeOut" } }
              }}
              initial="hidden"
              animate="show"
              exit="exit"
              className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
            >'''

content = content.replace(old_container, new_container)

# Replace the Card to be inside a motion.div
old_card_start = '''              {displayedTurnos.map((turno) => (
                <Card key={turno.id} className={	ransition-all hover:shadow-md }>'''

new_card_start = '''              {displayedTurnos.map((turno) => (
                <motion.div 
                  key={turno.id}
                  variants={{
                    hidden: { opacity: 0, y: 15 },
                    show: { opacity: 1, y: 0, transition: { type: "spring", duration: 0.4, bounce: 0.1 } }
                  }}
                >
                  <Card className={	ransition-all hover:shadow-md }>'''

content = content.replace(old_card_start, new_card_start)

# We also need to close the motion.div after the Card
old_card_end = '''                </Card>
              ))}'''

new_card_end = '''                </Card>
                </motion.div>
              ))}'''

content = content.replace(old_card_end, new_card_end)

with open('frontend/src/components/booking/BookingGrid.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('BookingGrid updated')
