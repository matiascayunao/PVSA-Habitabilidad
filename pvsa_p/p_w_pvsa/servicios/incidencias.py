from contextlib import contextmanager

from django.db import transaction
from django.utils import timezone

from ..models import ReporteIncidencia


@contextmanager
def reporte_atomico(reporte):
    foto_nueva = reporte.foto if reporte.foto and not reporte.foto._committed else None
    try:
        with transaction.atomic():
            yield
    except Exception:
        if foto_nueva and foto_nueva._committed and foto_nueva.name:
            foto_nueva.storage.delete(foto_nueva.name)
            foto_nueva.name = None
        raise


def guardar_reporte_publico(reporte, lugar, datos):
    reporte.lugar = lugar
    reporte.origen = ReporteIncidencia.Origen.QR_PUBLICO
    reporte.reportado_por = None
    opcion = datos['elemento_opcion']
    if opcion == 'otro':
        reporte.elemento_reportado = datos['otro_elemento'].strip()
    else:
        reporte.elemento_reportado = opcion
    with reporte_atomico(reporte):
        reporte.full_clean()
        reporte.save()

def guardar_reporte_interno(reporte, lugar, usuario, datos):
    reporte.lugar = lugar
    reporte.origen = ReporteIncidencia.Origen.INTERNO
    reporte.reportado_por = usuario
    reporte.estado = ReporteIncidencia.Estado.NUEVO
    reporte.atendido_por = None
    opcion = datos['elemento_opcion']
    reporte.elemento_reportado = (datos.get('otro_elemento') or '').strip() if opcion == 'otro' else opcion
    with reporte_atomico(reporte):
        reporte.full_clean()
        reporte.save()

def actualizar_estado_incidencia(reporte, estado_nuevo, observacion, usuario):
    estado_anterior = reporte.estado
    ahora = timezone.now()
    reporte.estado = estado_nuevo
    reporte.observacion_resolucion = observacion
    if estado_nuevo in (ReporteIncidencia.Estado.EN_REVISION, ReporteIncidencia.Estado.RESUELTO, ReporteIncidencia.Estado.DESCARTADO):
        if reporte.fecha_inicio_atencion is None:
            reporte.fecha_inicio_atencion = ahora
        if estado_anterior != estado_nuevo:
            reporte.atendido_por = usuario
    if estado_nuevo == ReporteIncidencia.Estado.RESUELTO:
        if estado_anterior != estado_nuevo:
            reporte.fecha_resolucion = ahora
    elif estado_anterior == ReporteIncidencia.Estado.RESUELTO:
        reporte.fecha_resolucion = None
    reporte.save(update_fields=['estado', 'observacion_resolucion', 'atendido_por', 'fecha_inicio_atencion', 'fecha_resolucion'])
