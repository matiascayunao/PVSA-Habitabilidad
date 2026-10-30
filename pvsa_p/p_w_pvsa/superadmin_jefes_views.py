"""Gestión de cuentas de Jefes de departamento: solo Superadmin.

Los lugares comunes no se asignan aquí: cada jefe los consulta
indirectamente por las ubicaciones de sus lugares propios.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_GET

from .models import AsignacionLugarJefe, Lugar


GRUPO_JEFES = "Jefe de departamento"


def _verificar_superadmin(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Solo el Superadmin puede administrar jefes.")


def _lugares_asignables():
    return (
        Lugar.objects.filter(es_area_comun=False)
        .select_related("piso", "piso__ubicacion", "piso__ubicacion__sector")
        .order_by(
            "piso__ubicacion__sector__sector",
            "piso__ubicacion__ubicacion",
            "piso__piso",
            "nombre_del_lugar",
        )
    )


class _CamposDeLugares(forms.Form):
    lugares = forms.ModelMultipleChoiceField(
        label="Lugares propios del departamento",
        queryset=Lugar.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=(
            "Marca solo oficinas, salas y otros espacios propios. "
            "Las áreas comunes de esas ubicaciones se consultarán automáticamente."
        ),
    )

    def preparar_lugares(self, usuario=None):
        self.fields["lugares"].queryset = _lugares_asignables()
        self.fields["lugares"].label_from_instance = (
            lambda lugar: (
                f"{lugar.piso.ubicacion.sector.sector} / "
                f"{lugar.piso.ubicacion.ubicacion} / "
                f"Piso {lugar.piso.piso} / "
                f"{lugar.nombre_del_lugar}"
            )
        )
        if usuario is not None and not self.is_bound:
            self.fields["lugares"].initial = list(
                AsignacionLugarJefe.objects.filter(usuario=usuario)
                .values_list("lugar_id", flat=True)
            )


def _dar_estilo(form):
    for nombre, campo in form.fields.items():
        if nombre == "lugares" or isinstance(campo.widget, forms.CheckboxInput):
            continue
        campo.widget.attrs["class"] = "form-control"


class CrearJefeForm(UserCreationForm, _CamposDeLugares):
    first_name = forms.CharField(label="Nombre", max_length=150, required=False)
    last_name = forms.CharField(label="Apellidos", max_length=150, required=False)
    email = forms.EmailField(label="Correo", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.preparar_lugares()
        _dar_estilo(self)


class EditarJefeForm(forms.ModelForm, _CamposDeLugares):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "is_active")
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "email": "Correo",
            "is_active": "Cuenta activa",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.preparar_lugares(self.instance)
        _dar_estilo(self)


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
