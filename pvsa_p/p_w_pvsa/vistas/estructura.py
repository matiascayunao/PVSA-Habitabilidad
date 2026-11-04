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
from ..models import ObjetoLugar
from ..servicios.estructura import _clave_estructura, crear_estructura_con_inventario




def _validar_repetidos_estructura(formset, lugar_existente=None):
    """Evita duplicados en el envío y en el inventario ya registrado."""
    variantes_en_lugar = set()
    if lugar_existente is not None:
        variantes_en_lugar = set(
            ObjetoLugar.objects.filter(lugar=lugar_existente)
            .exclude(tipo_de_objeto__isnull=True)
            .values_list("tipo_de_objeto_id", flat=True)
        )
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

        if variante_existente and variante_existente.pk in variantes_en_lugar:
            fila.add_error(
                "tipo_objeto_existente",
                "Esta variante ya está registrada en el lugar seleccionado. "
                "Edita el inventario existente en lugar de duplicarlo.",
            )
            es_valido = False

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
            and _validar_repetidos_estructura(
                objetos_formset, form.cleaned_data.get("lugar_existente")
            )
        ):
            lugar = crear_estructura_con_inventario(
                form.cleaned_data,
                (fila.cleaned_data for fila in objetos_formset),
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