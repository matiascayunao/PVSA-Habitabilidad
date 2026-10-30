from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from ..forms import CrearObjetoLugar
from ..forms import EditarObjetoLugar
from ..models import Sector
from ..models import Ubicacion
from ..models import Piso
from ..models import Lugar
from ..models import TipoLugar
from ..models import CategoriaObjeto
from ..models import Objeto
from ..models import TipoObjeto
from ..models import ObjetoLugar
from ..models import HistoricoObjeto
from .eliminacion import _confirm_delete


@login_required
def lista_objetos_lugar(request):
    sector_id = request.GET.get("sector", "").strip()
    ubicacion_id = request.GET.get("ubicacion", "").strip()
    piso_id = request.GET.get("piso", "").strip()
    tipo_lugar_id = request.GET.get("tipo_lugar", "").strip()
    lugar_id = request.GET.get("lugar", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    objeto_id = request.GET.get("objeto", "").strip()
    tipo_id = request.GET.get("tipo", "").strip()
    estado_val = request.GET.get("estado", "").strip()
    importancia_val = request.GET.get("importancia", "").strip()
    operatividad_val = request.GET.get("operatividad", "").strip()
    marca_val = request.GET.get("marca", "").strip()
    material_val = request.GET.get("material", "").strip()

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
        try:
            qs = qs.filter(lugar__piso__ubicacion__sector_id=int(sector_id))
        except ValueError:
            sector_id = ""

    if ubicacion_id:
        try:
            qs = qs.filter(lugar__piso__ubicacion_id=int(ubicacion_id))
        except ValueError:
            ubicacion_id = ""

    if piso_id:
        try:
            qs = qs.filter(lugar__piso_id=int(piso_id))
        except ValueError:
            piso_id = ""

    if tipo_lugar_id:
        try:
            qs = qs.filter(lugar__lugar_tipo_lugar_id=int(tipo_lugar_id))
        except ValueError:
            tipo_lugar_id = ""

    if lugar_id:
        try:
            qs = qs.filter(lugar_id=int(lugar_id))
        except ValueError:
            lugar_id = ""

    if categoria_id:
        try:
            qs = qs.filter(tipo_de_objeto__objeto__objeto_categoria_id=int(categoria_id))
        except ValueError:
            categoria_id = ""

    if objeto_id:
        try:
            qs = qs.filter(tipo_de_objeto__objeto_id=int(objeto_id))
        except ValueError:
            objeto_id = ""

    if tipo_id:
        try:
            qs = qs.filter(tipo_de_objeto_id=int(tipo_id))
        except ValueError:
            tipo_id = ""

    if estado_val:
        qs = qs.filter(estado=estado_val)

    if importancia_val:
        try:
            qs = qs.filter(importancia=int(importancia_val))
        except ValueError:
            importancia_val = ""

    if marca_val:
        qs = qs.filter(tipo_de_objeto__marca=marca_val)

    if material_val:
        qs = qs.filter(tipo_de_objeto__material=material_val)

    objetos_lugar = list(
        qs.order_by(
            "lugar__piso__ubicacion__sector__sector",
            "lugar__piso__ubicacion__ubicacion",
            "lugar__piso__piso",
            "lugar__nombre_del_lugar",
            "tipo_de_objeto__objeto__nombre_del_objeto",
        )
    )

    if operatividad_val:
        filtrados = []

        for obj in objetos_lugar:
            op = obj.operatividad_objeto

            if operatividad_val == "critico" and op < 50:
                filtrados.append(obj)
            elif operatividad_val == "observacion" and op >= 50 and op < 80:
                filtrados.append(obj)
            elif operatividad_val == "operativo" and op >= 80:
                filtrados.append(obj)

        objetos_lugar = filtrados

    sectores = Sector.objects.all().order_by("sector")

    ubicaciones = (
        Ubicacion.objects.select_related("sector")
        .all()
        .order_by("sector__sector", "ubicacion")
    )

    pisos = (
        Piso.objects.select_related("ubicacion", "ubicacion__sector")
        .all()
        .order_by("ubicacion__sector__sector", "ubicacion__ubicacion", "piso")
    )

    tipos_lugar = TipoLugar.objects.all().order_by("tipo_de_lugar")

    lugares = (
        Lugar.objects.select_related(
            "piso",
            "piso__ubicacion",
            "piso__ubicacion__sector",
            "lugar_tipo_lugar",
        )
        .all()
        .order_by(
            "piso__ubicacion__sector__sector",
            "piso__ubicacion__ubicacion",
            "piso__piso",
            "nombre_del_lugar",
        )
    )

    categorias = CategoriaObjeto.objects.all().order_by("nombre_de_categoria")

    objetos = (
        Objeto.objects.select_related("objeto_categoria")
        .all()
        .order_by("objeto_categoria__nombre_de_categoria", "nombre_del_objeto")
    )

    tipos = (
        TipoObjeto.objects.select_related("objeto", "objeto__objeto_categoria")
        .all()
        .order_by("objeto__nombre_del_objeto", "marca", "material")
    )

    marcas = (
        TipoObjeto.objects.exclude(Q(marca__isnull=True) | Q(marca__exact=""))
        .values_list("marca", flat=True)
        .distinct()
        .order_by("marca")
    )

    materiales = (
        TipoObjeto.objects.exclude(Q(material__isnull=True) | Q(material__exact=""))
        .values_list("material", flat=True)
        .distinct()
        .order_by("material")
    )

    estados = ObjetoLugar.ESTADO
    importancias = ObjetoLugar.IMPORTANCIA

    return render(
        request,
        "objeto_lugar/objetos_lugar.html",
        {
            "objetos": objetos_lugar,

            "sectores": sectores,
            "ubicaciones": ubicaciones,
            "pisos": pisos,
            "tipos_lugar": tipos_lugar,
            "lugares": lugares,
            "categorias": categorias,
            "objetos_catalogo": objetos,
            "tipos": tipos,
            "marcas": marcas,
            "materiales": materiales,
            "estados": estados,
            "importancias": importancias,

            "sector_actual": sector_id,
            "ubicacion_actual": ubicacion_id,
            "piso_actual": piso_id,
            "tipo_lugar_actual": tipo_lugar_id,
            "lugar_actual": lugar_id,
            "categoria_actual": categoria_id,
            "objeto_actual": objeto_id,
            "tipo_actual": tipo_id,
            "estado_actual": estado_val,
            "importancia_actual": importancia_val,
            "operatividad_actual": operatividad_val,
            "marca_actual": marca_val,
            "material_actual": material_val,
        },
    )


@login_required
def detalle_objeto_lugar(request, objeto_lugar_id):
    obj = get_object_or_404(ObjetoLugar, pk=objeto_lugar_id)
    historicos = (
        HistoricoObjeto.objects
        .filter(objeto_del_lugar=obj)
        .order_by("-fecha_anterior")
    )
    return render(
        request,
        "objeto_lugar/detalle_objeto_lugar.html",
        {"objeto_lugar": obj, "historicos": historicos},
    )


@login_required
def crear_objeto_lugar(request, lugar_id):
    lugar = get_object_or_404(Lugar, pk=lugar_id)

    tipos_catalogo = (
        TipoObjeto.objects
        .select_related("objeto", "objeto__objeto_categoria")
        .all()
        .order_by(
            "objeto__nombre_del_objeto",
            "marca",
            "material",
        )
    )

    objetos_catalogo = (
        Objeto.objects
        .select_related("objeto_categoria")
        .all()
        .order_by("nombre_del_objeto")
    )

    categorias_catalogo = CategoriaObjeto.objects.all().order_by("nombre_de_categoria")

    nuevo_valores = {
        "modo": request.POST.get("nuevo_modo", "nuevo") if request.method == "POST" else "nuevo",
        "objeto_existente": request.POST.get("nuevo_objeto_existente", "") if request.method == "POST" else "",
        "objeto_nombre": request.POST.get("nuevo_objeto_nombre", "") if request.method == "POST" else "",
        "categoria_existente": request.POST.get("nueva_categoria_existente", "") if request.method == "POST" else "",
        "categoria_nombre": request.POST.get("nueva_categoria_nombre", "") if request.method == "POST" else "",
        "marca": request.POST.get("nueva_marca", "") if request.method == "POST" else "",
        "material": request.POST.get("nuevo_material", "") if request.method == "POST" else "",
    }

    contexto = {
        "lugar": lugar,
        "tipos_catalogo": tipos_catalogo,
        "objetos_catalogo": objetos_catalogo,
        "categorias_catalogo": categorias_catalogo,
        "nuevo_valores": nuevo_valores,
    }

    if request.method == "GET":
        contexto["form"] = CrearObjetoLugar()
        return render(
            request,
            "objeto_lugar/crear_objeto_lugar.html",
            contexto,
        )

    form = CrearObjetoLugar(request.POST)
    contexto["form"] = form

    if form.is_valid():
        tipo_objeto = form.cleaned_data.get("tipo_de_objeto")

        if not tipo_objeto:
            modo = (request.POST.get("nuevo_modo") or "").strip()
            objeto_existente_id = (request.POST.get("nuevo_objeto_existente") or "").strip()
            objeto_nuevo_nombre = (request.POST.get("nuevo_objeto_nombre") or "").strip()
            categoria_existente_id = (request.POST.get("nueva_categoria_existente") or "").strip()
            categoria_nueva_nombre = (request.POST.get("nueva_categoria_nombre") or "").strip()
            marca = (request.POST.get("nueva_marca") or "").strip()
            material = (request.POST.get("nuevo_material") or "").strip()

            objeto = None
            categoria = None

            if modo == "variante":
                if not objeto_existente_id.isdigit():
                    form.add_error(
                        "tipo_de_objeto",
                        "Selecciona el objeto al que quieres agregar una nueva marca o material.",
                    )
                else:
                    objeto = Objeto.objects.filter(pk=int(objeto_existente_id)).first()
                    if not objeto:
                        form.add_error(
                            "tipo_de_objeto",
                            "El objeto seleccionado ya no existe.",
                        )
            else:
                if not objeto_nuevo_nombre:
                    form.add_error(
                        "tipo_de_objeto",
                        "Escribe el nombre del nuevo objeto.",
                    )
                else:
                    objeto = Objeto.objects.filter(
                        nombre_del_objeto__iexact=objeto_nuevo_nombre
                    ).first()

                    if not objeto:
                        if categoria_existente_id.isdigit():
                            categoria = CategoriaObjeto.objects.filter(
                                pk=int(categoria_existente_id)
                            ).first()

                            if not categoria:
                                form.add_error(
                                    "tipo_de_objeto",
                                    "La categoría seleccionada ya no existe.",
                                )

                        elif categoria_nueva_nombre:
                            categoria = CategoriaObjeto.objects.filter(
                                nombre_de_categoria__iexact=categoria_nueva_nombre
                            ).first()

                        else:
                            form.add_error(
                                "tipo_de_objeto",
                                "Selecciona una categoría o escribe una nueva.",
                            )

            if not form.errors:
                with transaction.atomic():
                    if not objeto:
                        if not categoria:
                            categoria = CategoriaObjeto.objects.create(
                                nombre_de_categoria=categoria_nueva_nombre
                            )

                        objeto = Objeto.objects.create(
                            nombre_del_objeto=objeto_nuevo_nombre,
                            objeto_categoria=categoria,
                        )

                    tipos_qs = TipoObjeto.objects.filter(objeto=objeto)

                    if marca:
                        tipos_qs = tipos_qs.filter(marca__iexact=marca)
                    else:
                        tipos_qs = tipos_qs.filter(
                            Q(marca__isnull=True) | Q(marca__exact="")
                        )

                    if material:
                        tipos_qs = tipos_qs.filter(material__iexact=material)
                    else:
                        tipos_qs = tipos_qs.filter(
                            Q(material__isnull=True) | Q(material__exact="")
                        )

                    tipo_objeto = tipos_qs.first()

                    if not tipo_objeto:
                        tipo_objeto = TipoObjeto.objects.create(
                            objeto=objeto,
                            marca=marca,
                            material=material,
                        )

                    obj = form.save(commit=False)
                    obj.tipo_de_objeto = tipo_objeto
                    obj.lugar = lugar
                    obj.save()

                return redirect("detalle_lugar", lugar_id=lugar.id)

        else:
            obj = form.save(commit=False)
            obj.lugar = lugar
            obj.save()
            return redirect("detalle_lugar", lugar_id=lugar.id)

    return render(
        request,
        "objeto_lugar/crear_objeto_lugar.html",
        contexto,
    )


@login_required
def editar_objeto_lugar(request, objeto_lugar_id):
    objeto_lugar = get_object_or_404(ObjetoLugar, pk=objeto_lugar_id)
    cancel_url = reverse(
        "detalle_objeto_lugar",
        kwargs={"objeto_lugar_id": objeto_lugar.id},
    )

    if request.method == "GET":
        return render(
            request,
            "editar_generico.html",
            {
                "titulo": "Editar objeto del lugar",
                "form": EditarObjetoLugar(instance=objeto_lugar),
                "cancel_url": cancel_url,
            },
        )

    form = EditarObjetoLugar(request.POST, instance=objeto_lugar)
    if form.is_valid():
        form.save()
        return redirect("detalle_objeto_lugar", objeto_lugar_id=objeto_lugar.id)

    return render(
        request,
        "editar_generico.html",
        {
            "titulo": "Editar objeto del lugar",
            "form": form,
            "cancel_url": cancel_url,
        },
    )


@login_required
def borrar_objeto_lugar(request, objeto_lugar_id):
    obj = get_object_or_404(ObjetoLugar, pk=objeto_lugar_id)
    return _confirm_delete(
        request,
        obj,
        "detalle_lugar",
        {"lugar_id": obj.lugar_id},
        "lista_objetos_lugar",
    )
