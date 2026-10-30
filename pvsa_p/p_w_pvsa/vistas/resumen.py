from django.db.models import Q
from django.shortcuts import render
from ..models import Sector
from ..models import Ubicacion
from ..models import Piso
from ..models import TipoLugar
from ..models import CategoriaObjeto
from ..models import Objeto
from ..models import TipoObjeto
from ..models import ObjetoLugar


def _acumular_objeto_en_resumen(destino, ol):
    cantidad = ol.cantidad or 0
    malas = ol.cantidad_mala or 0
    pendientes = ol.cantidad_pendiente or 0
    buenas = cantidad - malas - pendientes

    if buenas < 0:
        buenas = 0

    destino["total"] += cantidad
    destino["buenas"] += buenas
    destino["pendientes"] += pendientes
    destino["malas"] += malas

    importancia = ol.importancia or 1
    destino["_op_sum"] += (ol.operatividad_objeto or 0) * importancia
    destino["_imp_sum"] += importancia


def _cerrar_resumen(destino):
    total = destino.get("total") or 0

    if total == 0:
        destino["pct_buenas"] = 0
        destino["pct_pendientes"] = 0
        destino["pct_malas"] = 0
    else:
        destino["pct_buenas"] = round((destino.get("buenas") or 0) * 100 / total, 1)
        destino["pct_pendientes"] = round((destino.get("pendientes") or 0) * 100 / total, 1)
        destino["pct_malas"] = round((destino.get("malas") or 0) * 100 / total, 1)

    imp_sum = destino.get("_imp_sum") or 0

    if imp_sum == 0:
        destino["operatividad"] = 100.0
    else:
        destino["operatividad"] = round((destino.get("_op_sum") or 0) / imp_sum, 1)

    destino.pop("_op_sum", None)
    destino.pop("_imp_sum", None)

    return destino


def resumen_general(request):

    sector_id = request.GET.get("sector") or None
    ubicacion_id = request.GET.get("ubicacion") or None
    piso_id = request.GET.get("piso") or None
    tipo_lugar_id = request.GET.get("tipo_lugar") or None
    categoria_id = request.GET.get("categoria") or None
    objeto_id = request.GET.get("objeto") or None
    tipo_objeto_id = request.GET.get("tipo_objeto") or None
    estado = request.GET.get("estado") or None
    marca = request.GET.get("marca") or None
    material = request.GET.get("material") or None

    base_qs = ObjetoLugar.objects.select_related(
        "lugar",
        "lugar__piso",
        "lugar__piso__ubicacion",
        "lugar__piso__ubicacion__sector",
        "lugar__lugar_tipo_lugar",
        "tipo_de_objeto",
        "tipo_de_objeto__objeto",
        "tipo_de_objeto__objeto__objeto_categoria",
    )

    if sector_id:
        base_qs = base_qs.filter(lugar__piso__ubicacion__sector_id=sector_id)

    if ubicacion_id:
        base_qs = base_qs.filter(lugar__piso__ubicacion_id=ubicacion_id)

    if piso_id:
        base_qs = base_qs.filter(lugar__piso_id=piso_id)

    if tipo_lugar_id:
        base_qs = base_qs.filter(lugar__lugar_tipo_lugar_id=tipo_lugar_id)

    if categoria_id:
        base_qs = base_qs.filter(
            tipo_de_objeto__objeto__objeto_categoria_id=categoria_id
        )

    if objeto_id:
        base_qs = base_qs.filter(tipo_de_objeto__objeto_id=objeto_id)

    if tipo_objeto_id:
        base_qs = base_qs.filter(tipo_de_objeto_id=tipo_objeto_id)

    if estado:
        base_qs = base_qs.filter(estado=estado)

    if marca:
        base_qs = base_qs.filter(tipo_de_objeto__marca=marca)

    if material:
        base_qs = base_qs.filter(tipo_de_objeto__material=material)

    objetos_filtrados = list(base_qs)

    sectores_map = {}

    for ol in objetos_filtrados:
        if not ol.lugar or not ol.lugar.piso or not ol.lugar.piso.ubicacion or not ol.lugar.piso.ubicacion.sector:
            continue

        sector = ol.lugar.piso.ubicacion.sector
        key = sector.id

        if key not in sectores_map:
            sectores_map[key] = {
                "lugar__piso__ubicacion__sector__id": sector.id,
                "lugar__piso__ubicacion__sector__sector": sector.sector,
                "total": 0,
                "buenas": 0,
                "pendientes": 0,
                "malas": 0,
                "_op_sum": 0,
                "_imp_sum": 0,
            }

        _acumular_objeto_en_resumen(sectores_map[key], ol)

    resumen_sector = [
        _cerrar_resumen(r)
        for r in sorted(
            sectores_map.values(),
            key=lambda x: x["lugar__piso__ubicacion__sector__sector"]
        )
    ]

    ubicaciones_map = {}

    for ol in objetos_filtrados:
        if not ol.lugar or not ol.lugar.piso or not ol.lugar.piso.ubicacion:
            continue

        ubicacion = ol.lugar.piso.ubicacion
        sector = ubicacion.sector
        key = ubicacion.id

        if key not in ubicaciones_map:
            ubicaciones_map[key] = {
                "lugar__piso__ubicacion__id": ubicacion.id,
                "lugar__piso__ubicacion__ubicacion": ubicacion.ubicacion,
                "lugar__piso__ubicacion__sector__sector": sector.sector if sector else "",
                "total": 0,
                "buenas": 0,
                "pendientes": 0,
                "malas": 0,
                "_op_sum": 0,
                "_imp_sum": 0,
            }

        _acumular_objeto_en_resumen(ubicaciones_map[key], ol)

    resumen_ubic = [
        _cerrar_resumen(r)
        for r in sorted(
            ubicaciones_map.values(),
            key=lambda x: (
                x["lugar__piso__ubicacion__sector__sector"],
                x["lugar__piso__ubicacion__ubicacion"],
            )
        )
    ]
    objetos_map = {}
    malos_por_objeto = {}

    for ol in objetos_filtrados:
        if not ol.tipo_de_objeto or not ol.tipo_de_objeto.objeto:
            continue

        objeto = ol.tipo_de_objeto.objeto
        key = objeto.id

        if key not in objetos_map:
            objetos_map[key] = {
                "id": objeto.id,
                "nombre": objeto.nombre_del_objeto,
                "total": 0,
                "buenas": 0,
                "pendientes": 0,
                "malas": 0,
                "_op_sum": 0,
                "_imp_sum": 0,
            }

        _acumular_objeto_en_resumen(objetos_map[key], ol)

        if (ol.cantidad_mala or 0) > 0:
            malos_por_objeto.setdefault(key, []).append(ol)

    resumen_objetos = []

    for r in sorted(objetos_map.values(), key=lambda x: x["nombre"]):
        _cerrar_resumen(r)
        r["malos"] = malos_por_objeto.get(r["id"], [])
        resumen_objetos.append(r)

    sectores = Sector.objects.order_by("sector")

    ubicaciones = Ubicacion.objects.select_related("sector").order_by(
        "sector__sector",
        "ubicacion"
    )

    pisos = Piso.objects.select_related("ubicacion").order_by(
        "ubicacion__ubicacion",
        "piso"
    )

    tipos_lugar = TipoLugar.objects.order_by("tipo_de_lugar")

    categorias = CategoriaObjeto.objects.order_by("nombre_de_categoria")

    objetos_catalogo = Objeto.objects.select_related("objeto_categoria").order_by(
        "nombre_del_objeto"
    )

    tipos_objeto = TipoObjeto.objects.select_related("objeto").order_by(
        "objeto__nombre_del_objeto",
        "marca",
        "material"
    )

    marcas = (
        TipoObjeto.objects
        .exclude(Q(marca__isnull=True) | Q(marca__exact=""))
        .values_list("marca", flat=True)
        .distinct()
        .order_by("marca")
    )

    materiales = (
        TipoObjeto.objects
        .exclude(Q(material__isnull=True) | Q(material__exact=""))
        .values_list("material", flat=True)
        .distinct()
        .order_by("material")
    )

    estados = ObjetoLugar.ESTADO

    contexto = {
        "resumen_sector": resumen_sector,
        "resumen_ubic": resumen_ubic,
        "resumen_objetos": resumen_objetos,

        "sectores": sectores,
        "ubicaciones": ubicaciones,
        "pisos": pisos,
        "tipos_lugar": tipos_lugar,
        "categorias": categorias,
        "objetos_catalogo": objetos_catalogo,
        "tipos_objeto": tipos_objeto,
        "estados": estados,
        "marcas": marcas,
        "materiales": materiales,

        "sector_actual": sector_id or "",
        "ubicacion_actual": ubicacion_id or "",
        "piso_actual": piso_id or "",
        "tipo_lugar_actual": tipo_lugar_id or "",
        "categoria_actual": categoria_id or "",
        "objeto_actual": objeto_id or "",
        "tipo_objeto_actual": tipo_objeto_id or "",
        "estado_actual": estado or "",
        "marca_actual": marca or "",
        "material_actual": material or "",
    }

    return render(request, "resumen/resumen_general.html", contexto)
