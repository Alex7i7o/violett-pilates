from django.urls import path
from .views import AnaliticaDashboardView

urlpatterns = [
    path('analitica/dashboard/', AnaliticaDashboardView.as_view(), name='analitica-dashboard'),
]
