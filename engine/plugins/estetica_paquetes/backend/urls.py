from rest_framework.routers import DefaultRouter
from .views import ReglaPaqueteViewSet, BilleteraClienteViewSet

router = DefaultRouter()
router.register(r'reglas-paquetes', ReglaPaqueteViewSet, basename='reglapaquete')
router.register(r'billeteras', BilleteraClienteViewSet, basename='billetera')

urlpatterns = router.urls
