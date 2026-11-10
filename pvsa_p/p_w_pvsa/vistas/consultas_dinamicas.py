from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from ..models import Ubicacion
from ..models import Piso
from ..models import Lugar
from ..models import TipoLugar
from ..models import CategoriaObjeto
from ..models import Objeto
from ..models import TipoObjeto
from ..models import ObjetoLugar
from ..servicios.habituales import TIPICOS_POR_TIPO_LUGAR, sugerencias_habituales


def _id_consulta(valor):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    return numero if 0 < numero <= 9223372036854775807 else None


def ajax_ubicaciones_por_sector(request):
    sector_id = _id_consulta(request.GET.get("sector_id"))
    qs = Ubicacion.objects.filter(sector_id=sector_id).order_by("ubicacion")
    data = [{"id": u.id, "nombre": u.ubicacion} for u in qs]
    return JsonResponse(data, safe=False)


def ajax_pisos_por_ubicacion(request):
    ubicacion_id = _id_consulta(request.GET.get("ubicacion_id"))
    qs = Piso.objects.filter(ubicacion_id=ubicacion_id).order_by("piso")
    data = [{"id": p.id, "nombre": f"Piso {p.piso}"} for p in qs]
    return JsonResponse(data, safe=False)


def ajax_lugares_por_piso(request):
    piso_id = (request.GET.get("piso_id") or "").strip()
    tipo_lugar_id=(request.GET.get("tipo_lugar_id")or"").strip()
    qs = Lugar.objects.all().order_by("nombre_del_lugar")
    if piso_id.isdigit():
        qs = qs.filter(piso_id=int(piso_id))
    else:
        qs=qs.none()


    if tipo_lugar_id.isdigit():
        qs = qs.filter(lugar_tipo_lugar_id=int(tipo_lugar_id))

    data = [{"id":l.id, "nombre":l.nombre_del_lugar}for l in qs]
    return JsonResponse(data, safe=False)


def ajax_objetos_por_categoria(request):
    categoria_id = _id_consulta(request.GET.get("categoria_id"))
    qs = Objeto.objects.filter(objeto_categoria_id=categoria_id).order_by(
        "nombre_del_objeto"
    )
    data = [{"id": o.id, "nombre": o.nombre_del_objeto} for o in qs]
    return JsonResponse(data, safe=False)


def ajax_tipos_por_objeto(request):
    objeto_id = _id_consulta(request.GET.get("objeto_id"))
    qs = TipoObjeto.objects.filter(objeto_id=objeto_id).order_by("marca", "material")
    data = [
        {
            "id": t.id,
            "nombre": f"{t.marca} {t.material}",
        }
        for t in qs
    ]
    return JsonResponse(data, safe=False)




@require_GET
def objetos_tipicos_por_tipo_lugar(request, tipo_lugar_pk):

    tipo_lugar = get_object_or_404(TipoLugar, pk=tipo_lugar_pk)
    return JsonResponse(sugerencias_habituales(tipo_lugar), safe=False)


@login_required
@require_GET
def ajax_filtros_dependientes(request):
    def to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    sector_id = to_int(request.GET.get("sector"))
    ubicacion_id = to_int(request.GET.get("ubicacion"))
    piso_id = to_int(request.GET.get("piso"))
    tipo_lugar_id = to_int(request.GET.get("tipo_lugar"))
    lugar_id = to_int(request.GET.get("lugar"))
    categoria_id = to_int(request.GET.get("categoria"))
    objeto_id = to_int(request.GET.get("objeto"))
    tipo_objeto_id = to_int(request.GET.get("tipo_objeto") or request.GET.get("tipo"))
    marca = (request.GET.get("marca") or "").strip()
    material = (request.GET.get("material") or "").strip()
    qs = ObjetoLugar.objects.select_related(
        "lugar",
        "lugar__piso",
        "lugar__piso__ubicacion",
        "lugar__piso__ubicacion__sector",
        "lugar__lugar_tipo_lugar",
        "tipo_de_objeto",
        "tipo_de_objeto__objeto",
        "tipo_de_objeto__objeto__objeto_categoria",
    ).all()
    if sector_id:
        qs = qs.filter(lugar__piso__ubicacion__sector_id=sector_id)
    if ubicacion_id:
        qs = qs.filter(lugar__piso__ubicacion_id=ubicacion_id)
    if piso_id:
        qs = qs.filter(lugar__piso_id=piso_id)
    if tipo_lugar_id:
        qs = qs.filter(lugar__lugar_tipo_lugar_id=tipo_lugar_id)
    if lugar_id:
        qs = qs.filter(lugar_id=lugar_id)
    if categoria_id:
        qs = qs.filter(tipo_de_objeto__objeto__objeto_categoria_id=categoria_id)
    if objeto_id:
        qs = qs.filter(tipo_de_objeto__objeto_id=objeto_id)
    if tipo_objeto_id:
        qs = qs.filter(tipo_de_objeto_id=tipo_objeto_id)
    if marca:
        qs = qs.filter(tipo_de_objeto__marca=marca)
    if material:
        qs = qs.filter(tipo_de_objeto__material=material)
    ubicacion_ids = qs.values_list("lugar__piso__ubicacion_id", flat=True).distinct()
    piso_ids = qs.values_list("lugar__piso_id", flat=True).distinct()
    tipo_lugar_ids = qs.values_list("lugar__lugar_tipo_lugar_id", flat=True).distinct()
    lugar_ids = qs.values_list("lugar_id", flat=True).distinct()
    categoria_ids = qs.values_list("tipo_de_objeto__objeto__objeto_categoria_id", flat=True).distinct()
    objeto_ids = qs.values_list("tipo_de_objeto__objeto_id", flat=True).distinct()
    tipo_objeto_ids = qs.values_list("tipo_de_objeto_id", flat=True).distinct()
    ubicaciones = (
        Ubicacion.objects
        .filter(id__in=ubicacion_ids)
        .select_related("sector")
        .order_by("sector__sector", "ubicacion")
    )
    pisos = (
        Piso.objects
        .filter(id__in=piso_ids)
        .select_related("ubicacion", "ubicacion__sector")
        .order_by("ubicacion__sector__sector", "ubicacion__ubicacion", "piso")
    )
    tipos_lugar = (
        TipoLugar.objects
        .filter(id__in=tipo_lugar_ids)
        .order_by("tipo_de_lugar")
    )
    lugares = (
        Lugar.objects
        .filter(id__in=lugar_ids)
        .select_related("piso", "piso__ubicacion", "piso__ubicacion__sector", "lugar_tipo_lugar")
        .order_by(
            "piso__ubicacion__sector__sector",
            "piso__ubicacion__ubicacion",
            "piso__piso",
            "nombre_del_lugar",
        )
    )
    categorias = (
        CategoriaObjeto.objects
        .filter(id__in=categoria_ids)
        .order_by("nombre_de_categoria")
    )
    objetos = (
        Objeto.objects
        .filter(id__in=objeto_ids)
        .select_related("objeto_categoria")
        .order_by("objeto_categoria__nombre_de_categoria", "nombre_del_objeto")
    )
    tipos_objeto = (
        TipoObjeto.objects
        .filter(id__in=tipo_objeto_ids)
        .select_related("objeto", "objeto__objeto_categoria")
        .order_by("objeto__nombre_del_objeto", "marca", "material")
    )
    marcas = (
        qs.exclude(Q(tipo_de_objeto__marca__isnull=True) | Q(tipo_de_objeto__marca__exact=""))
        .values_list("tipo_de_objeto__marca", flat=True)
        .distinct()
        .order_by("tipo_de_objeto__marca")
    )
    materiales = (
        qs.exclude(Q(tipo_de_objeto__material__isnull=True) | Q(tipo_de_objeto__material__exact=""))
        .values_list("tipo_de_objeto__material", flat=True)
        .distinct()
        .order_by("tipo_de_objeto__material")
    )
    data = {
        "ubicaciones": [
            {
                "id": u.id,
                "nombre": f"{u.ubicacion} ({u.sector.sector})" if u.sector else u.ubicacion,
            }
            for u in ubicaciones
        ],
        "pisos": [
            {
                "id": p.id,
                "nombre": f"Piso {p.piso} - {p.ubicacion.ubicacion}",
            }
            for p in pisos
        ],
        "tipos_lugar": [
            {
                "id": tl.id,
                "nombre": tl.tipo_de_lugar,
            }
            for tl in tipos_lugar
        ],
        "lugares": [
            {
                "id": l.id,
                "nombre": f"{l.nombre_del_lugar} - Piso {l.piso.piso}",
            }
            for l in lugares
        ],
        "categorias": [
            {
                "id": c.id,
                "nombre": c.nombre_de_categoria,
            }
            for c in categorias
        ],
        "objetos": [
            {
                "id": o.id,
                "nombre": o.nombre_del_objeto,
            }
            for o in objetos
        ],
        "tipos_objeto": [
            {
                "id": t.id,
                "nombre": f"{t.objeto.nombre_del_objeto} - {t.marca or 'Sin marca'} / {t.material or 'Sin material'}",
            }
            for t in tipos_objeto
        ],
        "marcas": [
            {
                "id": m,
                "nombre": m,
            }
            for m in marcas
        ],
        "materiales": [
            {
                "id": m,
                "nombre": m,
            }
            for m in materiales
        ],
    }
    return JsonResponse(data)
