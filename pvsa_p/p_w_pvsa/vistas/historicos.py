import unicodedata

from django.core.paginator import Paginator
from ..servicios.identificadores import entero_identificador
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from ..forms import CrearHistorico
from ..forms import EditarHistorico
from ..models import Lugar
from ..models import ObjetoLugar
from ..models import HistoricoObjeto
from .eliminacion import _confirm_delete


@login_required
def lista_historicos(request):
    lugar_id = request.GET.get("lugar", "").strip()
    objeto_id = request.GET.get("objeto", "").strip()
    tipo_id = request.GET.get("tipo", "").strip()
    estado_val = request.GET.get("estado", "").strip()

    qs = HistoricoObjeto.objects.select_related(
        "objeto_del_lugar",
        "objeto_del_lugar__lugar",
        "objeto_del_lugar__lugar__piso",
        "objeto_del_lugar__lugar__piso__ubicacion",
        "objeto_del_lugar__lugar__piso__ubicacion__sector",
        "objeto_del_lugar__tipo_de_objeto",
        "objeto_del_lugar__tipo_de_objeto__objeto",
        "objeto_del_lugar__tipo_de_objeto__objeto__objeto_categoria",
    ).all()
    if lugar_id:
        try:
            qs = qs.filter(objeto_del_lugar__lugar_id=entero_identificador(lugar_id))
        except ValueError:
            lugar_id = ""

    if objeto_id:
        try:
            qs = qs.filter(variante_anterior__objeto_id=entero_identificador(objeto_id))
        except ValueError:
            objeto_id = ""

    if tipo_id:
        try:
            qs = qs.filter(variante_anterior__variante_id=entero_identificador(tipo_id))
        except ValueError:
            tipo_id = ""

    if estado_val:
        qs = qs.filter(estado_anterior=estado_val)

    historicos = qs.order_by(
        "-fecha_anterior",
        "objeto_del_lugar__lugar__piso__ubicacion__ubicacion",
        "objeto_del_lugar__lugar__piso__piso",
        "objeto_del_lugar__lugar__nombre_del_lugar",
    )
    consulta = request.GET.get("q", "").strip()
    orden = request.GET.get("orden", "reciente")
    if orden not in {"reciente", "antiguo", "objeto", "lugar"}:
        orden = "reciente"

    def normalizar(texto):
        return "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower())
                       if not "\u0300" <= c <= "\u036f").strip()

    def coincide(historico):
        lugar = historico.objeto_del_lugar.lugar
        datos = historico.variante_anterior or {}
        texto = " ".join([historico.identidad_variante, datos.get("marca") or "",
                          datos.get("material") or "", lugar.nombre_del_lugar if lugar else "",
                          lugar.piso.ubicacion.ubicacion if lugar else "",
                          lugar.piso.ubicacion.sector.sector if lugar else ""])
        return not consulta or normalizar(consulta) in normalizar(texto)

    def clave(historico):
        if orden == "objeto":
            valor = normalizar(historico.identidad_variante)
        elif orden == "lugar":
            valor = normalizar(historico.objeto_del_lugar.lugar.nombre_del_lugar
                               if historico.objeto_del_lugar.lugar else "")
        else:
            valor = historico.fecha_anterior.toordinal() * (1 if orden == "antiguo" else -1)
        return valor, historico.pk

    historicos = sorted(filter(coincide, historicos), key=clave)
    paginator = Paginator(historicos, 50)
    pagina = paginator.get_page(request.GET.get("pagina"))
    lugares = (
        Lugar.objects.select_related(
            "piso",
            "piso__ubicacion",
            "piso__ubicacion__sector",
        )
        .all()
        .order_by(
            "piso__ubicacion__ubicacion",
            "piso__piso",
            "nombre_del_lugar",
        )
    )

    objetos = {}
    tipos = {}
    for historico in HistoricoObjeto.objects.exclude(variante_anterior=None).order_by("pk"):
        datos = historico.variante_anterior
        if datos.get("variante_id") is None:
            continue
        etiqueta_objeto = f"{datos['objeto']} · {datos['categoria']}"
        objetos[datos["objeto_id"]] = {
            "id": datos["objeto_id"], "etiqueta": etiqueta_objeto,
        }
        tipos[datos["variante_id"]] = {
            "id": datos["variante_id"], "etiqueta": historico.identidad_variante,
        }
    objetos = sorted(objetos.values(), key=lambda dato: dato["etiqueta"].casefold())
    tipos = sorted(tipos.values(), key=lambda dato: dato["etiqueta"].casefold())
    estados = HistoricoObjeto._meta.get_field("estado_anterior").choices

    return render(
        request,
        "historico/historicos.html",
        {
            "historicos": pagina,
            "pagina": pagina,
            "paginator": paginator,
            "paginas": paginator.get_elided_page_range(pagina.number, on_each_side=1, on_ends=1),
            "consulta": consulta, "orden": orden,
            "filtros_listado": [(k, request.GET[k]) for k in (
                "lugar", "objeto", "tipo", "estado",
            ) if request.GET.get(k)],
            "lugares": lugares,
            "objetos_catalogo": objetos,
            "tipos": tipos,
            "estados": estados,
            "lugar_actual": lugar_id,
            "objeto_actual": objeto_id,
            "tipo_actual": tipo_id,
            "estado_actual": estado_val,
        },
    )


@login_required
def detalle_historico(request, historico_id):
    historico = get_object_or_404(HistoricoObjeto, pk=historico_id)
    return render(request, "historico/detalle_historico.html", {"historico": historico})


@login_required
def crear_historico(request, objeto_lugar_id):
    objeto_lugar = get_object_or_404(ObjetoLugar, pk=objeto_lugar_id)

    if request.method == "GET":
        form = CrearHistorico(
            initial={
                "objeto_del_lugar": objeto_lugar.id,
                "cantidad_anterior": objeto_lugar.cantidad,
                "cantidad_mala_anterior": objeto_lugar.cantidad_mala,
                "cantidad_pendiente_anterior": objeto_lugar.cantidad_pendiente,
                "minimo_operativo_anterior": objeto_lugar.minimo_operativo,
                "importancia_anterior": objeto_lugar.importancia,
                "estado_anterior": objeto_lugar.estado,
                "detalle_anterior": objeto_lugar.detalle,
                "fecha_anterior": objeto_lugar.fecha,
            }
        )

        return render(
            request,
            "historico/crear_historico.html",
            {
                "form": form,
                "objeto_lugar": objeto_lugar,
            },
        )

    form = CrearHistorico(
        request.POST,
        instance=HistoricoObjeto(objeto_del_lugar=objeto_lugar),
    )

    if form.is_valid():
        h = form.save(commit=False)
        h.objeto_del_lugar = objeto_lugar
        h.save()

        return redirect("detalle_objeto_lugar", objeto_lugar_id=objeto_lugar.id)

    return render(
        request,
        "historico/crear_historico.html",
        {
            "form": form,
            "objeto_lugar": objeto_lugar,
        },
    )


@login_required
def editar_historico(request, historico_id):
    historico = get_object_or_404(HistoricoObjeto, pk=historico_id)
    cancel_url = reverse("detalle_historico", kwargs={"historico_id": historico.id})

    if request.method == "GET":
        return render(
            request,
            "editar_generico.html",
            {
                "titulo": "Editar histórico",
                "form": EditarHistorico(instance=historico),
                "cancel_url": cancel_url,
            },
        )

    form = EditarHistorico(request.POST, instance=historico)
    if form.is_valid():
        form.save()
        return redirect("detalle_historico", historico_id=historico.id)

    return render(
        request,
        "editar_generico.html",
        {
            "titulo": "Editar histórico",
            "form": form,
            "cancel_url": cancel_url,
        },
    )


@login_required
def borrar_historico(request, historico_id):
    historico = get_object_or_404(HistoricoObjeto, pk=historico_id)
    return _confirm_delete(
        request,
        historico,
        "detalle_historico",
        {"historico_id": historico.id},
        "lista_historicos",
    )
