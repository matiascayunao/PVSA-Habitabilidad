from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_GET

from .formularios.jefaturas import CrearJefeForm, EditarJefeForm
from .models import AsignacionLugarJefe


GRUPO_JEFES = "Jefe de departamento"


def _verificar_superadmin(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Solo el Superadmin puede administrar jefes.")


def _jefes_validos():
    # Nunca administrar un superusuario ni cuentas de roles mezclados.
    return (
        User.objects.filter(groups__name=GRUPO_JEFES, is_superuser=False)
        .exclude(groups__name__in=["Administrador", "Operador"])
        .distinct()
    )


@require_GET
@login_required
def lista_jefes(request):
    _verificar_superadmin(request)
    jefes = (
        _jefes_validos()
        .annotate(total_lugares=Count("lugares_asignados_como_jefe", distinct=True))
        .order_by("username")
    )
    return render(
        request,
        "superadmin/lista_jefes.html",
        {"jefes": jefes},
    )


@require_http_methods(["GET", "POST"])
@login_required
def crear_jefe(request):
    _verificar_superadmin(request)
    form = CrearJefeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            usuario = form.save()
            grupo = Group.objects.get(name=GRUPO_JEFES)
            usuario.groups.add(grupo)
            for lugar in form.cleaned_data["lugares"]:
                AsignacionLugarJefe.objects.create(
                    usuario=usuario,
                    lugar=lugar,
                    asignado_por=request.user,
                )
        messages.success(request, f"Jefe '{usuario.username}' creado correctamente.")
        return redirect("superadmin_lista_jefes")
    return render(
        request,
        "superadmin/form_jefe.html",
        {"form": form, "titulo": "Crear jefe de departamento", "es_edicion": False},
    )


@require_http_methods(["GET", "POST"])
@login_required
def editar_jefe(request, usuario_id):
    _verificar_superadmin(request)
    usuario = get_object_or_404(_jefes_validos(), pk=usuario_id)
    form = EditarJefeForm(request.POST or None, instance=usuario)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
            nuevos_ids = set(form.cleaned_data["lugares"].values_list("pk", flat=True))
            anteriores_ids = set(
                AsignacionLugarJefe.objects.filter(usuario=usuario)
                .values_list("lugar_id", flat=True)
            )
            quitar = anteriores_ids - nuevos_ids
            agregar = nuevos_ids - anteriores_ids
            if quitar:
                AsignacionLugarJefe.objects.filter(
                    usuario=usuario, lugar_id__in=quitar
                ).delete()
            for lugar_id in agregar:
                AsignacionLugarJefe.objects.create(
                    usuario=usuario,
                    lugar_id=lugar_id,
                    asignado_por=request.user,
                )
        messages.success(request, f"Asignaciones de '{usuario.username}' guardadas.")
        return redirect("superadmin_lista_jefes")
    return render(
        request,
        "superadmin/form_jefe.html",
        {
            "form": form,
            "titulo": "Editar jefe de departamento",
            "es_edicion": True,
            "jefe": usuario,
        },
    )