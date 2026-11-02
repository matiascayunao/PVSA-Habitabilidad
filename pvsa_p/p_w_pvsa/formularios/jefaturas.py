"""Formularios para crear y editar jefes de departamento.

Los lugares comunes no se asignan directamente a los jefes:
se consultan a partir de las ubicaciones de sus lugares propios.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from ..models import AsignacionLugarJefe, Lugar


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