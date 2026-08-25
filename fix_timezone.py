with open('fireseed_project/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(\"TIME_ZONE = 'UTC'\", \"TIME_ZONE = 'America/Argentina/Buenos_Aires'\")

with open('fireseed_project/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Timezone fixed')
