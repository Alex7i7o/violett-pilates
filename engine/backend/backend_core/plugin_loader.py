import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def get_client_config():
    # En Docker, BASE_DIR es /app. En local, BASE_DIR es engine/backend.
    # El archivo se monta en /app/config/client-config.json
    config_path = BASE_DIR / 'config' / 'client-config.json'
    if not config_path.exists():
        # Fallback for local development if needed
        config_path = BASE_DIR.parent.parent / 'config_pilates' / 'client-config.json'
    
    if not config_path.exists():
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def get_active_plugins():
    config = get_client_config()
    plugins = config.get('active_plugins', [])
    
    django_apps = []
    for p in plugins:
        app_name = f'plugins.{p}.backend'
        plugin_dir = BASE_DIR / 'plugins' / p / 'backend'
        if not plugin_dir.exists():
            plugin_dir = BASE_DIR.parent / 'plugins' / p / 'backend'
            
        if plugin_dir.exists():
            django_apps.append(app_name)
    return django_apps

def get_plugin_urls():
    urls = []
    for p in get_active_plugins():
        # p is 'plugins.<name>.backend'
        plugin_path = p.split('.')[1] # name
        url_file = BASE_DIR / 'plugins' / plugin_path / 'backend' / 'urls.py'
        if not url_file.exists():
            url_file = BASE_DIR.parent / 'plugins' / plugin_path / 'backend' / 'urls.py'
            
        if url_file.exists():
            urls.append(("api/", f"{p}.urls"))
    return urls

def get_plugin_config(plugin_name):
    config = get_client_config()
    plugin_configs = config.get('plugin_config', {})
    return plugin_configs.get(plugin_name, {})
