import json
import re
import unicodedata
from datetime import date
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
RE_PISO = re.compile('^\\s*piso\\s*\\d+', re.IGNORECASE)
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
    rows = []
    for r in range(header_row + 1, ws.max_row + 1):
        if not any((ws.cell(r, c).value not in (None, '') for c in range(1, ws.max_column + 1))):
            continue
        rec = {}
        for col, key in header_map.items():
            rec[key] = ws.cell(r, col).value
        rows.append({
            'ubicacion': _clean_text(rec.get('ubicacion')),
            'sector': _clean_text(rec.get('sector')),
            'piso': _clean_text(rec.get('piso')),
            'tipo_de_lugar': _clean_text(rec.get('tipo_de_lugar')) or 'Sin especificar',
            'lugar': _clean_text(rec.get('lugar')),
            'categoria': _clean_text(rec.get('categoria')) or 'Sin categoría',
            'objeto': _clean_text(rec.get('objeto')),
            'tipo_objeto': _clean_text(rec.get('tipo_objeto')),
            'marca': _clean_text(rec.get('marca')),
            'material': _clean_text(rec.get('material')),
            'cantidad': rec.get('cantidad') if rec.get('cantidad') is not None else 0,
            'cantidad_mala': rec.get('cantidad_mala') if rec.get('cantidad_mala') is not None else 0,
            'cantidad_pendiente': rec.get('cantidad_pendiente') if rec.get('cantidad_pendiente') is not None else 0,
            'minimo_operativo': rec.get('minimo_operativo') if rec.get('minimo_operativo') is not None else 1,
            'importancia': rec.get('importancia') if rec.get('importancia') is not None else 1,
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
                    cant_val = ws.cell(rr, col_cantidad).value if col_cantidad else 0
                    mala_val = ws.cell(rr, col_mala).value if col_mala else 0
                    pendiente_val = ws.cell(rr, col_pendiente).value if col_pendiente else 0
                    minimo_val = ws.cell(rr, col_minimo).value if col_minimo else 1
                    importancia_val = ws.cell(rr, col_importancia).value if col_importancia else 1
                    est_val = ws.cell(rr, col_estado).value if col_estado else ''
                    det_val = ws.cell(rr, col_detalle).value if col_detalle else ''
                    fec_val = ws.cell(rr, col_fecha).value if col_fecha else None
                    rows.append({
                        'ubicacion': ubicacion,
                        'sector': sector,
                        'piso': current_piso,
                        'tipo_de_lugar': current_tipo_lugar or 'Sin especificar',
                        'lugar': lugar,
                        'categoria': _clean_text(cat_val) or 'Sin categoría',
                        'objeto': _clean_text(obj_val),
                        'tipo_objeto': _clean_text(tipo_val),
                        'cantidad': cant_val if cant_val is not None else 0,
                        'cantidad_mala': mala_val if mala_val is not None else 0,
                        'cantidad_pendiente': pendiente_val if pendiente_val is not None else 0,
                        'minimo_operativo': minimo_val if minimo_val is not None else 1,
                        'importancia': importancia_val if importancia_val is not None else 1,
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
    raise ValueError('No pude reconocer el formato del Excel. La plantilla debe tener como mínimo las columnas: ubicacion, sector, lugar, objeto y cantidad. También puede incluir cantidad_mala, cantidad_pendiente, minimo_operativo, importancia, detalle y fecha.')

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
        s = (piso_raw or '').strip()
        m = re.search('(\\d+)', s)
        return int(m.group(1)) if m else 0

    def _estado_to_code(estado_raw):
        s = (estado_raw or '').strip().lower()
        if s in ('b', 'bueno', 'todo bueno', 'operativo', 'funcionando'):
            return 'B'
        if s in ('p', 'pendiente', 'con pendientes', 'por revisar'):
            return 'P'
        if s in ('m', 'malo', 'con fallas', 'con falla', 'con unidades malas'):
            return 'M'
        return ''

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
        for r in rows:
            ubicacion = _clean_text(r.get('ubicacion'))
            sector = _clean_text(r.get('sector'))
            piso_raw = _clean_text(r.get('piso'))
            tipo_de_lugar = _clean_text(r.get('tipo_de_lugar')) or 'Sin especificar'
            lugar = _clean_text(r.get('lugar'))
            categoria = _clean_text(r.get('categoria')) or 'Sin categoría'
            objeto = _clean_text(r.get('objeto'))
            tipo_objeto_str = _clean_text(r.get('tipo_objeto'))
            marca_excel = _clean_text(r.get('marca'))
            material_excel = _clean_text(r.get('material'))
            detalle = _clean_text(r.get('detalle'))
            estado_excel = _estado_to_code(r.get('estado'))
            cantidad = _to_int(r.get('cantidad'), 0)
            cantidad_mala = _to_int(r.get('cantidad_mala'), 0)
            cantidad_pendiente = _to_int(r.get('cantidad_pendiente'), 0)
            minimo_operativo = _to_int(r.get('minimo_operativo'), 1)
            importancia = _importancia_to_int(r.get('importancia'))
            if not (ubicacion and sector and lugar and objeto):
                continue
            if cantidad <= 0:
                continue
            if cantidad_mala < 0:
                cantidad_mala = 0
            if cantidad_pendiente < 0:
                cantidad_pendiente = 0
            if minimo_operativo < 1:
                minimo_operativo = 1
            if minimo_operativo > cantidad:
                minimo_operativo = cantidad
            if cantidad_mala == 0 and cantidad_pendiente == 0:
                if estado_excel == 'M':
                    cantidad_mala = cantidad
                elif estado_excel == 'P':
                    cantidad_pendiente = cantidad
            if cantidad_mala + cantidad_pendiente > cantidad:
                continue
            if cantidad_mala > 0:
                estado = 'M'
            elif cantidad_pendiente > 0:
                estado = 'P'
            else:
                estado = 'B'
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
                if ubicacion_obj:
                    if ubicacion_obj.sector_id != sector_obj.id:
                        raise ValueError(f'La ubicación "{ubicacion}" ya existe en el sector "{ubicacion_obj.sector.sector}" y no puede importarse también en "{sector_obj.sector}".')
                else:
                    ubicacion_obj = Ubicacion.objects.create(ubicacion=ubicacion, sector=sector_obj)
                cache_ubicacion[ubicacion_key] = ubicacion_obj
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
                if lugar_obj:
                    if lugar_obj.lugar_tipo_lugar_id != tipo_lugar_obj.id:
                        raise ValueError(f'El lugar "{lugar}" ya existe en Piso {piso_obj.piso} como tipo "{lugar_obj.lugar_tipo_lugar.tipo_de_lugar}".')
                else:
                    lugar_obj = Lugar.objects.create(nombre_del_lugar=lugar, piso=piso_obj, lugar_tipo_lugar=tipo_lugar_obj)
                cache_lugar[lugar_key] = lugar_obj
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
                if objeto_obj:
                    if objeto_obj.objeto_categoria_id != categoria_obj.id:
                        raise ValueError(f'El objeto "{objeto}" ya existe en la categoría "{objeto_obj.objeto_categoria.nombre_de_categoria}".')
                else:
                    objeto_obj = Objeto.objects.create(nombre_del_objeto=objeto, objeto_categoria=categoria_obj)
                cache_objeto[objeto_key] = objeto_obj
            if marca_excel or material_excel:
                marca = normalizar_marca(marca_excel)
                material = normalizar_material(material_excel)
            else:
                marca, material = _split_tipo(tipo_objeto_str)
                marca = normalizar_marca(marca)
                material = normalizar_material(material)
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
            raw = json.loads(request.POST['payload_json'])
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
        normalized_rows = []
        for r in rows:
            cantidad = _to_int(r.get('cantidad'), 0)
            cantidad_mala = _to_int(r.get('cantidad_mala'), 0)
            cantidad_pendiente = _to_int(r.get('cantidad_pendiente'), 0)
            minimo_operativo = _to_int(r.get('minimo_operativo'), 1)
            importancia = _importancia_to_int(r.get('importancia'))
            estado_excel = _clean_text(r.get('estado')).upper()
            if cantidad < 0:
                cantidad = 0
            if cantidad_mala < 0:
                cantidad_mala = 0
            if cantidad_pendiente < 0:
                cantidad_pendiente = 0
            if minimo_operativo < 1:
                minimo_operativo = 1
            if cantidad > 0 and minimo_operativo > cantidad:
                minimo_operativo = cantidad
            if cantidad_mala == 0 and cantidad_pendiente == 0:
                if estado_excel in ('M', 'MALO', 'CON FALLAS', 'CON UNIDADES MALAS') and cantidad > 0:
                    cantidad_mala = cantidad
                elif estado_excel in ('P', 'PENDIENTE', 'CON PENDIENTES') and cantidad > 0:
                    cantidad_pendiente = cantidad
            if cantidad_mala + cantidad_pendiente > cantidad:
                cantidad_mala = 0
                cantidad_pendiente = 0
            if cantidad_mala > 0:
                estado_calculado = 'M'
            elif cantidad_pendiente > 0:
                estado_calculado = 'P'
            else:
                estado_calculado = 'B'
            normalized_rows.append({
                'ubicacion': _clean_text(r.get('ubicacion')),
                'sector': _clean_text(r.get('sector')),
                'piso': _clean_text(r.get('piso')),
                'tipo_de_lugar': _clean_text(r.get('tipo_de_lugar')) or 'Sin especificar',
                'lugar': _clean_text(r.get('lugar')),
                'categoria': _clean_text(r.get('categoria')) or 'Sin categoría',
                'objeto': _clean_text(r.get('objeto')),
                'tipo_objeto': _clean_text(r.get('tipo_objeto')),
                'marca': _clean_text(r.get('marca')),
                'material': _clean_text(r.get('material')),
                'cantidad': cantidad,
                'cantidad_mala': cantidad_mala,
                'cantidad_pendiente': cantidad_pendiente,
                'minimo_operativo': minimo_operativo,
                'importancia': importancia,
                'estado': estado_calculado,
                'detalle': _clean_text(r.get('detalle')),
                'fecha': r.get('fecha'),
            })
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