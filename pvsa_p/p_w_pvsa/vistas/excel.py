import json
import re
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from openpyxl import load_workbook
from ..excel_utils import build_excel_plantilla_carga_masiva
from ..excel_utils import build_excel_sectores
from ..models import Sector
from ..models import Ubicacion
from ..models import Piso
from ..models import Lugar
from ..models import TipoLugar
from ..models import CategoriaObjeto
from ..models import Objeto
from ..models import TipoObjeto
from ..models import ObjetoLugar

@login_required
def descargar_excel_sectores(request):
    ubicaciones = Ubicacion.objects.select_related('sector').order_by('sector__sector', 'ubicacion')
    xlsx_bytes = build_excel_sectores(ubicaciones)
    hoy = date.today().strftime('%d-%m-%Y')
    filename = f'PUERTO_{hoy}.xlsx'
    response = HttpResponse(xlsx_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename= "{filename}"'
    return response

def _norm_header(x: object) -> str:
    if x is None:
        return ''
    s = str(x).strip()
    s = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
    return s.lower().replace(' ', '').replace('_', '')

def _clean_text(x: object) -> str:
    if x is None:
        return ''
    s = str(x).strip()
    return '' if s == '-' else s

def _to_int(value, default=0):
    try:
        if value in (None, ''):
            return default
        return int(float(value))
    except Exception:
        return default

def _importancia_to_int(value):
    s = _clean_text(value).lower()
    if s in ('3', 'alta', 'critica', 'crítica', 'alta/critica', 'alta / critica', 'alta/crítica', 'alta / crítica'):
        return 3
    if s in ('2', 'media'):
        return 2
    return 1

def _entero_importacion(valor, campo, fila, predeterminado=None):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        if predeterminado is not None:
            return predeterminado
        raise ValueError(f'Fila {fila}: el campo "{campo}" es obligatorio.')
    if isinstance(valor, bool):
        raise ValueError(f'Fila {fila}: "{campo}" debe ser un número entero válido.')
    try:
        numero = Decimal(str(valor).strip())
    except (InvalidOperation, ValueError, OverflowError):
        raise ValueError(f'Fila {fila}: "{campo}" debe ser un número entero válido.')
    if not numero.is_finite():
        raise ValueError(f'Fila {fila}: "{campo}" debe ser un número entero válido.')
    if numero > 2147483647 or numero < -2147483648:
        raise ValueError(f'Fila {fila}: "{campo}" está fuera del rango permitido.')
    if numero != numero.to_integral_value():
        raise ValueError(f'Fila {fila}: "{campo}" debe ser un número entero válido.')
    return int(numero)


def _importancia_importacion(valor, fila):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ValueError(f'Fila {fila}: el campo "Importancia" debe indicarse explícitamente (Baja, Media o Alta / Crítica).')
    try:
        numero = _entero_importacion(valor, 'Importancia', fila)
        if numero in (1, 2, 3):
            return numero
    except ValueError:
        pass
    nombre = _norm_header(valor)
    equivalencias = {
        'baja': 1,
        'media': 2,
        'alta': 3,
        'critica': 3,
        'alta/critica': 3,
    }
    if nombre in equivalencias:
        return equivalencias[nombre]
    raise ValueError(f'Fila {fila}: "Importancia" debe ser Baja, Media o Alta / Crítica.')


def _normalizar_fila_importacion(fila_datos, numero_fila, *, permitir_estado_legado=False):
    if not isinstance(fila_datos, dict):
        raise ValueError(f'Fila {numero_fila}: formato de datos no válido.')

    # Una importación actualiza los inventarios existentes. Nunca se deben
    # interpretar campos operativos omitidos como 0, 1 ni reconstruirlos desde
    # el estado B/P/M: el estado no contiene los contadores exactos.
    campos_operativos = (
        ('cantidad_mala', 'Con falla'),
        ('cantidad_pendiente', 'Por revisar'),
        ('minimo_operativo', 'Mínimo operativo'),
        ('importancia', 'Importancia'),
    )
    for clave, etiqueta in campos_operativos:
        valor = fila_datos.get(clave)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            raise ValueError(
                f'Fila {numero_fila}: falta "{etiqueta}". '
                'Para evitar sobrescribir datos del inventario con valores supuestos, '
                'completa Con falla, Por revisar, Mínimo operativo e Importancia. '
                'Escribe 0 explícitamente si no hay unidades con falla o por revisar.'
            )

    cantidad = _entero_importacion(fila_datos.get('cantidad'), 'Cantidad total', numero_fila)
    malas = _entero_importacion(fila_datos.get('cantidad_mala'), 'Con falla', numero_fila)
    pendientes = _entero_importacion(fila_datos.get('cantidad_pendiente'), 'Por revisar', numero_fila)
    minimo = _entero_importacion(fila_datos.get('minimo_operativo'), 'Mínimo operativo', numero_fila)
    importancia = _importancia_importacion(fila_datos.get('importancia'), numero_fila)

    if cantidad <= 0:
        raise ValueError(f'Fila {numero_fila}: la cantidad total debe ser mayor que cero.')
    if malas < 0 or pendientes < 0:
        raise ValueError(f'Fila {numero_fila}: "Con falla" y "Por revisar" no pueden ser negativos.')
    if minimo < 1 or minimo > cantidad:
        raise ValueError(f'Fila {numero_fila}: el mínimo operativo debe estar entre 1 y la cantidad total.')

    # Se conserva el argumento permitir_estado_legado para compatibilidad
    # con las llamadas existentes, pero no se reconstruyen cifras a partir
    # de un estado legado. Si faltan cifras, el archivo ya fue rechazado.

    if malas + pendientes > cantidad:
        raise ValueError(
            f'Fila {numero_fila}: la suma de "Con falla" y "Por revisar" '
            'no puede superar la cantidad total.'
        )

    campos_texto = ('sector', 'ubicacion', 'piso', 'tipo_de_lugar', 'lugar',
                    'categoria', 'objeto', 'tipo_objeto', 'marca', 'material', 'detalle')
    resultado = {campo: _clean_text(fila_datos.get(campo)) for campo in campos_texto}
    # El Excel exportado presenta la variante como "Marca - Material".
    # Cada componente admite hasta 100 caracteres, por lo que el texto
    # compuesto puede ocupar 203 (100 + 3 del separador + 100).
    for campo in campos_texto:
        limite = 200 if campo == 'detalle' else (203 if campo == 'tipo_objeto' else 100)
        if len(resultado[campo]) > limite:
            raise ValueError(f'Fila {numero_fila}: "{campo}" no puede superar {limite} caracteres.')

    # En el formato exportado, marca/material se obtienen de "tipo_objeto".
    # Verificar también cada componente, no solo la longitud del conjunto:
    # una marca de 120 caracteres no es válida aunque el total sea < 203.
    # Separar textos legados una sola vez, antes de mostrar la previsualización.
    # Si marca y/o material están presentes (aunque vacíos), respetar la
    # edición explícita: el usuario podría haber borrado ambos componentes.
    if 'marca' not in fila_datos and 'material' not in fila_datos:
        resultado['marca'], resultado['material'] = _split_tipo(resultado['tipo_objeto'])
    for campo in ('marca', 'material'):
        if len(resultado[campo]) > 100:
            raise ValueError(f'Fila {numero_fila}: "{campo}" no puede superar 100 caracteres.')
    for campo, etiqueta in (
        ('sector', 'Sector'), ('ubicacion', 'Ubicación'),
        ('lugar', 'Lugar'), ('objeto', 'Objeto'),
    ):
        if not resultado[campo]:
            raise ValueError(f'Fila {numero_fila}: el campo "{etiqueta}" es obligatorio.')
    resultado['tipo_de_lugar'] = resultado['tipo_de_lugar'] or 'Sin especificar'
    resultado['categoria'] = resultado['categoria'] or 'Sin categoría'
    resultado.update({
        'cantidad': cantidad,
        'cantidad_mala': malas,
        'cantidad_pendiente': pendientes,
        'minimo_operativo': minimo,
        'importancia': importancia,
        'estado': 'M' if malas > 0 else ('P' if pendientes > 0 else 'B'),
        'fecha': fila_datos.get('fecha'),
    })
    return resultado
HEADER_ALIASES = {
    'ubicacion': 'ubicacion',
    'ubicación': 'ubicacion',
    'sector': 'sector',
    'piso': 'piso',
    'tipodelugar': 'tipo_de_lugar',
    'tipolugar': 'tipo_de_lugar',
    'tipo_de_lugar': 'tipo_de_lugar',
    'lugar': 'lugar',
    'categoria': 'categoria',
    'categoría': 'categoria',
    'objeto': 'objeto',
    'tipo': 'tipo_objeto',
    'tipoobjeto': 'tipo_objeto',
    'tipo_objeto': 'tipo_objeto',
    'tipo_de_objeto': 'tipo_objeto',
    'marca': 'marca',
    'material': 'material',
    'cantidad': 'cantidad',
    'cantidadtotal': 'cantidad',
    'total': 'cantidad',
    'cantidadmala': 'cantidad_mala',
    'cantidad_mala': 'cantidad_mala',
    'malas': 'cantidad_mala',
    'mala': 'cantidad_mala',
    'fallas': 'cantidad_mala',
    'confalla': 'cantidad_mala',
    'cantidadpendiente': 'cantidad_pendiente',
    'cantidad_pendiente': 'cantidad_pendiente',
    'pendientes': 'cantidad_pendiente',
    'pendiente': 'cantidad_pendiente',
    'porrevisar': 'cantidad_pendiente',
    'minimooperativo': 'minimo_operativo',
    'mínimooperativo': 'minimo_operativo',
    'minimo_operativo': 'minimo_operativo',
    'minimo': 'minimo_operativo',
    'mínimo': 'minimo_operativo',
    'importancia': 'importancia',
    'estado': 'estado',
    'condicion': 'estado',
    'condición': 'estado',
    'detalle': 'detalle',
    'especificacion': 'detalle',
    'especificación': 'detalle',
    'observacion': 'detalle',
    'observación': 'detalle',
    'fecha': 'fecha',
}
REQUIRED_HEADERS_NORMALIZADO = {'ubicacion', 'sector', 'lugar', 'objeto', 'cantidad'}
RE_SECTOR_UBI = re.compile('sector:\\s*(.*?)\\s*\\|\\s*ubicaci[oó]n:\\s*(.*)', re.IGNORECASE)
RE_PISO = re.compile(r'^\s*piso\s*[+-]?\d+\s*$', re.IGNORECASE)
RE_TIPO_LUGAR = re.compile('^\\s*tipo\\s*de\\s*lugar\\s*:\\s*(.*)$', re.IGNORECASE)

def _row_first_text(ws, r: int) -> str:
    for c in range(1, ws.max_column + 1):
        v = ws.cell(r, c).value
        if v not in (None, ''):
            return str(v).strip()
    return ''

def _find_sector_ubicacion(ws):
    for r in range(1, min(ws.max_row, 15) + 1):
        for c in range(1, min(ws.max_column, 8) + 1):
            v = ws.cell(r, c).value
            if not v:
                continue
            m = RE_SECTOR_UBI.search(str(v))
            if m:
                return (m.group(1).strip(), m.group(2).strip())
    return (None, None)

def _parse_normalizado(wb):
    ws = wb['ObjetosLugar'] if 'ObjetosLugar' in wb.sheetnames else wb.worksheets[0]
    header_row = None
    header_map = {}
    for r in range(1, min(ws.max_row, 40) + 1):
        mapped = []
        for c in range(1, ws.max_column + 1):
            key = HEADER_ALIASES.get(_norm_header(ws.cell(r, c).value))
            if key:
                mapped.append((c, key))
        keys = set((k for _, k in mapped))
        if REQUIRED_HEADERS_NORMALIZADO.issubset(keys):
            header_row = r
            header_map = {col: key for col, key in mapped}
            break
    if not header_row:
        return []

    requeridos = (
        ('cantidad_mala', 'Con falla'),
        ('cantidad_pendiente', 'Por revisar'),
        ('minimo_operativo', 'Mínimo operativo'),
        ('importancia', 'Importancia'),
    )
    disponibles = set(header_map.values())
    faltantes = [nombre for clave, nombre in requeridos if clave not in disponibles]
    if faltantes:
        raise ValueError(
            'Este Excel de carga masiva no incluye las columnas obligatorias: '
            + ', '.join(faltantes) + '. '
            'No se puede calcular cuántas unidades están con falla o por revisar '
            'a partir del estado. Descarga la plantilla actualizada y completa '
            'los cuatro campos operativos para importar sin alterar inventarios.'
        )

    rows = []
    for r in range(header_row + 1, ws.max_row + 1):
        if not any((ws.cell(r, c).value not in (None, '') for c in range(1, ws.max_column + 1))):
            continue
        rec = {}
        for col, key in header_map.items():
            rec[key] = ws.cell(r, col).value
        # La plantilla moderna separa marca/material. En hojas normalizadas
        # antiguas sin esas columnas, interpretamos la variante una sola vez
        # antes de permitir su edición en pantalla.
        marca_val = _clean_text(rec.get('marca'))
        material_val = _clean_text(rec.get('material'))
        if 'marca' not in header_map.values() and 'material' not in header_map.values():
            marca_val, material_val = _split_tipo(_clean_text(rec.get('tipo_objeto')))
        rows.append({
            'ubicacion': _clean_text(rec.get('ubicacion')),
            'sector': _clean_text(rec.get('sector')),
            'piso': _clean_text(rec.get('piso')),
            'tipo_de_lugar': _clean_text(rec.get('tipo_de_lugar')) or 'Sin especificar',
            'lugar': _clean_text(rec.get('lugar')),
            'categoria': _clean_text(rec.get('categoria')) or 'Sin categoría',
            'objeto': _clean_text(rec.get('objeto')),
            'tipo_objeto': _clean_text(rec.get('tipo_objeto')),
            'marca': marca_val,
            'material': material_val,
            'cantidad': rec.get('cantidad') if rec.get('cantidad') is not None else 0,
            '__contadores_presentes__': any(k in ('cantidad_mala', 'cantidad_pendiente') for k in header_map.values()),
            'cantidad_mala': rec.get('cantidad_mala'),
            'cantidad_pendiente': rec.get('cantidad_pendiente'),
            'minimo_operativo': rec.get('minimo_operativo'),
            'importancia': rec.get('importancia'),
            'estado': _clean_text(rec.get('estado')),
            'detalle': _clean_text(rec.get('detalle')),
            'fecha': rec.get('fecha'),
        })
    return rows

def _parse_exportado(wb):
    rows = []
    for ws in wb.worksheets:
        sector, ubicacion = _find_sector_ubicacion(ws)
        if not sector or not ubicacion:
            continue
        current_piso = ''
        current_tipo_lugar = 'Sin especificar'
        r = 1
        max_r = ws.max_row
        while r <= max_r:
            txt = _row_first_text(ws, r)
            if txt and RE_PISO.match(txt):
                current_piso = txt
                r += 1
                continue
            if txt:
                mt = RE_TIPO_LUGAR.match(txt)
                if mt:
                    current_tipo_lugar = (mt.group(1) or '').strip() or 'Sin especificar'
                    r += 1
                    continue
            mapped = []
            for c in range(1, ws.max_column + 1):
                key = HEADER_ALIASES.get(_norm_header(ws.cell(r, c).value))
                if key:
                    mapped.append((c, key))
            keys = set((k for _, k in mapped))
            if {'objeto', 'cantidad'}.issubset(keys):
                required = {'cantidad_mala', 'cantidad_pendiente', 'minimo_operativo', 'importancia'}
                faltantes = required - keys
                if faltantes:
                    raise ValueError(
                        'Este Excel exportado es de una versión anterior y no conserva '
                        'los valores exactos de fallas, pendientes, mínimo e importancia. '
                        'Para evitar modificar inventarios por accidente, no se puede '
                        'reimportar automáticamente. Exporta un archivo actualizado desde '
                        'PVSA o utiliza la plantilla de carga masiva con esos datos completos.'
                    )
                header_map = {col: key for col, key in mapped}
                lugar = ''
                for back in (1, 2, 3, 4):
                    if r - back < 1:
                        break
                    tback = _row_first_text(ws, r - back)
                    if not tback:
                        continue
                    if RE_PISO.match(tback):
                        continue
                    if RE_TIPO_LUGAR.match(tback):
                        continue
                    lugar = tback
                    break
                if not lugar:
                    lugar = 'Sin lugar'
                col_categoria = next((c for c, k in header_map.items() if k == 'categoria'), None)
                col_objeto = next((c for c, k in header_map.items() if k == 'objeto'), None)
                col_tipo = next((c for c, k in header_map.items() if k == 'tipo_objeto'), None)
                # Las exportaciones nuevas conservan ambos componentes en
                # columnas ocultas. Las antiguas, sin ellas, siguen siendo legibles.
                col_marca = next((c for c, k in header_map.items() if k == 'marca'), None)
                col_material = next((c for c, k in header_map.items() if k == 'material'), None)
                col_cantidad = next((c for c, k in header_map.items() if k == 'cantidad'), None)
                col_mala = next((c for c, k in header_map.items() if k == 'cantidad_mala'), None)
                col_pendiente = next((c for c, k in header_map.items() if k == 'cantidad_pendiente'), None)
                col_minimo = next((c for c, k in header_map.items() if k == 'minimo_operativo'), None)
                col_importancia = next((c for c, k in header_map.items() if k == 'importancia'), None)
                col_estado = next((c for c, k in header_map.items() if k == 'estado'), None)
                col_detalle = next((c for c, k in header_map.items() if k == 'detalle'), None)
                col_fecha = next((c for c, k in header_map.items() if k == 'fecha'), None)
                rr = r + 1
                while rr <= max_r:
                    tline = _row_first_text(ws, rr)
                    if tline and (RE_PISO.match(tline) or RE_TIPO_LUGAR.match(tline)):
                        break
                    obj_val = ws.cell(rr, col_objeto).value if col_objeto else None
                    if obj_val is None or str(obj_val).strip() == '':
                        break
                    cat_val = ws.cell(rr, col_categoria).value if col_categoria else None
                    tipo_val = ws.cell(rr, col_tipo).value if col_tipo else None
                    marca_val = ws.cell(rr, col_marca).value if col_marca else None
                    material_val = ws.cell(rr, col_material).value if col_material else None
                    cant_val = ws.cell(rr, col_cantidad).value if col_cantidad else 0
                    mala_val = ws.cell(rr, col_mala).value if col_mala else None
                    pendiente_val = ws.cell(rr, col_pendiente).value if col_pendiente else None
                    minimo_val = ws.cell(rr, col_minimo).value if col_minimo else None
                    importancia_val = ws.cell(rr, col_importancia).value if col_importancia else None
                    est_val = ws.cell(rr, col_estado).value if col_estado else ''
                    det_val = ws.cell(rr, col_detalle).value if col_detalle else ''
                    fec_val = ws.cell(rr, col_fecha).value if col_fecha else None
                    # Marca/material que el Excel anterior no separaba deben
                    # mostrarse como campos editables desde el primer render.
                    if col_marca is None and col_material is None:
                        marca_val, material_val = _split_tipo(_clean_text(tipo_val))
                    rows.append({
                        'ubicacion': ubicacion,
                        'sector': sector,
                        'piso': current_piso,
                        'tipo_de_lugar': current_tipo_lugar or 'Sin especificar',
                        'lugar': lugar,
                        'categoria': _clean_text(cat_val) or 'Sin categoría',
                        'objeto': _clean_text(obj_val),
                        'tipo_objeto': _clean_text(tipo_val),
                        'marca': _clean_text(marca_val),
                        'material': _clean_text(material_val),
                        'cantidad': cant_val if cant_val is not None else 0,
                        '__contadores_presentes__': any(k in ('cantidad_mala', 'cantidad_pendiente') for k in header_map.values()),
                        'cantidad_mala': mala_val,
                        'cantidad_pendiente': pendiente_val,
                        'minimo_operativo': minimo_val,
                        'importancia': importancia_val,
                        'estado': _clean_text(est_val),
                        'detalle': _clean_text(det_val),
                        'fecha': fec_val,
                    })
                    rr += 1
                r = rr
                continue
            r += 1
    return rows

def parse_excel(file_obj):
    file_obj.seek(0)
    wb = load_workbook(file_obj, data_only=True)
    rows = _parse_normalizado(wb)
    if rows:
        return (rows, 'normalizado')
    rows = _parse_exportado(wb)
    if rows:
        return (rows, 'exportado')
    raise ValueError('No pude reconocer el formato del Excel. Usa la plantilla de carga masiva con Sector, Ubicación, Lugar, Objeto, Cantidad total, Con falla, Por revisar, Mínimo operativo e Importancia. También se admite el Excel exportado actual de PVSA.')

def _split_tipo(tipo_str: str):
    tipo_str = (tipo_str or '').strip()
    if ' - ' in tipo_str:
        marca, material = [x.strip() for x in tipo_str.split(' - ', 1)]
        return (marca, material)
    if '-' in tipo_str:
        marca, material = [x.strip() for x in tipo_str.split('-', 1)]
        return (marca, material)
    return (tipo_str, '')

def import_from_rows(rows):

    def _piso_to_int(piso_raw):
        texto = str(piso_raw if piso_raw is not None else '').strip()
        if not texto:
            return 0  # Piso omitido: comportamiento anterior de la plantilla.
        match = re.fullmatch(r'(?:Piso\s*)?([+-]?\d+)', texto, flags=re.IGNORECASE)
        if not match:
            raise ValueError(
                f'Piso inválido: {texto!r}. Ingresa un entero, por ejemplo -1, 0, 2 o Piso -1.'
            )
        numero = int(match.group(1))
        if numero < -2147483648 or numero > 2147483647:
            raise ValueError('El número de piso está fuera del rango permitido.')
        return numero

    def key(value):
        return (value or '').strip().casefold()

    def normalizar_marca(value):
        texto = (value or '').strip()
        if texto.casefold() == 'sin marca':
            return ''
        return texto

    def normalizar_material(value):
        texto = (value or '').strip()
        if texto.casefold() == 'sin material':
            return ''
        return texto
    if not isinstance(rows, list) or not rows:
        raise ValueError('La importación no contiene filas para guardar.')
    filas_validadas = [
        _normalizar_fila_importacion(fila, indice)
        for indice, fila in enumerate(rows, start=1)
    ]
    created_ol = 0
    updated_ol = 0
    cache_sector = {}
    cache_ubicacion = {}
    cache_piso = {}
    cache_tipo_lugar = {}
    cache_lugar = {}
    cache_categoria = {}
    cache_objeto = {}
    cache_variante = {}
    with transaction.atomic():
        for r in filas_validadas:
            ubicacion = r['ubicacion']
            sector = r['sector']
            piso_raw = r['piso']
            tipo_de_lugar = r['tipo_de_lugar']
            lugar = r['lugar']
            categoria = r['categoria']
            objeto = r['objeto']
            tipo_objeto_str = r['tipo_objeto']
            marca_excel = r['marca']
            material_excel = r['material']
            detalle = r['detalle']
            cantidad = r['cantidad']
            cantidad_mala = r['cantidad_mala']
            cantidad_pendiente = r['cantidad_pendiente']
            minimo_operativo = r['minimo_operativo']
            importancia = r['importancia']
            estado = r['estado']
            sector_key = key(sector)
            if sector_key in cache_sector:
                sector_obj = cache_sector[sector_key]
            else:
                sector_obj = Sector.objects.filter(sector__iexact=sector).first()
                if not sector_obj:
                    sector_obj = Sector.objects.create(sector=sector)
                cache_sector[sector_key] = sector_obj
            ubicacion_key = key(ubicacion)
            if ubicacion_key in cache_ubicacion:
                ubicacion_obj = cache_ubicacion[ubicacion_key]
            else:
                ubicacion_obj = Ubicacion.objects.select_related('sector').filter(ubicacion__iexact=ubicacion).first()
                if not ubicacion_obj:
                    ubicacion_obj = Ubicacion.objects.create(ubicacion=ubicacion, sector=sector_obj)
                cache_ubicacion[ubicacion_key] = ubicacion_obj
            # Validar también cuando la ubicación proviene de la caché.
            if ubicacion_obj.sector_id != sector_obj.id:
                raise ValueError(f'La ubicación "{ubicacion}" ya existe en el sector "{ubicacion_obj.sector.sector}" y no puede importarse también en "{sector_obj.sector}".')
            piso_int = _piso_to_int(piso_raw)
            piso_key = (piso_int, ubicacion_obj.id)
            if piso_key in cache_piso:
                piso_obj = cache_piso[piso_key]
            else:
                piso_obj = Piso.objects.filter(piso=piso_int, ubicacion=ubicacion_obj).first()
                if not piso_obj:
                    piso_obj = Piso.objects.create(piso=piso_int, ubicacion=ubicacion_obj)
                cache_piso[piso_key] = piso_obj
            tipo_lugar_key = key(tipo_de_lugar)
            if tipo_lugar_key in cache_tipo_lugar:
                tipo_lugar_obj = cache_tipo_lugar[tipo_lugar_key]
            else:
                tipo_lugar_obj = TipoLugar.objects.filter(tipo_de_lugar__iexact=tipo_de_lugar).first()
                if not tipo_lugar_obj:
                    tipo_lugar_obj = TipoLugar.objects.create(tipo_de_lugar=tipo_de_lugar)
                cache_tipo_lugar[tipo_lugar_key] = tipo_lugar_obj
            lugar_key = (key(lugar), piso_obj.id)
            if lugar_key in cache_lugar:
                lugar_obj = cache_lugar[lugar_key]
            else:
                lugar_obj = Lugar.objects.select_related('lugar_tipo_lugar').filter(piso=piso_obj, nombre_del_lugar__iexact=lugar).first()
                if not lugar_obj:
                    lugar_obj = Lugar.objects.create(nombre_del_lugar=lugar, piso=piso_obj, lugar_tipo_lugar=tipo_lugar_obj)
                cache_lugar[lugar_key] = lugar_obj
            # Un mismo lugar no puede cambiar de tipo dentro de la importación.
            if lugar_obj.lugar_tipo_lugar_id != tipo_lugar_obj.id:
                raise ValueError(f'El lugar "{lugar}" ya existe en Piso {piso_obj.piso} como tipo "{lugar_obj.lugar_tipo_lugar.tipo_de_lugar}".')
            categoria_key = key(categoria)
            if categoria_key in cache_categoria:
                categoria_obj = cache_categoria[categoria_key]
            else:
                categoria_obj = CategoriaObjeto.objects.filter(nombre_de_categoria__iexact=categoria).first()
                if not categoria_obj:
                    categoria_obj = CategoriaObjeto.objects.create(nombre_de_categoria=categoria)
                cache_categoria[categoria_key] = categoria_obj
            objeto_key = key(objeto)
            if objeto_key in cache_objeto:
                objeto_obj = cache_objeto[objeto_key]
            else:
                objeto_obj = Objeto.objects.select_related('objeto_categoria').filter(nombre_del_objeto__iexact=objeto).first()
                if not objeto_obj:
                    objeto_obj = Objeto.objects.create(nombre_del_objeto=objeto, objeto_categoria=categoria_obj)
                cache_objeto[objeto_key] = objeto_obj
            # La categoría debe coincidir incluso si el objeto ya está en caché.
            if objeto_obj.objeto_categoria_id != categoria_obj.id:
                raise ValueError(f'El objeto "{objeto}" ya existe en la categoría "{objeto_obj.objeto_categoria.nombre_de_categoria}".')
            # La previsualización envía marca/material explícitos: aunque
            # estén vacíos, nunca deben reconstruirse desde tipo_objeto.
            marca = normalizar_marca(marca_excel)
            material = normalizar_material(material_excel)
            variante_key = (objeto_obj.id, key(marca), key(material))
            if variante_key in cache_variante:
                tipo_obj = cache_variante[variante_key]
            else:
                tipo_obj = None
                for existente in TipoObjeto.objects.filter(objeto=objeto_obj):
                    marca_existente = normalizar_marca(existente.marca)
                    material_existente = normalizar_material(existente.material)
                    if key(marca_existente) == key(marca) and key(material_existente) == key(material):
                        tipo_obj = existente
                        break
                if not tipo_obj:
                    tipo_obj = TipoObjeto.objects.create(objeto=objeto_obj, marca=marca or None, material=material or None)
                cache_variante[variante_key] = tipo_obj
            obj_lugar_existente = ObjetoLugar.objects.filter(lugar=lugar_obj, tipo_de_objeto=tipo_obj).order_by('id').first()
            if obj_lugar_existente:
                obj_lugar_existente.cantidad = cantidad
                obj_lugar_existente.cantidad_mala = cantidad_mala
                obj_lugar_existente.cantidad_pendiente = cantidad_pendiente
                obj_lugar_existente.minimo_operativo = minimo_operativo
                obj_lugar_existente.importancia = importancia
                obj_lugar_existente.estado = estado
                obj_lugar_existente.detalle = detalle
                obj_lugar_existente.save()
                updated_ol += 1
            else:
                ObjetoLugar.objects.create(
                    lugar=lugar_obj,
                    tipo_de_objeto=tipo_obj,
                    cantidad=cantidad,
                    cantidad_mala=cantidad_mala,
                    cantidad_pendiente=cantidad_pendiente,
                    minimo_operativo=minimo_operativo,
                    importancia=importancia,
                    estado=estado,
                    detalle=detalle,
                )
                created_ol += 1
    return {'created': created_ol, 'updated': updated_ol}

@login_required
@require_http_methods(['GET', 'POST'])
def carga_masiva(request):
    if request.method == 'GET':
        return render(request, 'excel/carga_masiva.html', {'step': 'upload'})
    if request.POST.get('payload_json'):
        raw = {}
        try:
            raw = json.loads(request.POST['payload_json'], parse_float=Decimal)
            if not isinstance(raw, dict):
                raise ValueError('El contenido de la importación no es válido.')
            rows = raw.get('objetos_lugar', [])
            result = import_from_rows(rows)
            messages.success(request, f"Importación OK. Creados: {result['created']} | Actualizados: {result['updated']}")
            return redirect('carga_masiva')
        except Exception as e:
            return render(request, 'excel/carga_masiva.html', {'step': 'preview', 'error': str(e), 'payload': raw if isinstance(raw, dict) else {'objetos_lugar': []}, 'detected': 'manual'})
    file_obj = request.FILES.get('archivo')
    if not file_obj:
        return render(request, 'excel/carga_masiva.html', {'step': 'upload', 'error': 'Selecciona un archivo Excel (.xlsx).'})
    try:
        rows, detected = parse_excel(file_obj)
        normalized_rows = [
            _normalizar_fila_importacion(r, indice, permitir_estado_legado=True)
            for indice, r in enumerate(rows, start=1)
        ]
        payload = {'objetos_lugar': normalized_rows}
        return render(request, 'excel/carga_masiva.html', {'step': 'preview', 'payload': payload, 'detected': detected})
    except Exception as e:
        return render(request, 'excel/carga_masiva.html', {'step': 'upload', 'error': str(e)})

@login_required
def descargar_plantilla_carga_masiva(request):
    xlsx_bytes = build_excel_plantilla_carga_masiva()
    response = HttpResponse(xlsx_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename= "PLANTILLA_CARGA_MASIVA.xlsx"'
    return response