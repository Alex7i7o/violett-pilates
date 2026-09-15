from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import mercadopago
import os
import json
from backend_core.hooks import registry

class MercadoPagoWebhookView(APIView):
    authentication_classes = [] # No requiere auth para el webhook
    permission_classes = []

    def post(self, request, *args, **kwargs):
        topic = request.query_params.get("topic") or request.data.get("type")
        
        if topic == "payment":
            payment_id = request.query_params.get("id") or request.data.get("data", {}).get("id")
            
            if not payment_id:
                return Response({"status": "ignored"}, status=status.HTTP_200_OK)

            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config', 'client-config.json')
            if not os.path.exists(config_path):
                 config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config_estetica', 'client-config.json')
                 
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                mp_cfg = config.get('plugin_config', {}).get('pagos', {}).get('mercadopago', {})
                access_token = os.environ.get('MP_ACCESS_TOKEN', mp_cfg.get('access_token'))
            except Exception:
                access_token = None

            if not access_token:
                return Response({"status": "error", "detail": "Missing MP_ACCESS_TOKEN"}, status=500)

            sdk = mercadopago.SDK(access_token)
            payment_info = sdk.payment().get(payment_id)

            if payment_info["status"] == 200:
                payment = payment_info["response"]
                if payment["status"] == "approved":
                    external_reference = payment.get("external_reference")
                    if external_reference:
                        try:
                            # Formato: user_id_itemtype_refid
                            parts = external_reference.split('_', 2)
                            user_id = parts[0]
                            item_type = parts[1]
                            ref_id = parts[2]
                            
                            from core.models import Usuario
                            usuario = Usuario.objects.get(id=user_id)
                            
                            # Disparar hook para que los plugins se enteren
                            if item_type == 'plan':
                                from plugins.membresias.backend.models import Plan
                                plan = Plan.objects.get(id=ref_id)
                                registry.execute('pago_confirmado', {}, usuario=usuario, plan=plan, payment_id=payment_id)
                            elif item_type == 'servicio_regla':
                                # ref_id is servicioId_reglaId
                                s_id, r_id = ref_id.split('_')
                                from plugins.estetica_servicios.backend.models import ServicioEstetica
                                from plugins.estetica_paquetes.backend.models import ReglaPaquete
                                servicio = ServicioEstetica.objects.get(id=s_id)
                                regla = ReglaPaquete.objects.get(id=r_id)
                                registry.execute('pago_servicio_regla_confirmado', {}, usuario=usuario, servicio=servicio, regla=regla, payment_id=payment_id)
                        except Exception as e:
                            print(f"[MP WEBHOOK ERROR] {e}")

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
