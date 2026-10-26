import re

def sanitizar_para_whatsapp(texto: str) -> str:
    """
    Convierte el formato Markdown estándar generado por los LLMs a formato nativo de WhatsApp:
    1. Transforma tablas Markdown (| col | col |) en bloques ordenados con viñetas legibles en celular.
    2. Convierte encabezados de Markdown (#, ##, ###, ####) en '✦ *Título:*'.
    3. Reemplaza negrita doble (**texto**) por negrita simple nativa de WhatsApp (*texto*).
    4. Corrige negrita-itálica (***texto***) y limpia hashtags sueltos.
    """
    if not texto:
        return ""

    lines = texto.split("\n")
    processed_lines = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Detección de bloque de tabla Markdown
        if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2:
            table_lines = []
            while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 2:
                # Extraer encabezados de la primera fila
                header_raw = table_lines[0]
                headers = [c.strip() for c in header_raw[1:-1].split("|")]
                
                # Extraer filas de datos (omitiendo fila separadora |--|--|)
                data_rows = []
                for row in table_lines[1:]:
                    cells = [c.strip() for c in row[1:-1].split("|")]
                    if all(re.match(r'^[:\-\s]+$', c) for c in cells if c):
                        continue
                    data_rows.append(cells)

                # Formatear cada fila de la tabla como una tarjeta limpia de WhatsApp
                for cells in data_rows:
                    if not cells:
                        continue
                    raw_title = cells[0]
                    # Limpiar asteriscos del título para evitar dobles
                    clean_title = re.sub(r'^\*+|\*+$', '', raw_title).strip()
                    
                    card_lines = [f"✦ *{clean_title}*"]
                    
                    sub_info = []
                    desc_info = []
                    for col_idx in range(1, len(cells)):
                        val = cells[col_idx]
                        if not val:
                            continue
                        h_name = headers[col_idx] if col_idx < len(headers) else ""
                        
                        # Si es descripción larga o explicativa
                        if any(k in h_name.lower() for k in ["ideal", "descrip", "detalle", "para qué", "objetivo"]):
                            desc_info.append(val)
                        elif h_name:
                            sub_info.append(f"{h_name}: {val}")
                        else:
                            sub_info.append(val)
                    
                    if sub_info:
                        card_lines.append(f"   • {' | '.join(sub_info)}")
                    if desc_info:
                        card_lines.append(f"   • {' '.join(desc_info)}")
                    
                    processed_lines.append("\n".join(card_lines))
                    processed_lines.append("")
                continue
            else:
                processed_lines.append(table_lines[0])
                continue

        # Convertir encabezados Markdown (### Título) a formato WhatsApp
        header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if header_match:
            title = header_match.group(2).strip()
            # Si no termina en puntuación, agregar dos puntos
            if not title.endswith(('?', '!', ':', '.', '✦')):
                title = f"{title}:"
            # Si no empieza con emoji o destello, anteponer ✦
            if not title.startswith(('✦', '✨', '🌟', '•', '👉', '📅', '⏰', '🗓️', '💎')):
                title = f"✦ *{title}*"
            else:
                title = f"*{title}*"
            processed_lines.append(title)
            i += 1
            continue

        processed_lines.append(line)
        i += 1

    res = "\n".join(processed_lines)

    # 1. Convertir negrita + itálica (***texto***)
    res = re.sub(r'\*\*\*(.+?)\*\*\*', r'*_\1_*', res)

    # 2. Convertir negrita doble (Markdown **texto**) a negrita simple de WhatsApp (*texto*)
    res = re.sub(r'\*\*(.+?)\*\*', r'*\1*', res)

    # 3. Convertir doble subrayado (__texto__) a itálica (_texto_)
    res = re.sub(r'__(.+?)__', r'_\1_', res)

    # 4. Eliminar hashtags sueltos al inicio de cualquier línea
    res = re.sub(r'(?m)^#{1,6}\s*', '', res)

    # 5. Normalizar saltos de línea excesivos (máximo 2 consecutivos)
    res = re.sub(r'\n{3,}', '\n\n', res)

    return res.strip()
