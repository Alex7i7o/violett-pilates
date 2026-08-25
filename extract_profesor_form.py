import re
with open('profs_admin.txt', 'r', encoding='utf-16le') as f:
    content = f.read()

form_match = re.search(r'(<form.*?<\/form>)', content, flags=re.DOTALL)
if form_match:
    print(form_match.group(1)[:500] + "\n...\n" + form_match.group(1)[-500:])
