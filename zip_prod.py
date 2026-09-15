import zipfile
import os

print("Creating ultimate deploy zip...")
folders = ['engine', 'proxy', 'config_pilates', 'config_estetica', 'landings']
files = ['docker-compose.yml', '.env.example', 'deploy.sh']

def should_ignore(path):
    parts = path.split(os.sep)
    # Ignore node_modules, __pycache__, .git, venv everywhere
    for ignore_dir in ['node_modules', '__pycache__', 'venv', 'env', '.git']:
        if ignore_dir in parts:
            return True
    
    # Ignore engine/frontend/dist but DO NOT ignore landings/dist!
    # Because engine/frontend builds via Docker, but landings is served directly.
    if 'engine' in parts and 'dist' in parts:
        return True
        
    if path.endswith('.pyc') or path.endswith('.tar.gz') or path.endswith('.zip') or path.endswith('tree.txt'):
        return True
    return False

with zipfile.ZipFile("ViolettPilates-Deploy.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
    for fd in folders:
        if os.path.exists(fd):
            for root, dirs, filenames in os.walk(fd):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    if not should_ignore(filepath):
                        zf.write(filepath, filepath)
    
    for f in files:
        if os.path.exists(f):
            zf.write(f, f)

print("Zip created successfully.")