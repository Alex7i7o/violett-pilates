with open('frontend/src/components/booking/BookingGrid.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip().startswith('<Card key={turno.id}'):
        new_lines.append('                <motion.div key={turno.id} variants={{ hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0, transition: { type: \"spring\", duration: 0.4, bounce: 0.1 } } }}>\n')
        line = line.replace('key={turno.id} ', '')
    new_lines.append(line)

with open('frontend/src/components/booking/BookingGrid.tsx', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed')
