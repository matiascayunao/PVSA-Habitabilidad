import json
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ..excel_utils import build_excel_plantilla_carga_masiva, build_excel_sectores
from ..models import Ubicacion
from ..servicios.excel import (
    _norm_header,
    _clean_text,
    _to_int,
    _importancia_to_int,
    _entero_importacion,
    _importancia_importacion,
    _normalizar_fila_importacion,
    HEADER_ALIASES,
    REQUIRED_HEADERS_NORMALIZADO,
    RE_SECTOR_UBI,
    RE_PISO,
    RE_TIPO_LUGAR,
    _row_first_text,
    _find_sector_ubicacion,
    _parse_normalizado,
    _parse_exportado,
    parse_excel,
    _split_tipo,
    import_from_rows,
)


@login_required
def descargar_excel_sectores(request):
    ubicaciones = Ubicacion.objects.select_related('sector').order_by('sector__sector', 'ubicacion')
    xlsx_bytes = build_excel_sectores(ubicaciones)
    hoy = date.today().strftime('%d-%m-%Y')
    filename = f'PUERTO_{hoy}.xlsx'
    response = HttpResponse(xlsx_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename= "{filename}"'
    return response


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
