"""Edición limitada del inventario por jefes de departamento.

Nunca reutiliza rutas globales; comprueba pertenencia en cada GET y POST.
El histórico de ObjetoLugar.save() permanece activo y esta capa agrega actor,
fecha y snapshots de auditoría en la misma transacción.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CrearObjetoLugar, EditarObjetoLugar
from .models import AuditoriaInventarioJefe, ObjetoLugar
from .pvsa_permisos import es_jefe_departamento, lugares_propios_jefe


CAMPOS_INVENTARIO = (
    "tipo_de_objeto_id",
    "cantidad",
    "detalle",
    "importancia",
    "cantidad_mala",
    "cantidad_pendiente",
    "minimo_operativo",
)


def _exigir_jefe(usuario):
    if not es_jefe_departamento(usuario):
        raise PermissionDenied("Esta función está reservada a jefes de departamento.")


def _fotografia_registro(objeto):
    """Datos concretos, serializables, sin referencias a objetos Django."""
    return {
        "lugar_id": objeto.lugar_id,
        "tipo_de_objeto_id": objeto.tipo_de_objeto_id,
        "cantidad": objeto.cantidad,
        "detalle": objeto.detalle or "",
        "importancia": objeto.importancia,
        "cantidad_mala": objeto.cantidad_mala,
        "cantidad_pendiente": objeto.cantidad_pendiente,
        "minimo_operativo": objeto.minimo_operativo,
        "estado": objeto.estado,
    }


def _auditar(usuario, accion, objeto, antes, despues):
    AuditoriaInventarioJefe.objects.create(
        accion=accion,
        usuario=usuario,
        usuario_nombre=usuario.get_username(),
        lugar_id_registrado=objeto.lugar_id,
        objeto_lugar_id_registrado=objeto.pk,
        datos_antes=antes,
        datos_despues=despues,
    )


@login_required
@require_http_methods(["GET", "POST"])
def crear_objeto_jefe(request, lugar_id):
    _exigir_jefe(request.user)
    # En POST se vuelve a consultar la asignación: nunca confiar en el HTML.
    if request.method == "POST":
        with transaction.atomic():
            lugar = get_object_or_404(
                lugares_propios_jefe(request.user).select_for_update(),
                pk=lugar_id,
            )
            form = CrearObjetoLugar(request.POST)
            form.instance.lugar = lugar
            form.fields["tipo_de_objeto"].required = True
            if form.is_valid():
                objeto = form.save(commit=False)
                # El lugar proviene exclusivamente de la URL verificada.
                objeto.lugar = lugar
                objeto.save()  # Valida cantidades y calcula estado.
                _auditar(
                    request.user,
                    AuditoriaInventarioJefe.Accion.CREAR,
                    objeto,
                    {},
                    _fotografia_registro(objeto),
                )
                messages.success(request, "Objeto registrado correctamente.")
                return redirect("detalle_lugar_jefe", lugar_id=lugar.pk)
    else:
        lugar = get_object_or_404(lugares_propios_jefe(request.user), pk=lugar_id)
        form = CrearObjetoLugar()
        form.fields["tipo_de_objeto"].required = True

    return render(
        request,
        "jefe/form_objeto.html",
        {"titulo": "Agregar objeto", "lugar": lugar, "form": form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def editar_objeto_jefe(request, objeto_lugar_id):
    _exigir_jefe(request.user)
    # Filtrado por lugar asignado y NO común. El ID de otro objeto da 404.
    base = ObjetoLugar.objects.filter(
        lugar__in=lugares_propios_jefe(request.user)
    )

    if request.method == "POST":
        with transaction.atomic():
            objeto = get_object_or_404(
                base.select_for_update(), pk=objeto_lugar_id
            )
            antes = _fotografia_registro(objeto)
            form = EditarObjetoLugar(request.POST, instance=objeto)
            form.fields["tipo_de_objeto"].required = True
            if form.is_valid():
                actualizado = form.save(commit=False)
                # No se expone lugar en el formulario, y no se permite moverlo.
                actualizado.lugar_id = antes["lugar_id"]
                if all(
                    getattr(actualizado, campo) == antes[campo]
                    for campo in CAMPOS_INVENTARIO
                ):
                    messages.info(request, "No había cambios que guardar.")
                else:
                    actualizado.save()  # Conserva el histórico automático.
                    _auditar(
                        request.user,
                        AuditoriaInventarioJefe.Accion.EDITAR,
                        actualizado,
                        antes,
                        _fotografia_registro(actualizado),
                    )
                    messages.success(request, "Objeto actualizado correctamente.")
                return redirect(
                    "detalle_lugar_jefe", lugar_id=actualizado.lugar_id
                )
    else:
        objeto = get_object_or_404(base, pk=objeto_lugar_id)
        form = EditarObjetoLugar(instance=objeto)
        form.fields["tipo_de_objeto"].required = True

    return render(
        request,
        "jefe/form_objeto.html",
        {
            "titulo": "Editar objeto",
            "lugar": objeto.lugar,
            "form": form,
        },
    )
