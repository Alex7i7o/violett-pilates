import re
import os

with open('prof_dash.txt', 'r', encoding='utf-16le') as f:
    content = f.read()

blocks = re.findall(r'\{activeTab === \'(.*?)\' && \(\s*<motion\.div.*?>([\s\S]*?)<\/motion\.div>\s*\)\}', content)
print([b[0] for b in blocks])
