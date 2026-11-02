from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from ..models import ObjetoLugar
from ..pvsa_permisos import (
    es_jefe_departamento,
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
