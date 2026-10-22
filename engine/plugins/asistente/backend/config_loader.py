import os
import json
import logging
from pathlib import Path
from backend_core.plugin_loader import get_client_config, get_plugin_config, BASE_DIR

logger = logging.getLogger(__name__)

def get_brand_persona() -> str:
    """
    Carga el manual de tono, estilo y reglas de comunicacion (brand_persona.md)
    desde la carpeta de configuracion del cliente correspondiente.
    """
    # En Docker, el volumen de config suele montarse en /app/config/
    candidate_paths = [
        BASE_DIR / 'config' / 'brand_persona.md',
        BASE_DIR.parent.parent / 'config_pilates' / 'brand_persona.md',
        BASE_DIR.parent.parent / 'config_estetica' / 'brand_persona.md',
    ]

    for path in candidate_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Error leyendo brand_persona.md desde {path}: {e}")

    # Fallback si no existe archivo de persona
    client_config = get_client_config()
    business_name = client_config.get('business_name', 'Violett Pilates')
    return f"""Sos la asistente y recepcionista oficial de {business_name} ✦.
Respondé siempre con cordialidad, calidez, respeto y estilo elegante.
Utilizá voseo argentino respetuoso y el icono ✦ como separador visual."""

def get_reglas_negocio() -> str:
    """
    Carga el manual de reglas operativas y políticas de negocio (reglas_negocio.md).
    """
    candidate_paths = [
        BASE_DIR / 'config' / 'reglas_negocio.md',
        BASE_DIR.parent.parent / 'config_pilates' / 'reglas_negocio.md',
        BASE_DIR.parent.parent / 'config_estetica' / 'reglas_negocio.md',
    ]

    for path in candidate_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Error leyendo reglas_negocio.md desde {path}: {e}")
    return ""

def get_asistente_config() -> dict:
    """
    Devuelve la configuracion operativa del plugin asistente desde client-config.json.
    """
    cfg = get_plugin_config('asistente')
    default_rules = {
        "max_cupo_por_turno": 3,
        "horas_limite_cancelacion": 24,
        "estructura_sesion": "55 minutos de clase + 5 minutos de ritual de descompresión",
        "direccion": "Gral. Guido 1573, Ramos Mejía",
        "alias_transferencia": "",
        "titular_transferencia": "Débora Zárate"
    }
    
    rules = cfg.get('reglas_operativas', {})
    for k, v in default_rules.items():
        if k not in rules:
            rules[k] = v

    return {
        "nombre_asistente": cfg.get('nombre_asistente', 'Violett'),
        "telefono_estudio": cfg.get('telefono_estudio', '5491164142172'),
        "telefono_duena": cfg.get('telefono_duena', ''),
        "reglas_operativas": rules,
        "estilo_comunicacion": cfg.get('estilo_comunicacion', {
            "icono_sello": "✦",
            "tratar_de": "vos"
        }),
        "modos_activos": cfg.get('modos_activos', {
            "atencion_alumnas": True,
            "gestion_profesores": True,
            "asistente_duena": True,
            "llenado_proactivo_camillas": True
        })
    }
