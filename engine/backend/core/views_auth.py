from dj_rest_auth.views import LoginView
from rest_framework.throttling import ScopedRateThrottle

class AuthThrottle(ScopedRateThrottle):
    scope = 'auth'

class ThrottledLoginView(LoginView):
    authentication_classes = []
    throttle_scope = 'auth'
    throttle_classes = [AuthThrottle]

