from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import json
import os
import mercadopago
from django.apps import apps

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        servicio_id = request.data.get('servicio_id')
        regla_id = request.data.get('regla_id')
        
        titulo = "Item"
        precio = 0.0
        ref_id = ""
        item_type = ""

        if plan_id:
            if 'membresias' not in [app.name for app in apps.get_app_configs()]:
                return Response({"detail": "Membresias no está activo."}, status=status.HTTP_400_BAD_REQUEST)
            from plugins.membresias.backend.models import Plan
            try:
                plan = Plan.objects.get(id=plan_id)
                titulo = plan.nombre
                precio = float(plan.precio)
                ref_id = str(plan.id)
                item_type = "plan"
            except Plan.DoesNotExist:
                return Response({"detail": "Plan no encontrado."}, status=status.HTTP_404_NOT_FOUND)
                
        elif servicio_id and regla_id:
            from plugins.estetica_servicios.backend.models import ServicioEstetica
            from plugins.estetica_paquetes.backend.models import ReglaPaquete
            try:
                servicio = ServicioEstetica.objects.get(id=servicio_id)
                regla = ReglaPaquete.objects.get(id=regla_id)
                
                # Calcular descuento
                precio_base_total = float(servicio.precio_base) * regla.cantidad_sesiones
                descuento = float(regla.descuento_porcentaje) / 100.0
                precio = precio_base_total * (1 - descuento)
                
                titulo = f"Paquete de {regla.cantidad_sesiones} Sesiones: {servicio.nombre}"
                ref_id = f"{servicio.id}_{regla.id}"
                item_type = "servicio_regla"
            except ServicioEstetica.DoesNotExist:
                return Response({"detail": "Servicio no encontrado."}, status=status.HTTP_404_NOT_FOUND)
            except ReglaPaquete.DoesNotExist:
                return Response({"detail": "Regla no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"detail": "Faltan parámetros."}, status=status.HTTP_400_BAD_REQUEST)

        # Leer configuración
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config', 'client-config.json')
        if not os.path.exists(config_path):
             config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config_estetica', 'client-config.json')
             
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        pagos_cfg = config.get('plugin_config', {}).get('pagos', {})
        metodo = pagos_cfg.get('metodo_activo', 'alias')
        
        if metodo == 'alias':
            return Response({
                "type": "alias",
                "info": pagos_cfg.get('alias_info', {})
            })
        elif metodo == 'mercadopago':
            mp_cfg = pagos_cfg.get('mercadopago', {})
            access_token = os.environ.get('MP_ACCESS_TOKEN', mp_cfg.get('access_token'))
            if not access_token:
                return Response({"detail": "MercadoPago no configurado."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            sdk = mercadopago.SDK(access_token)
            
            preference_data = {
                "items": [
                    {
                        "title": titulo,
                        "quantity": 1,
                        "unit_price": precio,
                        "currency_id": "ARS"
                    }
                ],
                "payer": {
                    "email": request.user.email,
                    "name": request.user.nombre,
                    "surname": request.user.apellido
                },
                "external_reference": f"{request.user.id}_{item_type}_{ref_id}",
                "back_urls": {
                    "success": config.get('domain', 'http://localhost/estetica/app') + "/mi-cuenta?payment=success",
                    "failure": config.get('domain', 'http://localhost/estetica/app') + "/mi-cuenta?payment=failure",
                    "pending": config.get('domain', 'http://localhost/estetica/app') + "/mi-cuenta?payment=pending"
                },
                "auto_return": "approved"
            }
            
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]
            
            return Response({
                "type": "mercadopago",
                "init_point": preference["init_point"],
                "preference_id": preference["id"]
            })
        else:
            return Response({"detail": "Método de pago no soportado."}, status=status.HTTP_400_BAD_REQUEST)
