# Developed by FireSeed - Fueling Innovation
from dj_rest_auth.jwt_auth import JWTCookieAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class GracefulJWTCookieAuthentication(JWTCookieAuthentication):
    """
    Subclass of JWTCookieAuthentication that prevents invalid or expired cookies
    from locking users out of AllowAny endpoints (such as login and registration).
    If a cookie token is invalid or expired, it gracefully returns None instead
    of raising an uncaught InvalidToken exception.
    Protected endpoints requiring authentication will still reject requests with 401
    ('Authentication credentials were not provided') via permission classes.
    """
    def authenticate(self, request):
        # Never perform cookie authentication on login/registration/logout endpoints
        if request.path.startswith('/api/auth/login') or request.path.startswith('/api/auth/registration'):
            return None

        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError):
            return None
