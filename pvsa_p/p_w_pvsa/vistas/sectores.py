from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from ..forms import CrearSector
from ..forms import EditarSector
from ..models import Sector
from ..models import Ubicacion
from .eliminacion import _confirm_delete


@login_required
def lista_sectores(request):
    sectores = Sector.objects.all().order_by("sector")
    return render(request, "sector/sectores.html", {"sectores": sectores})


@login_required
def detalle_sector(request, sector_id):
    sector = get_object_or_404(Sector, pk=sector_id)
    ubicaciones = Ubicacion.objects.filter(sector=sector).order_by("ubicacion")
    return render(
        request,
        "sector/detalle_sector.html",
        {"sector": sector, "ubicaciones": ubicaciones},
    )


@login_required
def crear_sector(request):
    form = CrearSector(request.POST or None)

    contexto = {
        "form": form,
        "sectores_existentes": list(
            Sector.objects.order_by("sector").values_list("sector", flat=True)
        ),
    }

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("lista_sectores")

    return render(
        request,
        "sector/crear_sector.html",
        contexto,
    )


@login_required
def editar_sector(request, sector_id):
    sector = get_object_or_404(Sector, pk=sector_id)
    if request.method == "GET":
        return render(
            request,
            "sector/editar_sector.html",
            {"form": EditarSector(instance=sector), "sector": sector},
        )

    form = EditarSector(request.POST, instance=sector)
    if form.is_valid():
        form.save()
        return redirect("detalle_sector", sector_id=sector.id)
    return render(
        request,
        "sector/editar_sector.html",
        {"form": form, "sector": sector},
    )


@login_required
def borrar_sector(request, sector_id):
    sector = get_object_or_404(Sector, pk=sector_id)
    return _confirm_delete(
        request, sector, "detalle_sector", {"sector_id": sector.id}, "lista_sectores"
    )
