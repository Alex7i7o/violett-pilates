import os
import re

for root, _, files in os.walk('core'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # replace timezone.now().date() with timezone.localdate()
            content = content.replace("timezone.now().date()", "timezone.localdate()")
            
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed dates in {path}")
