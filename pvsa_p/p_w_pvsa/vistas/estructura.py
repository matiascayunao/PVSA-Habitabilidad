from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect
from django.shortcuts import render
from ..forms import EstructuraCompletaForm
from ..forms import ObjetoLugarFilaFormSet
from ..models import Sector
from ..models import Ubicacion
from ..models import Piso
from ..models import Lugar
from ..models import TipoLugar
from ..models import CategoriaObjeto
from ..models import Objeto
from ..models import TipoObjeto
from ..models import ObjetoLugar


@login_required
@transaction.atomic
def crear_estructura(request):
    if request.method == "POST":
        form = EstructuraCompletaForm(request.POST)
        objetos_formset = ObjetoLugarFilaFormSet(
            request.POST,
            prefix="obj",
        )

        if form.is_valid() and objetos_formset.is_valid():
            cd = form.cleaned_data

            sector = cd.get("sector_existente")
            if not sector:
                sector = Sector.objects.create(
                    sector=(cd.get("sector_nuevo") or "").strip()
                )

            ubicacion = cd.get("ubicacion_existente")
            if not ubicacion:
                ubicacion = Ubicacion.objects.create(
                    ubicacion=(cd.get("ubicacion_nueva") or "").strip(),
                    sector=sector,
                )

            piso = cd.get("piso_existente")
            if not piso:
                piso = Piso.objects.create(
                    piso=cd.get("piso_nuevo"),
                    ubicacion=ubicacion,
                )

            tipo_lugar = cd.get("tipo_lugar_existente")
            if not tipo_lugar:
                tipo_lugar = TipoLugar.objects.create(
                    tipo_de_lugar=(
                        cd.get("tipo_lugar_nuevo") or ""
                    ).strip()
                )

            lugar = cd.get("lugar_existente")

            if not lugar:
                lugar = Lugar.objects.create(
                    nombre_del_lugar=(
                        cd.get("lugar_nuevo") or ""
                    ).strip(),
                    piso=piso,
                    lugar_tipo_lugar=tipo_lugar,
                    es_area_comun=cd.get(
                        "lugar_es_area_comun",
                        False,
                    ),
                )


            for fila in objetos_formset:
                if not fila.cleaned_data:
                    continue

                if fila.cleaned_data.get("__empty__"):
                    continue

                row = fila.cleaned_data

                categoria = row.get("categoria_existente")
                if not categoria:
                    categoria = CategoriaObjeto.objects.create(
                        nombre_de_categoria=(
                            row.get("categoria_nueva") or ""
                        ).strip()
                    )

                objeto = row.get("objeto_existente")
                if not objeto:
                    objeto = Objeto.objects.create(
                        nombre_del_objeto=(
                            row.get("objeto_nuevo") or ""
                        ).strip(),
                        objeto_categoria=categoria,
                    )

                tipo_objeto = row.get("tipo_objeto_existente")
                if not tipo_objeto:
                    marca = (row.get("marca") or "").strip() or None
                    material = (row.get("material") or "").strip() or None

                    tipo_objeto = TipoObjeto.objects.create(
                        objeto=objeto,
                        marca=marca,
                        material=material,
                    )

                ObjetoLugar.objects.create(
                    lugar=lugar,
                    tipo_de_objeto=tipo_objeto,
                    cantidad=row.get("cantidad"),
                    detalle=(row.get("detalle") or "").strip(),
                    importancia=row.get("importancia") or 1,
                    cantidad_mala=row.get("cantidad_mala") or 0,
                    cantidad_pendiente=(
                        row.get("cantidad_pendiente") or 0
                    ),
                    minimo_operativo=(
                        row.get("minimo_operativo") or 1
                    ),
                )

            return redirect(
                "detalle_lugar",
                lugar_id=lugar.id,
            )
    else:
        form = EstructuraCompletaForm()
        objetos_formset = ObjetoLugarFilaFormSet(
            prefix="obj"
        )

    contexto = {
        "form": form,
        "objetos_formset": objetos_formset,
        "sectores_existentes": list(
            Sector.objects
            .order_by("sector")
            .values_list("sector", flat=True)
        ),
        "ubicaciones_existentes": list(
            Ubicacion.objects
            .select_related("sector")
            .order_by("ubicacion")
            .values(
                "ubicacion",
                "sector__sector",
            )
        ),
        "pisos_existentes": list(
            Piso.objects
            .select_related("ubicacion")
            .order_by(
                "ubicacion__ubicacion",
                "piso",
            )
            .values(
                "piso",
                "ubicacion_id",
            )
        ),
        "tipos_lugar_existentes": list(
            TipoLugar.objects
            .order_by("tipo_de_lugar")
            .values_list("tipo_de_lugar", flat=True)
        ),
        "lugares_existentes": list(
            Lugar.objects
            .select_related(
                "piso",
                "piso__ubicacion",
                "piso__ubicacion__sector",
            )
            .order_by("nombre_del_lugar")
            .values(
                "nombre_del_lugar",
                "piso_id",
            )
        ),
        "categorias_existentes": list(
            CategoriaObjeto.objects
            .order_by("nombre_de_categoria")
            .values_list("nombre_de_categoria", flat=True)
        ),
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

    return render(
        request,
        "crear_estructura.html",
        contexto,
    )
