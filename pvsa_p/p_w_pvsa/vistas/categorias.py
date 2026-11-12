from ..servicios.estructura import guardar_sin_duplicados
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from ..forms import CrearTipoLugar
from ..forms import CrearCategoriaObjeto
from ..forms import CrearObjeto
from ..forms import CrearTipoObjeto
from ..forms import EditarTipoLugar
from ..forms import EditarCategoria
from ..forms import EditarObjeto
from ..forms import EditarTipoObjeto
from ..models import Lugar
from ..models import TipoLugar
from ..models import CategoriaObjeto
from ..models import Objeto
from ..models import TipoObjeto
from ..models import ObjetoLugar
from ..models import TipoLugarObjetoTipico
from .eliminacion import _confirm_delete


@login_required
def lista_tipos_lugar(request):
    tipos = TipoLugar.objects.all().order_by("tipo_de_lugar")
    return render(request, "tipo_lugar/tipos_lugar.html", {"tipos": tipos})


@login_required
def detalle_tipo_lugar(request, tipo_lugar_id):

    tipo = get_object_or_404(TipoLugar, pk=tipo_lugar_id)

    if request.method == "POST":
        nuevos_ids = []
        invalido = False
        for valor in request.POST.getlist("tipicos"):
            try:
                numero = int(valor)
                if not 0 < numero <= 9223372036854775807:
                    raise ValueError
            except (TypeError, ValueError):
                invalido = True
                break
            if numero not in nuevos_ids:
                nuevos_ids.append(numero)
        if not invalido:
            validos = set(TipoObjeto.objects.filter(pk__in=nuevos_ids).values_list("pk", flat=True))
            invalido = validos != set(nuevos_ids)
        if invalido:
            messages.error(request, "Selecciona únicamente variantes existentes. No se modificaron los objetos habituales.")
        else:
            with transaction.atomic():
                TipoLugarObjetoTipico.objects.filter(tipo_lugar=tipo).delete()
                TipoLugarObjetoTipico.objects.bulk_create([
                    TipoLugarObjetoTipico(
                        tipo_lugar=tipo, tipo_objeto_id=tipo_id,
                        activo=True, orden=indice,
                    )
                    for indice, tipo_id in enumerate(nuevos_ids)
                ])
            return redirect("detalle_tipo_lugar", tipo_lugar_id=tipo.id)

    lugares = Lugar.objects.filter(lugar_tipo_lugar=tipo).order_by("nombre_del_lugar")

    tipicos_qs = (
        TipoLugarObjetoTipico.objects.filter(tipo_lugar=tipo, activo=True)
        .select_related("tipo_objeto__objeto__objeto_categoria")
        .order_by(
            "orden",
            "tipo_objeto__objeto__objeto_categoria__nombre_de_categoria",
            "tipo_objeto__objeto__nombre_del_objeto",
            "tipo_objeto__marca",
            "tipo_objeto__material",
        )
    )
    tipicos_ids = list(tipicos_qs.values_list("tipo_objeto_id", flat=True))

    tipos_objeto = (
        TipoObjeto.objects.select_related("objeto__objeto_categoria")
        .all()
        .order_by(
            "objeto__objeto_categoria__nombre_de_categoria",
            "objeto__nombre_del_objeto",
            "marca",
            "material",
        )
    )

    return render(
        request,
        "tipo_lugar/detalle_tipo_lugar.html",
        {
            "tipo": tipo,
            "lugares": lugares,
            "tipicos": tipicos_qs,
            "tipicos_ids": tipicos_ids,
            "tipos_objeto": tipos_objeto,
        },
    )


@login_required
def crear_tipo_lugar(request):
    form = CrearTipoLugar(request.POST or None)

    contexto = {
        "form": form,
        "tipos_existentes": list(
            TipoLugar.objects
            .order_by("tipo_de_lugar")
            .values_list("tipo_de_lugar", flat=True)
        ),
    }

    if request.method == "POST" and form.is_valid():
        tipo = form.save()
        return redirect(
            "detalle_tipo_lugar",
            tipo_lugar_id=tipo.id,
        )

    return render(
        request,
        "tipo_lugar/crear_tipo_lugar.html",
        contexto,
    )


@login_required
def editar_tipo_lugar(request, tipo_lugar_id):
    tipo = get_object_or_404(TipoLugar, pk=tipo_lugar_id)
    cancel_url = reverse("detalle_tipo_lugar", kwargs={"tipo_lugar_id": tipo.id})

    if request.method == "GET":
        return render(
            request,
            "editar_generico.html",
            {
                "titulo": "Editar tipo de lugar",
                "form": EditarTipoLugar(instance=tipo),
                "cancel_url": cancel_url,
            },
        )

    form = EditarTipoLugar(request.POST, instance=tipo)
    if form.is_valid():
        form.save()
        return redirect("detalle_tipo_lugar", tipo_lugar_id=tipo.id)

    return render(
        request,
        "editar_generico.html",
        {
            "titulo": "Editar tipo de lugar",
            "form": form,
            "cancel_url": cancel_url,
        },
    )


@login_required
def borrar_tipo_lugar(request, tipo_lugar_id):
    tipo = get_object_or_404(TipoLugar, pk=tipo_lugar_id)
    return _confirm_delete(
        request,
        tipo,
        "detalle_tipo_lugar",
        {"tipo_lugar_id": tipo.id},
        "lista_tipos_lugar",
    )


@login_required
def lista_categorias(request):
    categorias = CategoriaObjeto.objects.all().order_by("nombre_de_categoria")
    return render(request, "categoria/categorias.html", {"categorias": categorias})


@login_required
def detalle_categoria(request, categoria_id):
    categoria = get_object_or_404(CategoriaObjeto, pk=categoria_id)
    objetos = Objeto.objects.filter(objeto_categoria_id=categoria_id).order_by("nombre_del_objeto")
    return render(
        request,
        "categoria/detalle_categoria.html",
        {"categoria": categoria, "objetos": objetos},
    )


@login_required
def crear_categoria_objeto(request):
    form = CrearCategoriaObjeto(request.POST or None)

    contexto = {
        "form": form,
        "categorias_existentes": list(
            CategoriaObjeto.objects
            .order_by("nombre_de_categoria")
            .values_list("nombre_de_categoria", flat=True)
        ),
    }

    if request.method == "POST" and form.is_valid():
        categoria = form.save()
        return redirect(
            "detalle_categoria",
            categoria_id=categoria.id,
        )

    return render(
        request,
        "categoria/crear_categoria_objeto.html",
        contexto,
    )


@login_required
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(CategoriaObjeto, pk=categoria_id)
    cancel_url = reverse("detalle_categoria", kwargs={"categoria_id": categoria.id})

    if request.method == "GET":
        return render(
            request,
            "editar_generico.html",
            {
                "titulo": "Editar categoría",
                "form": EditarCategoria(instance=categoria),
                "cancel_url": cancel_url,
            },
        )

    form = EditarCategoria(request.POST, instance=categoria)
    if form.is_valid():
        form.save()
        return redirect("detalle_categoria", categoria_id=categoria.id)

    return render(
        request,
        "editar_generico.html",
        {
            "titulo": "Editar categoría",
            "form": form,
            "cancel_url": cancel_url,
        },
    )


@login_required
def borrar_categoria(request, categoria_id):
    categoria = get_object_or_404(CategoriaObjeto, pk=categoria_id)
    return _confirm_delete(
        request,
        categoria,
        "detalle_categoria",
        {"categoria_id": categoria.id},
        "lista_categorias",
    )


@login_required
def lista_objetos(request):
    categoria_id = request.GET.get("categoria", "").strip()
    objetos_qs = Objeto.objects.select_related("objeto_categoria").all()
    if categoria_id:
        try:
            objetos_qs = objetos_qs.filter(objeto_categoria_id=int(categoria_id))
        except ValueError:
            categoria_id = ""

    objetos = objetos_qs.order_by(
        "objeto_categoria__nombre_de_categoria",
        "nombre_del_objeto",
    )
    categorias = CategoriaObjeto.objects.all().order_by("nombre_de_categoria")

    return render(
        request,
        "objeto/objetos.html",
        {
            "objetos": objetos,
            "categorias": categorias,
            "categoria_actual": categoria_id,
        },
    )


@login_required
def detalle_objeto(request, objeto_id):
    objeto = get_object_or_404(Objeto, pk=objeto_id)
    tipos = TipoObjeto.objects.filter(objeto=objeto).order_by("marca", "material")
    return render(
        request,
        "objeto/detalle_objeto.html",
        {"objeto": objeto, "tipos": tipos},
    )


@login_required
def crear_objeto(request):
    initial = {}
    categoria_preseleccionada = None

    categoria_id = request.GET.get("categoria", "").strip()

    if categoria_id:
        try:
            categoria_preseleccionada = CategoriaObjeto.objects.get(
                pk=int(categoria_id)
            )
            initial["objeto_categoria"] = categoria_preseleccionada
        except (ValueError, CategoriaObjeto.DoesNotExist):
            categoria_preseleccionada = None

    form = CrearObjeto(
        request.POST or None,
        initial=initial if request.method == "GET" else None,
    )

    contexto = {
        "form": form,
        "categoria_preseleccionada": categoria_preseleccionada,
        "objetos_existentes": list(
            Objeto.objects
            .select_related("objeto_categoria")
            .order_by("nombre_del_objeto")
            .values(
                "nombre_del_objeto",
                "objeto_categoria__nombre_de_categoria",
            )
        ),
    }

    if request.method == "POST" and form.is_valid():
        objeto = form.save()
        return redirect(
            "detalle_objeto",
            objeto_id=objeto.id,
        )

    return render(
        request,
        "objeto/crear_objeto.html",
        contexto,
    )


@login_required
def editar_objeto(request, objeto_id):
    objeto = get_object_or_404(Objeto, pk=objeto_id)
    cancel_url = reverse("detalle_objeto", kwargs={"objeto_id": objeto.id})

    if request.method == "GET":
        return render(
            request,
            "editar_generico.html",
            {
                "titulo": "Editar objeto",
                "form": EditarObjeto(instance=objeto),
                "cancel_url": cancel_url,
            },
        )

    form = EditarObjeto(request.POST, instance=objeto)
    if form.is_valid():
        form.save()
        return redirect("detalle_objeto", objeto_id=objeto.id)

    return render(
        request,
        "editar_generico.html",
        {
            "titulo": "Editar objeto",
            "form": form,
            "cancel_url": cancel_url,
        },
    )


@login_required
def borrar_objeto(request, objeto_id):
    objeto = get_object_or_404(Objeto, pk=objeto_id)
    return _confirm_delete(
        request,
        objeto,
        "detalle_objeto",
        {"objeto_id": objeto.id},
        "lista_objetos",
    )


@login_required
def lista_tipos_objeto(request):
    categoria_id = request.GET.get("categoria", "").strip()
    objeto_id = request.GET.get("objeto", "").strip()
    tipos_qs = TipoObjeto.objects.select_related(
        "objeto",
        "objeto__objeto_categoria",
    ).all()
    if categoria_id:
        try:
            c_id = int(categoria_id)
            tipos_qs = tipos_qs.filter(objeto__objeto_categoria_id=c_id)
        except ValueError:
            categoria_id = ""
    if objeto_id:
        try:
            o_id = int(objeto_id)
            tipos_qs = tipos_qs.filter(objeto_id=o_id)
        except ValueError:
            objeto_id = ""

    tipos_objeto = tipos_qs.order_by(
        "objeto__objeto_categoria__nombre_de_categoria",
        "objeto__nombre_del_objeto",
        "marca",
        "material",
    )
    categorias = CategoriaObjeto.objects.all().order_by("nombre_de_categoria")
    objetos = Objeto.objects.select_related("objeto_categoria").all().order_by(
        "objeto_categoria__nombre_de_categoria",
        "nombre_del_objeto",
    )

    return render(
        request,
        "tipo_objeto/tipos_objeto.html",
        {
            "tipos_objeto": tipos_objeto,
            "categorias": categorias,
            "objetos": objetos,
            "categoria_actual": categoria_id,
            "objeto_actual": objeto_id,
        },
    )


@login_required
def detalle_tipo_objeto(request, tipo_objeto_id):
    tipo = get_object_or_404(TipoObjeto, pk=tipo_objeto_id)
    usados = (
        ObjetoLugar.objects.filter(tipo_de_objeto=tipo)
        .select_related("lugar")
        .order_by("-fecha")
    )
    return render(
        request,
        "tipo_objeto/detalle_tipo_objeto.html",
        {"tipo": tipo, "usados": usados},
    )


@login_required
def crear_tipo_objeto(request):
    initial = {}
    objeto_preseleccionado = None

    objeto_id = request.GET.get("objeto", "").strip()

    if objeto_id:
        try:
            objeto_preseleccionado = (
                Objeto.objects
                .select_related("objeto_categoria")
                .get(pk=int(objeto_id))
            )
            initial["objeto"] = objeto_preseleccionado
        except (ValueError, Objeto.DoesNotExist):
            objeto_preseleccionado = None

    form = CrearTipoObjeto(
        request.POST or None,
        initial=initial if request.method == "GET" else None,
    )

    contexto = {
        "form": form,
        "objeto_preseleccionado": objeto_preseleccionado,
        "variantes_existentes": list(
            TipoObjeto.objects
            .select_related("objeto")
            .order_by(
                "objeto__nombre_del_objeto",
                "marca",
                "material",
            )
            .values(
                "objeto_id",
                "objeto__nombre_del_objeto",
                "marca",
                "material",
            )
        ),
    }

    if request.method == "POST" and form.is_valid():
        tipo = guardar_sin_duplicados(form)
        if tipo is not None:
            return redirect(
                "detalle_tipo_objeto",
                tipo_objeto_id=tipo.id,
            )

    return render(
        request,
        "tipo_objeto/crear_tipo_objeto.html",
        contexto,
    )


@login_required
def editar_tipo_objeto(request, tipo_objeto_id):
    tipo = get_object_or_404(TipoObjeto, pk=tipo_objeto_id)
    cancel_url = reverse("detalle_tipo_objeto", kwargs={"tipo_objeto_id": tipo.id})

    if request.method == "GET":
        return render(
            request,
            "editar_generico.html",
            {
                "titulo": "Editar tipo de objeto",
                "form": EditarTipoObjeto(instance=tipo),
                "cancel_url": cancel_url,
            },
        )

    form = EditarTipoObjeto(request.POST, instance=tipo)
    if form.is_valid():
        if guardar_sin_duplicados(form) is not None:
            return redirect("detalle_tipo_objeto", tipo_objeto_id=tipo.id)

    return render(
        request,
        "editar_generico.html",
        {
            "titulo": "Editar tipo de objeto",
            "form": form,
            "cancel_url": cancel_url,
        },
    )


@login_required
def borrar_tipo_objeto(request, tipo_objeto_id):
    tipo = get_object_or_404(TipoObjeto, pk=tipo_objeto_id)
    return _confirm_delete(
        request,
        tipo,
        "detalle_tipo_objeto",
        {"tipo_objeto_id": tipo.id},
        "lista_tipos_objeto",
    )
