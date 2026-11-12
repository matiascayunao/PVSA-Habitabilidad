from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from ..models import ReporteIncidencia
from ..servicios.incidencias import guardar_reporte_interno, reporte_atomico
from ..pvsa_permisos import es_jefe_departamento, lugares_visibles_jefe
from ..formularios.reporte_forms import ReportePublicoForm


def _exigir_jefe(usuario):
    if not es_jefe_departamento(usuario):
        raise PermissionDenied(
            "Esta función está reservada a jefes de departamento."
        )


@login_required(login_url="signin")
@never_cache
@require_http_methods(["GET", "POST"])
def reportar_incidencia_jefe(request, lugar_id):
    _exigir_jefe(request.user)

    
    
    lugar = get_object_or_404(
        lugares_visibles_jefe(request.user).select_related(
            "piso", "piso__ubicacion", "piso__ubicacion__sector"
        ),
        pk=lugar_id,
    )

    if request.method == "POST":
        form = ReportePublicoForm(request.POST, request.FILES)

        if form.is_valid():
            reporte = form.save(commit=False)
            with reporte_atomico(reporte):
                
                if not lugares_visibles_jefe(request.user).filter(
                    pk=lugar.pk
                ).exists():
                    raise Http404("No tienes acceso a este lugar.")

                guardar_reporte_interno(reporte, lugar, request.user, form.cleaned_data)

            messages.success(
                request,
                f"Reporte #{reporte.pk} enviado correctamente. "
                "Puedes consultar su estado en Mis reportes.",
            )
            return redirect("jefe_mis_reportes")
    else:
        form = ReportePublicoForm()

    return render(
        request,
        "jefe/form_reporte.html",
        {"lugar": lugar, "form": form},
    )


@login_required(login_url="signin")
@never_cache
@require_GET
def mis_reportes_jefe(request):
    _exigir_jefe(request.user)

    
    reportes = (
        ReporteIncidencia.objects.filter(
            reportado_por=request.user,
            origen=ReporteIncidencia.Origen.INTERNO,
        )
        .select_related("lugar", "lugar__piso", "lugar__piso__ubicacion")
        .order_by("-fecha_reporte", "-pk")
    )

    pagina = Paginator(reportes, 10).get_page(request.GET.get("pagina"))
    return render(request, "jefe/mis_reportes.html", {"pagina": pagina})


@login_required(login_url="signin")
@never_cache
@require_GET
def foto_reporte_jefe(request, reporte_id):
    _exigir_jefe(request.user)

    
    
    reporte = get_object_or_404(
        ReporteIncidencia.objects.filter(
            reportado_por=request.user,
            origen=ReporteIncidencia.Origen.INTERNO,
        ),
        pk=reporte_id,
    )

    if not reporte.foto:
        raise Http404("El reporte no tiene fotografía.")

    tipos = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    tipo = tipos.get(Path(reporte.foto.name).suffix.lower())
    if not tipo:
        raise Http404("Formato de fotografía no disponible.")

    try:
        archivo = reporte.foto.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("No se encontró la fotografía.")

    respuesta = FileResponse(archivo, content_type=tipo)
    respuesta["Cache-Control"] = "private, no-store, max-age=0"
    respuesta["X-Content-Type-Options"] = "nosniff"
    respuesta["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return respuesta
