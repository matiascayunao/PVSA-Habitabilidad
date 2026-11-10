from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from ..forms import CrearHistorico
from ..forms import EditarHistorico
from ..models import Lugar
from ..models import Objeto
from ..models import TipoObjeto
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
            qs = qs.filter(objeto_del_lugar__lugar_id=int(lugar_id))
        except ValueError:
            lugar_id = ""

    if objeto_id:
        try:
            qs = qs.filter(objeto_del_lugar__tipo_de_objeto__objeto_id=int(objeto_id))
        except ValueError:
            objeto_id = ""

    if tipo_id:
        try:
            qs = qs.filter(objeto_del_lugar__tipo_de_objeto_id=int(tipo_id))
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
    estados = HistoricoObjeto._meta.get_field("estado_anterior").choices

    return render(
        request,
        "historico/historicos.html",
        {
            "historicos": historicos,
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
