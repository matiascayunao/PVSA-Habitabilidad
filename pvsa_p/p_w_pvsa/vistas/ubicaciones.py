from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from ..forms import CrearUbicacion
from ..forms import EditarUbicacion
from ..models import Sector
from ..models import Ubicacion
from ..models import Piso
from .eliminacion import _confirm_delete


@login_required
def lista_ubicaciones(request):
    sector_id = request.GET.get("sector", "").strip()
    ubicaciones_qs = Ubicacion.objects.select_related("sector").all()

    if sector_id:
        try:
            ubicaciones_qs = ubicaciones_qs.filter(sector_id=int(sector_id))
        except ValueError:
            sector_id = ""

    ubicaciones = ubicaciones_qs.order_by("ubicacion")
    sectores = Sector.objects.all().order_by("sector")

    return render(
        request,
        "ubicacion/ubicaciones.html",
        {
            "ubicaciones": ubicaciones,
            "sectores": sectores,
            "sector_actual": sector_id,
        },
    )


@login_required
def detalle_ubicacion(request, ubicacion_id):
    ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
    pisos = Piso.objects.filter(ubicacion=ubicacion).order_by("piso")
    return render(
        request,
        "ubicacion/detalle_ubicacion.html",
        {"ubicacion": ubicacion, "pisos": pisos},
    )


@login_required
def crear_ubicacion(request):
    initial = {}
    sector_preseleccionado = None

    sector_id = request.GET.get("sector", "").strip()

    if sector_id:
        try:
            sector_preseleccionado = Sector.objects.get(pk=int(sector_id))
            initial["sector"] = sector_preseleccionado
        except (ValueError, Sector.DoesNotExist):
            sector_preseleccionado = None

    form = CrearUbicacion(
        request.POST or None,
        initial=initial if request.method == "GET" else None,
    )

    contexto = {
        "form": form,
        "sector_preseleccionado": sector_preseleccionado,
        "ubicaciones_existentes": list(
            Ubicacion.objects
            .select_related("sector")
            .order_by("ubicacion")
            .values(
                "ubicacion",
                "sector__sector",
            )
        ),
    }

    if request.method == "POST" and form.is_valid():
        ubicacion = form.save()
        return redirect(
            "detalle_sector",
            sector_id=ubicacion.sector_id,
        )

    return render(
        request,
        "ubicacion/crear_ubicacion.html",
        contexto,
    )


@login_required
def editar_ubicacion(request, ubicacion_id):
    ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
    if request.method == "GET":
        return render(
            request,
            "ubicacion/editar_ubicacion.html",
            {"form": EditarUbicacion(instance=ubicacion), "ubicacion": ubicacion},
        )

    form = EditarUbicacion(request.POST, instance=ubicacion)
    if form.is_valid():
        form.save()
        return redirect("detalle_ubicacion", ubicacion_id=ubicacion.id)
    return render(
        request,
        "ubicacion/editar_ubicacion.html",
        {"form": form, "ubicacion": ubicacion},
    )


@login_required
def borrar_ubicacion(request, ubicacion_id):
    ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
    return _confirm_delete(
        request,
        ubicacion,
        "detalle_ubicacion",
        {"ubicacion_id": ubicacion.id},
        "lista_ubicaciones",
    )
