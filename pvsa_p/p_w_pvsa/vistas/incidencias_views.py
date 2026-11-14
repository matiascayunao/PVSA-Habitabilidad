from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import (
    FileResponse,
    Http404,
    HttpResponseBadRequest,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
)

from ..servicios.incidencias import actualizar_estado_incidencia

from ..models import (
    Sector,
    Ubicacion,
    Lugar,
    ReporteIncidencia,
)


def _verificar_administrador(usuario):
    autorizado = (
        usuario.is_authenticated
        and (
            usuario.is_superuser
            or usuario.groups.filter(
                name="Administrador"
            ).exists()
        )
    )

    if not autorizado:
        raise PermissionDenied(
            "No tienes permisos para gestionar incidencias."
        )


def _id_filtro(valor):
    valor = str(valor or "").strip()
    if len(valor) > 19 or not valor.isdecimal():
        return None
    try:
        numero = int(valor)
    except ValueError:
        return None
    return numero if numero <= 9223372036854775807 else None


@login_required(login_url="signin")
@never_cache
@require_GET
def lista_incidencias(request):
    _verificar_administrador(request.user)

    sector_id = _id_filtro(request.GET.get("sector"))
    ubicacion_id = _id_filtro(
        request.GET.get("ubicacion")
    )
    lugar_id = _id_filtro(request.GET.get("lugar"))

    estado = request.GET.get("estado", "").strip()

    estados_validos = {
        valor
        for valor, _ in ReporteIncidencia.Estado.choices
    }

    if estado not in estados_validos:
        estado = ""

    reportes = (
        ReporteIncidencia.objects
        .select_related(
            "lugar",
            "lugar__piso",
            "lugar__piso__ubicacion",
            "lugar__piso__ubicacion__sector",
        )
        .order_by("-fecha_reporte", "-pk")
    )

    if sector_id:
        reportes = reportes.filter(
            lugar__piso__ubicacion__sector_id=sector_id
        )

    if ubicacion_id:
        reportes = reportes.filter(
            lugar__piso__ubicacion_id=ubicacion_id
        )

    if lugar_id:
        reportes = reportes.filter(lugar_id=lugar_id)

    if estado:
        reportes = reportes.filter(estado=estado)

    paginador = Paginator(reportes, 20)
    pagina = paginador.get_page(
        request.GET.get("pagina")
    )

    parametros = request.GET.copy()
    parametros.pop("pagina", None)

    return render(
        request,
        "incidencias/lista_incidencias.html",
        {
            "pagina": pagina,
            "sectores": Sector.objects.order_by("sector"),
            "ubicaciones": Ubicacion.objects.order_by(
                "ubicacion"
            ),
            "lugares": Lugar.objects.order_by(
                "nombre_del_lugar"
            ),
            "estados": ReporteIncidencia.Estado.choices,
            "filtro_sector": sector_id,
            "filtro_ubicacion": ubicacion_id,
            "filtro_lugar": lugar_id,
            "filtro_estado": estado,
            "querystring": parametros.urlencode(),
        },
    )


@login_required(login_url="signin")
@never_cache
@require_http_methods(["GET", "POST"])
def detalle_incidencia(request, incidencia_id):
    _verificar_administrador(request.user)

    reporte = get_object_or_404(
        ReporteIncidencia.objects.select_related(
            "lugar",
            "lugar__piso",
            "lugar__piso__ubicacion",
            "lugar__piso__ubicacion__sector",
            "reportado_por",
            "atendido_por",
        ),
        pk=incidencia_id,
    )

    if request.method == "POST":

        if request.POST.get("accion") != "actualizar_estado":
            return HttpResponseBadRequest(
                "Acción no válida."
            )

        estado_nuevo = request.POST.get(
            "estado", ""
        ).strip()

        estados_validos = {
            valor
            for valor, _ in ReporteIncidencia.Estado.choices
        }

        if estado_nuevo not in estados_validos:
            return HttpResponseBadRequest(
                "Estado de incidencia no válido."
            )

        observacion = request.POST.get(
            "observacion_resolucion", ""
        ).strip()

        if len(observacion) > 3000:
            messages.error(
                request,
                "La observación no puede superar 3000 caracteres.",
            )
        else:
            actualizar_estado_incidencia(reporte, estado_nuevo, observacion, request.user)

            messages.success(
                request,
                "La incidencia se actualizó correctamente.",
            )

            return redirect(
                "detalle_incidencia",
                incidencia_id=reporte.pk,
            )

    return render(
        request,
        "incidencias/detalle_incidencia.html",
        {
            "reporte": reporte,
            "estados": ReporteIncidencia.Estado.choices,
        },
    )


@login_required(login_url="signin")
@never_cache
@require_GET
def foto_incidencia(request, incidencia_id):
    _verificar_administrador(request.user)

    reporte = get_object_or_404(
        ReporteIncidencia,
        pk=incidencia_id,
    )

    if not reporte.foto:
        raise Http404("La incidencia no tiene fotografía.")

    extension = Path(reporte.foto.name).suffix.lower()

    tipos = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    tipo = tipos.get(extension)

    if not tipo:
        raise Http404("Formato de imagen no disponible.")

    try:
        archivo = reporte.foto.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("No se encontró la fotografía.")

    respuesta = FileResponse(
        archivo,
        content_type=tipo,
    )

    respuesta["Cache-Control"] = (
        "private, no-store, max-age=0"
    )
    respuesta["X-Content-Type-Options"] = "nosniff"
    respuesta["Content-Security-Policy"] = (
        "default-src 'none'; sandbox"
    )

    return respuesta
