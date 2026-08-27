import os
import re

for root, _, files in os.walk('core'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # replace now.date() with timezone.localdate(now) if now is timezone.now()
            # wait, it's safer to just replace now.date() with timezone.localdate(now)
            content = content.replace("now.date()", "timezone.localdate(now)")
            
            # replace datetime.date.today() with timezone.localdate()
            content = content.replace("datetime.date.today()", "timezone.localdate()")
            
            if content != original_content:
                # Ensure timezone is imported
                if "from django.utils import timezone" not in content and "django.utils.timezone" not in content:
                    content = "from django.utils import timezone\n" + content
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed dates in {path}")
