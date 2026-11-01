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


def _clave_estructura(valor):
    """Compara nombres de una misma solicitud sin crear registros duplicados."""
    return " ".join((valor or "").split()).casefold()


def _validar_repetidos_estructura(formset):
    """Evita conflictos entre filas que cada formulario aislado no detecta."""
    objetos_nuevos = {}
    inventarios_por_variante = {}
    es_valido = True

    for indice, fila in enumerate(formset.forms, start=1):
        datos = fila.cleaned_data
        if not datos or datos.get("__empty__"):
            continue

        categoria_existente = datos.get("categoria_existente")
        categoria_nueva = _clave_estructura(datos.get("categoria_nueva"))
        objeto_existente = datos.get("objeto_existente")
        objeto_nuevo = _clave_estructura(datos.get("objeto_nuevo"))
        variante_existente = datos.get("tipo_objeto_existente")

        if objeto_existente and categoria_nueva:
            fila.add_error(
                "objeto_existente",
                "Un objeto existente debe conservar su categoría. "
                "Selecciona la categoría a la que pertenece.",
            )
            es_valido = False

        if variante_existente and objeto_nuevo:
            fila.add_error(
                "tipo_objeto_existente",
                "Una variante existente no puede asignarse a un objeto nuevo.",
            )
            es_valido = False

        if objeto_nuevo:
            categoria_id = (
                ("existente", categoria_existente.pk)
                if categoria_existente else ("nueva", categoria_nueva)
            )
            primera_categoria = objetos_nuevos.get(objeto_nuevo)
            if primera_categoria is not None and primera_categoria != categoria_id:
                fila.add_error(
                    "objeto_nuevo",
                    "Este objeto nuevo aparece en distintas categorías. "
                    "Un objeto debe pertenecer a una sola categoría.",
                )
                es_valido = False
            else:
                objetos_nuevos[objeto_nuevo] = categoria_id

        objeto_id = (
            ("existente", objeto_existente.pk)
            if objeto_existente else ("nuevo", objeto_nuevo)
        )
        variante_id = (
            ("existente", variante_existente.pk)
            if variante_existente else (
                "nueva",
                _clave_estructura(datos.get("marca")),
                _clave_estructura(datos.get("material")),
            )
        )
        combinacion = (objeto_id, variante_id)
        primera_fila = inventarios_por_variante.get(combinacion)
        if primera_fila is not None:
            fila.add_error(
                "tipo_objeto_existente",
                f"Esta misma variante ya está incluida en la fila {primera_fila}. "
                "Registra cada variante una sola vez por lugar.",
            )
            es_valido = False
        else:
            inventarios_por_variante[combinacion] = indice

    return es_valido


@login_required
@transaction.atomic
def crear_estructura(request):
    if request.method == "POST":
        form = EstructuraCompletaForm(request.POST)
        objetos_formset = ObjetoLugarFilaFormSet(
            request.POST,
            prefix="obj",
        )

        if (
            form.is_valid()
            and objetos_formset.is_valid()
            and _validar_repetidos_estructura(objetos_formset)
        ):
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


            # Se comparten los catálogos nuevos dentro de esta solicitud.
            # Así, repetir una categoría u objeto en distintas filas no
            # intenta crear un segundo registro con el mismo nombre único.
            categorias_creadas = {}
            objetos_creados = {}
            variantes_creadas = {}

            for fila in objetos_formset:
                if not fila.cleaned_data:
                    continue

                if fila.cleaned_data.get("__empty__"):
                    continue

                row = fila.cleaned_data

                categoria = row.get("categoria_existente")
                if not categoria:
                    nombre_categoria = (row.get("categoria_nueva") or "").strip()
                    clave_categoria = _clave_estructura(nombre_categoria)
                    categoria = categorias_creadas.get(clave_categoria)
                    if categoria is None:
                        categoria = CategoriaObjeto.objects.create(
                            nombre_de_categoria=nombre_categoria,
                        )
                        categorias_creadas[clave_categoria] = categoria

                objeto = row.get("objeto_existente")
                if not objeto:
                    nombre_objeto = (row.get("objeto_nuevo") or "").strip()
                    clave_objeto = _clave_estructura(nombre_objeto)
                    objeto = objetos_creados.get(clave_objeto)
                    if objeto is None:
                        objeto = Objeto.objects.create(
                            nombre_del_objeto=nombre_objeto,
                            objeto_categoria=categoria,
                        )
                        objetos_creados[clave_objeto] = objeto

                tipo_objeto = row.get("tipo_objeto_existente")
                if not tipo_objeto:
                    marca = (row.get("marca") or "").strip() or None
                    material = (row.get("material") or "").strip() or None
                    clave_variante = (
                        objeto.pk,
                        _clave_estructura(marca),
                        _clave_estructura(material),
                    )
                    tipo_objeto = variantes_creadas.get(clave_variante)
                    if tipo_objeto is None:
                        tipo_objeto = TipoObjeto.objects.create(
                            objeto=objeto,
                            marca=marca,
                            material=material,
                        )
                        variantes_creadas[clave_variante] = tipo_objeto

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
