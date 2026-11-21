from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from ..models import HistoricoObjeto, ObjetoLugar
from ..pvsa_permisos import (
    es_jefe_departamento,
    historicos_propios_jefe,
    lugares_propios_jefe,
    lugares_visibles_jefe,
    puede_editar_inventario_jefe,
)


def _comprobar_jefe(request):
    if not es_jefe_departamento(request.user):
        raise PermissionDenied("Este panel es exclusivo de jefes de departamento.")


@login_required
@require_GET
def panel_jefe(request):
    _comprobar_jefe(request)

    lugares = (
        lugares_visibles_jefe(request.user)
        .select_related("piso", "piso__ubicacion", "piso__ubicacion__sector", "lugar_tipo_lugar")
        .order_by("piso__ubicacion__ubicacion", "piso__piso", "nombre_del_lugar")
    )
    propios = []
    comunes = []
    for lugar in lugares:
        if lugar.es_area_comun:
            comunes.append(lugar)
        else:
            propios.append(lugar)

    return render(
        request,
        "jefe/panel.html",
        {"lugares_propios": propios, "lugares_comunes": comunes},
    )


@login_required
@require_GET
def detalle_lugar_jefe(request, lugar_id):
    _comprobar_jefe(request)

    
    
    lugar = get_object_or_404(
        lugares_visibles_jefe(request.user).select_related(
            "piso", "piso__ubicacion", "piso__ubicacion__sector", "lugar_tipo_lugar"
        ),
        pk=lugar_id,
    )
    objetos = (
        ObjetoLugar.objects.filter(lugar=lugar)
        .select_related("tipo_de_objeto", "tipo_de_objeto__objeto")
        .order_by("-fecha", "-pk")
    )
    return render(
        request,
        "jefe/detalle_lugar.html",
        {
            "lugar": lugar,
            "objetos": objetos,
            "es_lugar_propio": puede_editar_inventario_jefe(request.user, lugar),
        },
    )


def _preparar_historicos(historicos, usuario):
    origenes = dict(lugares_propios_jefe(usuario).values_list("pk", "nombre_del_lugar"))
    for historico in historicos:
        datos = historico.variante_anterior
        historico.lugar_origen_nombre = origenes.get(datos["lugar_id"], "")
        try:
            historico.fecha_registro = parse_datetime(datos.get("fecha_registro", ""))
        except (TypeError, ValueError):
            historico.fecha_registro = None


def _contexto_historial(request):
    return urlencode([
        (nombre, request.GET[nombre])
        for nombre in ("q", "estado", "orden", "pagina") if nombre in request.GET
    ])


@login_required
@never_cache
@require_GET
def historicos_objeto_jefe(request, objeto_lugar_id):
    _comprobar_jefe(request)
    objeto = get_object_or_404(
        ObjetoLugar.objects.filter(lugar__in=lugares_propios_jefe(request.user))
        .select_related("lugar", "tipo_de_objeto__objeto"),
        pk=objeto_lugar_id,
    )
    historicos = historicos_propios_jefe(request.user).filter(objeto_del_lugar=objeto)
    consulta = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")
    orden = request.GET.get("orden", "reciente")
    if estado not in dict(HistoricoObjeto.ESTADO):
        estado = ""
    if orden not in {"reciente", "antiguo"}:
        orden = "reciente"
    if estado:
        historicos = historicos.filter(estado_anterior=estado)
    if consulta:
        historicos = historicos.filter(
            Q(detalle_anterior__icontains=consulta)
            | Q(variante_anterior__objeto__icontains=consulta)
            | Q(variante_anterior__marca__icontains=consulta)
            | Q(variante_anterior__material__icontains=consulta)
        )
    historicos = historicos.order_by("pk" if orden == "antiguo" else "-pk")
    pagina = Paginator(historicos, 50).get_page(request.GET.get("pagina"))
    pagina.object_list = list(pagina.object_list)
    _preparar_historicos(pagina, request.user)
    return render(request, "jefe/historicos.html", {
        "objeto": objeto, "pagina": pagina,
        "paginas": pagina.paginator.get_elided_page_range(pagina.number, on_each_side=1, on_ends=1),
        "consulta": consulta, "estado": estado, "orden": orden,
        "estados": HistoricoObjeto.ESTADO,
        "contexto_historial": _contexto_historial(request),
    })


@login_required
@never_cache
@require_GET
def detalle_historico_jefe(request, historico_id):
    _comprobar_jefe(request)
    historico = get_object_or_404(
        historicos_propios_jefe(request.user).select_related(
            "objeto_del_lugar__lugar__piso__ubicacion__sector",
        ),
        pk=historico_id,
    )
    _preparar_historicos([historico], request.user)
    return render(request, "historico/detalle_historico.html", {
        "historico": historico, "es_historial_jefe": True,
        "contexto_historial": _contexto_historial(request),
    })
