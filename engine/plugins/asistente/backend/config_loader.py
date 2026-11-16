import functools
import os
import re
import json
import logging
from pathlib import Path
from backend_core.plugin_loader import get_client_config, get_plugin_config, BASE_DIR

logger = logging.getLogger(__name__)

def normalizar_telefono_ar(tel: str) -> str:
    clean = re.sub(r'[^0-9]', '', str(tel or ''))
    if len(clean) == 10 and clean.startswith('11'):
        return f"549{clean}"
    if len(clean) == 12 and clean.startswith('5411'):
        return f"549{clean[2:]}"
    return clean

def limpiar_numero_telefono(phone: str) -> str:
    """Elimina espacios, guiones, signos más y paréntesis de un número telefónico."""
    if not phone:
        return ""
    return re.sub(r'[\s\+\-\(\)]', '', str(phone))

def normalizar_comparacion_ar(phone: str) -> str:
    """Extrae el núcleo numérico para comparación flexible en Argentina."""
    clean = limpiar_numero_telefono(phone)
    if clean.startswith('549'):
        clean = clean[3:]
    elif clean.startswith('54'):
        clean = clean[2:]
    if clean.startswith('0'):
        clean = clean[1:]
    if clean.startswith('15') and len(clean) == 10:
        clean = clean[2:]
    return clean

def es_telefono_staff_o_duena(phone: str) -> bool:
    """
    Verifica con tolerancia de formatos si un número corresponde a la dueña
    o a cualquier miembro del staff autorizado en la configuración.
    """
    if not phone:
        return False
    
    clean_input = limpiar_numero_telefono(phone)
    if not clean_input:
        return False
    
    core_input = normalizar_comparacion_ar(clean_input)
    ultimos_8_input = clean_input[-8:] if len(clean_input) >= 8 else clean_input

    config = get_asistente_config()
    
    # 1. Chequear lista de staff_telefonos configurados
    staff_list = config.get('staff_telefonos', [])
    for item in staff_list:
        if not item.get('activo', True):
            continue
        t_raw = item.get('telefono', '')
        t_clean = limpiar_numero_telefono(t_raw)
        if not t_clean:
            continue
        t_core = normalizar_comparacion_ar(t_clean)
        
        # Coincidencia exacta o por núcleo
        if clean_input == t_clean or (core_input and core_input == t_core):
            return True
        # Coincidencia por últimos 8 dígitos (celulares AR con o sin 9/15)
        if len(t_clean) >= 8 and len(clean_input) >= 8 and t_clean.endswith(ultimos_8_input):
            return True

    # 2. Chequear telefono_duena principal
    tel_duena = config.get('telefono_duena', '')
    if tel_duena:
        t_clean = limpiar_numero_telefono(tel_duena)
        t_core = normalizar_comparacion_ar(t_clean)
        if clean_input == t_clean or (core_input and core_input == t_core):
            return True
        if len(t_clean) >= 8 and len(clean_input) >= 8 and t_clean.endswith(ultimos_8_input):
            return True

    return False

def obtener_nombre_staff(phone: str) -> str:
    """Devuelve el nombre configurado del miembro del staff o 'Deby' por defecto."""
    if not phone:
        return "Deby"
    clean_input = limpiar_numero_telefono(phone)
    core_input = normalizar_comparacion_ar(clean_input)
    ultimos_8 = clean_input[-8:] if len(clean_input) >= 8 else clean_input

    config = get_asistente_config()
    staff_list = config.get('staff_telefonos', [])
    for item in staff_list:
        if not item.get('activo', True):
            continue
        t_clean = limpiar_numero_telefono(item.get('telefono', ''))
        t_core = normalizar_comparacion_ar(t_clean)
        if clean_input == t_clean or (core_input and core_input == t_core) or (len(t_clean) >= 8 and t_clean.endswith(ultimos_8)):
            return item.get('nombre', 'Deby')

    return config.get('reglas_operativas', {}).get('nombre_duena', 'Deby')

def obtener_telefonos_alertas_staff() -> list:
    """Devuelve los teléfonos limpios de todos los miembros del staff configurados para recibir alertas."""
    config = get_asistente_config()
    telefonos = []
    staff_list = config.get('staff_telefonos', [])
    for item in staff_list:
        if item.get('activo', True) and item.get('recibe_alertas', True):
            t_clean = limpiar_numero_telefono(item.get('telefono', ''))
            if t_clean and t_clean not in telefonos:
                telefonos.append(t_clean)
    
    # Asegurar que telefono_duena esté si la lista está vacía
    if not telefonos:
        tel_duena = config.get('telefono_duena', '')
        if tel_duena:
            t_clean = limpiar_numero_telefono(tel_duena)
            if t_clean:
                telefonos.append(t_clean)
            
    return telefonos

def obtener_todos_telefonos_staff() -> list:
    """Devuelve los teléfonos limpios de todos los miembros del staff activos."""
    config = get_asistente_config()
    telefonos = []
    staff_list = config.get('staff_telefonos', [])
    for item in staff_list:
        if item.get('activo', True):
            t_clean = limpiar_numero_telefono(item.get('telefono', ''))
            if t_clean and t_clean not in telefonos:
                telefonos.append(t_clean)
    
    tel_duena = config.get('telefono_duena', '')
    if tel_duena:
        t_clean = limpiar_numero_telefono(tel_duena)
        if t_clean and t_clean not in telefonos:
            telefonos.append(t_clean)
            
    return telefonos


@functools.lru_cache(maxsize=1)
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

@functools.lru_cache(maxsize=1)
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
        "titular_transferencia": "Débora Zárate (Deby)",
        "nombre_duena": "Deby"
    }
    
    rules = cfg.get('reglas_operativas', {})
    for k, v in default_rules.items():
        if k not in rules:
            rules[k] = v

    tel_duena_raw = (
        os.environ.get('TELEFONO_DUENA') or 
        os.environ.get('WHATSAPP_TELEFONO_DUENA') or 
        cfg.get('telefono_duena', '5491157691786')
    )
    telefono_duena = normalizar_telefono_ar(tel_duena_raw)

    staff_raw = cfg.get('staff_telefonos', [])
    staff_telefonos = []
    if isinstance(staff_raw, list):
        for s in staff_raw:
            if isinstance(s, dict):
                tel = s.get('telefono', '')
                if tel:
                    staff_telefonos.append({
                        "id": str(s.get('id', f"staff_{len(staff_telefonos)+1}")),
                        "nombre": s.get('nombre') or 'Miembro del Staff',
                        "telefono": normalizar_telefono_ar(tel),
                        "telefono_original": str(tel),
                        "rol": s.get('rol', 'DUENA'),
                        "activo": s.get('activo', True),
                        "recibe_alertas": s.get('recibe_alertas', True),
                        "notas": s.get('notas', '')
                    })
            elif isinstance(s, str) and s.strip():
                staff_telefonos.append({
                    "id": f"staff_{len(staff_telefonos)+1}",
                    "nombre": "Miembro del Staff",
                    "telefono": normalizar_telefono_ar(s),
                    "telefono_original": s.strip(),
                    "rol": "DUENA",
                    "activo": True,
                    "recibe_alertas": True,
                    "notas": ""
                })

    # Asegurar que al menos la dueña principal figure en staff_telefonos
    if not staff_telefonos and telefono_duena:
        staff_telefonos.append({
            "id": "staff_deby_1",
            "nombre": rules.get('nombre_duena', 'Débora Zárate (Deby)'),
            "telefono": telefono_duena,
            "telefono_original": tel_duena_raw,
            "rol": "DUENA",
            "activo": True,
            "recibe_alertas": True,
            "notas": "Línea oficial de la dueña"
        })

    return {
        "nombre_asistente": cfg.get('nombre_asistente', 'Violett'),
        "telefono_estudio": cfg.get('telefono_estudio', '5491164142172'),
        "telefono_duena": telefono_duena,
        "staff_telefonos": staff_telefonos,
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
