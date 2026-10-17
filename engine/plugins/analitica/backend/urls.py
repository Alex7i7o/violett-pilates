from django.urls import path
from .views import AnaliticaDashboardView, TestEmailView

urlpatterns = [
    path('analitica/dashboard/', AnaliticaDashboardView.as_view(), name='analitica-dashboard'),
    path('analitica/test-email/', TestEmailView.as_view(), name='analitica-test-email'),
]
