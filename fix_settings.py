import re

with open('fireseed_project/settings.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add cookie settings at the end of the file
cookie_settings = '''
# --- SECURITY & PRODUCTION COOKIES (FASE 3) ---
# En producci\u00f3n, si DEBUG es False, se aplican pol\u00edticas estrictas de cookies (HTTPS)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # HSTS settings (descomentar al usar dominio definitivo)
    # SECURE_HSTS_SECONDS = 31536000 
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True

CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # "https://midominio.com",
]

# Update REST_AUTH with secure cookies
'''

if 'SESSION_COOKIE_SECURE' not in c:
    c += cookie_settings
    
    # Also inject JWT_AUTH_SECURE into REST_AUTH
    c = c.replace(
        "'JWT_AUTH_REFRESH_COOKIE': 'fireseed-refresh-token',",
        "'JWT_AUTH_REFRESH_COOKIE': 'fireseed-refresh-token',\n    'JWT_AUTH_SECURE': not DEBUG,\n    'JWT_AUTH_SAMESITE': 'Lax',"
    )
    
    with open('fireseed_project/settings.py', 'w', encoding='utf-8') as f:
        f.write(c)

print("Settings updated")
