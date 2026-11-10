from django import forms
from django.forms import ModelForm
from ..models import ObjetoLugar, HistoricoObjeto


class CrearObjetoLugar(forms.ModelForm):
    class Meta:
        model = ObjetoLugar
        fields = [
            "tipo_de_objeto",
            "cantidad",
            "detalle",
            "importancia",
            "cantidad_mala",
            "cantidad_pendiente",
            "minimo_operativo",
        ]

        widgets = {
            "tipo_de_objeto": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "detalle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Detalle u observación opcional",
                }
            ),
            "importancia": forms.Select(attrs={"class": "form-select"}),
            "cantidad_mala": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "cantidad_pendiente": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "minimo_operativo": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }

        labels = {
            "tipo_de_objeto": "Tipo de objeto",
            "cantidad": "Cantidad total",
            "detalle": "Detalle",
            "importancia": "Importancia",
            "cantidad_mala": "Unidades malas",
            "cantidad_pendiente": "Unidades pendientes",
            "minimo_operativo": "Mínimo operativo",
        }

        help_texts = {
            "cantidad": "Cantidad total de unidades existentes.",
            "cantidad_mala": "Cantidad de unidades que no están funcionando.",
            "cantidad_pendiente": "Cantidad de unidades pendientes de revisión.",
            "minimo_operativo": "Cantidad mínima que debe estar funcionando para considerar aceptable este objeto.",
            "importancia": "Nivel de peso del objeto dentro del lugar.",
        }

    def clean(self):
        cleaned = super().clean()

        cantidad = cleaned.get("cantidad") or 0
        cantidad_mala = cleaned.get("cantidad_mala") or 0
        cantidad_pendiente = cleaned.get("cantidad_pendiente") or 0
        minimo_operativo = cleaned.get("minimo_operativo")
        if minimo_operativo is None:
            minimo_operativo = 1

        if cantidad <= 0:
            raise forms.ValidationError("La cantidad total debe ser mayor a 0.")

        if cantidad_mala < 0:
            raise forms.ValidationError("Las unidades malas no pueden ser negativas.")

        if cantidad_pendiente < 0:
            raise forms.ValidationError("Las unidades pendientes no pueden ser negativas.")

        if cantidad_mala + cantidad_pendiente > cantidad:
            raise forms.ValidationError(
                "La suma de unidades malas y pendientes no puede superar la cantidad total."
            )

        if minimo_operativo <= 0:
            raise forms.ValidationError("El mínimo operativo debe ser mayor a 0.")

        if minimo_operativo > cantidad:
            raise forms.ValidationError(
                "El mínimo operativo no puede ser mayor que la cantidad total."
            )

        return cleaned


class CrearHistorico(forms.ModelForm):
    fecha_anterior = forms.DateField(
        input_formats=["%d/%m/%Y"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "class": "form-control",
                "placeholder": "dd/mm/aaaa",
            },
        ),
    )

    importancia_anterior = forms.TypedChoiceField(
        label="Importancia anterior",
        required=True,
        coerce=int,
        choices=(
            (1, "Baja"),
            (2, "Media"),
            (3, "Alta / Crítica"),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = HistoricoObjeto
        fields = [
            "objeto_del_lugar",
            "cantidad_anterior",
            "cantidad_mala_anterior",
            "cantidad_pendiente_anterior",
            "minimo_operativo_anterior",
            "importancia_anterior",
            "estado_anterior",
            "detalle_anterior",
            "fecha_anterior",
        ]

        widgets = {
            "objeto_del_lugar": forms.Select(attrs={"class": "form-select"}),
            "cantidad_anterior": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "cantidad_mala_anterior": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "cantidad_pendiente_anterior": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "minimo_operativo_anterior": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "estado_anterior": forms.Select(attrs={"class": "form-select"}),
            "detalle_anterior": forms.TextInput(attrs={"class": "form-control"}),
        }

        labels = {
            "objeto_del_lugar": "Objeto del lugar",
            "cantidad_anterior": "Cantidad total anterior",
            "cantidad_mala_anterior": "Cantidad mala anterior",
            "cantidad_pendiente_anterior": "Cantidad pendiente anterior",
            "minimo_operativo_anterior": "Mínimo operativo anterior",
            "estado_anterior": "Condición anterior",
            "detalle_anterior": "Detalle anterior",
            "fecha_anterior": "Fecha anterior",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.initial.get("objeto_del_lugar") or getattr(self.instance, "objeto_del_lugar_id", None):
            self.fields["objeto_del_lugar"].disabled = True

    def clean(self):
        cleaned = super().clean()

        cantidad = cleaned.get("cantidad_anterior") or 0
        cantidad_mala = cleaned.get("cantidad_mala_anterior") or 0
        cantidad_pendiente = cleaned.get("cantidad_pendiente_anterior") or 0
        minimo_operativo = cleaned.get("minimo_operativo_anterior")
        if minimo_operativo is None:
            minimo_operativo = 1

        if cantidad <= 0:
            raise forms.ValidationError("La cantidad total anterior debe ser mayor a 0.")

        if cantidad_mala < 0:
            raise forms.ValidationError("Las unidades malas anteriores no pueden ser negativas.")

        if cantidad_pendiente < 0:
            raise forms.ValidationError("Las unidades pendientes anteriores no pueden ser negativas.")

        if minimo_operativo < 1:
            raise forms.ValidationError("El mínimo operativo anterior debe ser al menos 1.")

        if cantidad_mala + cantidad_pendiente > cantidad:
            raise forms.ValidationError(
                "La suma de cantidad mala anterior y cantidad pendiente anterior no puede superar la cantidad total anterior."
            )

        if minimo_operativo > cantidad:
            raise forms.ValidationError(
                "El mínimo operativo anterior no puede ser mayor que la cantidad total anterior."
            )

        return cleaned


class EditarObjetoLugar(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo_de_objeto"].required = True

    class Meta:
        model = ObjetoLugar
        fields = [
            "tipo_de_objeto",
            "cantidad",
            "detalle",
            "importancia",
            "cantidad_mala",
            "cantidad_pendiente",
            "minimo_operativo",
        ]

        widgets = {
            "tipo_de_objeto": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "detalle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Detalle u observación opcional",
                }
            ),
            "importancia": forms.Select(attrs={"class": "form-select"}),
            "cantidad_mala": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "cantidad_pendiente": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "minimo_operativo": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }

        labels = {
            "tipo_de_objeto": "Tipo de objeto",
            "cantidad": "Cantidad total",
            "detalle": "Detalle",
            "importancia": "Importancia",
            "cantidad_mala": "Unidades malas",
            "cantidad_pendiente": "Unidades pendientes",
            "minimo_operativo": "Mínimo operativo",
        }

        help_texts = {
            "cantidad": "Cantidad total de unidades existentes.",
            "cantidad_mala": "Cantidad de unidades que no están funcionando.",
            "cantidad_pendiente": "Cantidad de unidades pendientes de revisión.",
            "minimo_operativo": "Cantidad mínima que debe estar funcionando para considerar aceptable este objeto.",
            "importancia": "Nivel de peso del objeto dentro del lugar.",
        }

    def clean(self):
        cleaned = super().clean()

        cantidad = cleaned.get("cantidad") or 0
        cantidad_mala = cleaned.get("cantidad_mala") or 0
        cantidad_pendiente = cleaned.get("cantidad_pendiente") or 0
        minimo_operativo = cleaned.get("minimo_operativo")
        if minimo_operativo is None:
            minimo_operativo = 1

        if cantidad <= 0:
            raise forms.ValidationError("La cantidad total debe ser mayor a 0.")

        if cantidad_mala < 0:
            raise forms.ValidationError("Las unidades malas no pueden ser negativas.")

        if cantidad_pendiente < 0:
            raise forms.ValidationError("Las unidades pendientes no pueden ser negativas.")

        if cantidad_mala + cantidad_pendiente > cantidad:
            raise forms.ValidationError(
                "La suma de unidades malas y pendientes no puede superar la cantidad total."
            )

        if minimo_operativo <= 0:
            raise forms.ValidationError("El mínimo operativo debe ser mayor a 0.")

        if minimo_operativo > cantidad:
            raise forms.ValidationError(
                "El mínimo operativo no puede ser mayor que la cantidad total."
            )

        return cleaned


class EditarHistorico(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["objeto_del_lugar"].disabled = True

    fecha_anterior = forms.DateField(
        input_formats=["%d/%m/%Y"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "class": "form-control",
                "placeholder": "dd/mm/aaaa",
            },
        ),
    )

    importancia_anterior = forms.TypedChoiceField(
        label="Importancia anterior",
        required=True,
        coerce=int,
        choices=(
            (1, "Baja"),
            (2, "Media"),
            (3, "Alta / Crítica"),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = HistoricoObjeto
        fields = [
            "objeto_del_lugar",
            "cantidad_anterior",
            "cantidad_mala_anterior",
            "cantidad_pendiente_anterior",
            "minimo_operativo_anterior",
            "importancia_anterior",
            "estado_anterior",
            "detalle_anterior",
            "fecha_anterior",
        ]

        widgets = {
            "objeto_del_lugar": forms.Select(attrs={"class": "form-select"}),
            "cantidad_anterior": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "cantidad_mala_anterior": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "cantidad_pendiente_anterior": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "minimo_operativo_anterior": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "estado_anterior": forms.Select(attrs={"class": "form-select"}),
            "detalle_anterior": forms.TextInput(attrs={"class": "form-control"}),
        }

        labels = {
            "objeto_del_lugar": "Objeto del lugar",
            "cantidad_anterior": "Cantidad total anterior",
            "cantidad_mala_anterior": "Cantidad mala anterior",
            "cantidad_pendiente_anterior": "Cantidad pendiente anterior",
            "minimo_operativo_anterior": "Mínimo operativo anterior",
            "estado_anterior": "Condición anterior",
            "detalle_anterior": "Detalle anterior",
            "fecha_anterior": "Fecha anterior",
        }

    def clean(self):
        cleaned = super().clean()

        cantidad = cleaned.get("cantidad_anterior") or 0
        cantidad_mala = cleaned.get("cantidad_mala_anterior") or 0
        cantidad_pendiente = cleaned.get("cantidad_pendiente_anterior") or 0
        minimo_operativo = cleaned.get("minimo_operativo_anterior")
        if minimo_operativo is None:
            minimo_operativo = 1

        if cantidad <= 0:
            raise forms.ValidationError("La cantidad total anterior debe ser mayor a 0.")

        if cantidad_mala < 0:
            raise forms.ValidationError("Las unidades malas anteriores no pueden ser negativas.")

        if cantidad_pendiente < 0:
            raise forms.ValidationError("Las unidades pendientes anteriores no pueden ser negativas.")

        if minimo_operativo < 1:
            raise forms.ValidationError("El mínimo operativo anterior debe ser al menos 1.")

        if cantidad_mala + cantidad_pendiente > cantidad:
            raise forms.ValidationError(
                "La suma de cantidad mala anterior y cantidad pendiente anterior no puede superar la cantidad total anterior."
            )

        if minimo_operativo > cantidad:
            raise forms.ValidationError(
                "El mínimo operativo anterior no puede ser mayor que la cantidad total anterior."
            )

        return cleaned
