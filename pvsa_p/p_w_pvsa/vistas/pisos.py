from ..servicios.estructura import guardar_sin_duplicados
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from ..forms import CrearPiso
from ..forms import EditarPiso
from ..models import Ubicacion
from ..models import Piso
from ..models import Lugar
from .eliminacion import _confirm_delete


@login_required
def lista_pisos(request):
    ubicacion_id = request.GET.get("ubicacion", "").strip()
    pisos_qs = Piso.objects.select_related("ubicacion", "ubicacion__sector").all()
    if ubicacion_id:
        try:
            pisos_qs = pisos_qs.filter(ubicacion_id=int(ubicacion_id))
        except ValueError:
            ubicacion_id = ""

    pisos = pisos_qs.order_by("ubicacion__ubicacion", "piso")
    ubicaciones = Ubicacion.objects.select_related("sector").all().order_by("ubicacion")

    return render(
        request,
        "piso/pisos.html",
        {
            "pisos": pisos,
            "ubicaciones": ubicaciones,
            "ubicacion_actual": ubicacion_id,
        },
    )


@login_required
def detalle_piso(request, piso_id):
    piso = get_object_or_404(Piso, pk=piso_id)
    lugares = Lugar.objects.filter(piso=piso).order_by("nombre_del_lugar")
    return render(
        request,
        "piso/detalle_piso.html",
        {"piso": piso, "lugares": lugares},
    )


@login_required
def crear_piso(request):
    initial = {}
    ubicacion_preseleccionada = None

    ubicacion_id = request.GET.get("ubicacion", "").strip()

    if ubicacion_id:
        try:
            ubicacion_preseleccionada = (
                Ubicacion.objects
                .select_related("sector")
                .get(pk=int(ubicacion_id))
            )
            initial["ubicacion"] = ubicacion_preseleccionada
        except (ValueError, Ubicacion.DoesNotExist):
            ubicacion_preseleccionada = None

    form = CrearPiso(
        request.POST or None,
        initial=initial if request.method == "GET" else None,
    )

    contexto = {
        "form": form,
        "ubicacion_preseleccionada": ubicacion_preseleccionada,
        "pisos_existentes": list(
            Piso.objects
            .select_related("ubicacion")
            .order_by("ubicacion__ubicacion", "piso")
            .values(
                "piso",
                "ubicacion_id",
            )
        ),
    }

    if request.method == "POST" and form.is_valid():
        piso = guardar_sin_duplicados(form)
        if piso is not None:
            return redirect(
                "detalle_ubicacion",
                ubicacion_id=piso.ubicacion_id,
            )

    return render(
        request,
        "piso/crear_piso.html",
        contexto,
    )


@login_required
def editar_piso(request, piso_id):
    piso = get_object_or_404(Piso, pk=piso_id)
    cancel_url = reverse("detalle_piso", kwargs={"piso_id": piso.id})

    if request.method == "GET":
        return render(
            request,
            "editar_generico.html",
            {
                "titulo": "Editar piso",
                "form": EditarPiso(instance=piso),
                "cancel_url": cancel_url,
            },
        )

    form = EditarPiso(request.POST, instance=piso)
    if form.is_valid():
        if guardar_sin_duplicados(form) is not None:
            return redirect("detalle_piso", piso_id=piso.id)

    return render(
        request,
        "editar_generico.html",
        {
            "titulo": "Editar piso",
            "form": form,
            "cancel_url": cancel_url,
        },
    )


@login_required
def borrar_piso(request, piso_id):
    piso = get_object_or_404(Piso, pk=piso_id)
    return _confirm_delete(
        request, piso, "detalle_piso", {"piso_id": piso.id}, "lista_pisos"
    )
