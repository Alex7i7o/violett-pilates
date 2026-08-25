import re

with open('prof_dash.txt', 'r', encoding='utf-16le') as f:
    content = f.read()

right_col = re.search(r'\{\/\* Right Column: Bolsa de Trabajo \*\/\}[\s\S]*?<\/div>\s*<\/div>', content)
if right_col:
    print("Found right column")
else:
    print("Not found")
