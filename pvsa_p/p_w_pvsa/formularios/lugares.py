from django import forms
from django.forms import ModelForm
from ..models import Lugar, Piso, TipoLugar


class CrearLugar(ModelForm):
    class Meta:
        model = Lugar
        fields = ["nombre_del_lugar","piso","lugar_tipo_lugar","es_area_comun",]
        widgets = {
            "nombre_del_lugar": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Baño hombres principal",
                    "autocomplete": "off",
                }
            ),
            "piso": forms.Select(
                attrs={"class": "form-select"}
            ),
            "lugar_tipo_lugar": forms.Select(
                attrs={"class": "form-select"}
            ),
            "es_area_comun": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["piso"].queryset = (
            Piso.objects
            .select_related("ubicacion", "ubicacion__sector")
            .order_by(
                "ubicacion__sector__sector",
                "ubicacion__ubicacion",
                "piso",
            )
        )

        self.fields["piso"].label_from_instance = (
            lambda piso:
            f"{piso.ubicacion.sector.sector} · "
            f"{piso.ubicacion.ubicacion} · "
            f"Piso {piso.piso}"
        )

    def clean_nombre_del_lugar(self):
        nombre = " ".join(
            (self.cleaned_data.get("nombre_del_lugar") or "").split()
        )
        return nombre

    def clean(self):
        cleaned = super().clean()

        nombre = cleaned.get("nombre_del_lugar")
        piso = cleaned.get("piso")

        if not nombre or not piso:
            return cleaned

        nombre_normalizado = nombre.casefold()

        existentes = Lugar.objects.filter(piso=piso)

        for existente in existentes:
            nombre_existente = " ".join(
                (existente.nombre_del_lugar or "").split()
            ).casefold()

            if nombre_existente == nombre_normalizado:
                self.add_error(
                    "nombre_del_lugar",
                    "Ya existe un lugar con este nombre en el piso seleccionado.",
                )
                break

        return cleaned


class CrearTipoLugar(ModelForm):
    class Meta:
        model = TipoLugar
        fields = ["tipo_de_lugar"]
        widgets = {
            "tipo_de_lugar": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Baño",
                    "autocomplete": "off",
                }
            )
        }

    def clean_tipo_de_lugar(self):
        nombre = " ".join(
            (self.cleaned_data.get("tipo_de_lugar") or "").split()
        )

        if not nombre:
            return nombre

        if TipoLugar.objects.filter(
            tipo_de_lugar__iexact=nombre
        ).exists():
            raise forms.ValidationError(
                "Ya existe un tipo de lugar con este nombre."
            )

        return nombre


class EditarTipoLugar(ModelForm):
    class Meta:
        model = TipoLugar
        fields = ["tipo_de_lugar"]
        widgets = {
            "tipo_de_lugar": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            )
        }

    def clean_tipo_de_lugar(self):
        nombre = " ".join(
            (self.cleaned_data.get("tipo_de_lugar") or "").split()
        )

        if not nombre:
            return nombre

        existe = (
            TipoLugar.objects
            .filter(tipo_de_lugar__iexact=nombre)
            .exclude(pk=self.instance.pk)
            .exists()
        )

        if existe:
            raise forms.ValidationError(
                "Ya existe otro tipo de lugar con este nombre."
            )

        return nombre


class EditarLugar(ModelForm):
    class Meta:
        model = Lugar
        fields = ["nombre_del_lugar", "piso", "lugar_tipo_lugar", "es_area_comun"]
        widgets = {
            "nombre_del_lugar": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "piso": forms.Select(
                attrs={"class": "form-select"}
            ),
            "lugar_tipo_lugar": forms.Select(
                attrs={"class": "form-select"}
            ),
            "es_area_comun": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["piso"].queryset = (
            Piso.objects
            .select_related("ubicacion", "ubicacion__sector")
            .order_by(
                "ubicacion__sector__sector",
                "ubicacion__ubicacion",
                "piso",
            )
        )

        self.fields["piso"].label_from_instance = (
            lambda piso:
            f"{piso.ubicacion.sector.sector} · "
            f"{piso.ubicacion.ubicacion} · "
            f"Piso {piso.piso}"
        )

    def clean_nombre_del_lugar(self):
        nombre = " ".join(
            (self.cleaned_data.get("nombre_del_lugar") or "").split()
        )
        return nombre

    def clean(self):
        cleaned = super().clean()

        nombre = cleaned.get("nombre_del_lugar")
        piso = cleaned.get("piso")

        if not nombre or not piso:
            return cleaned

        nombre_normalizado = nombre.casefold()

        existentes = (
            Lugar.objects
            .filter(piso=piso)
            .exclude(pk=self.instance.pk)
        )

        for existente in existentes:
            nombre_existente = " ".join(
                (existente.nombre_del_lugar or "").split()
            ).casefold()

            if nombre_existente == nombre_normalizado:
                self.add_error(
                    "nombre_del_lugar",
                    "Ya existe otro lugar con este nombre en el piso seleccionado.",
                )
                break

        return cleaned