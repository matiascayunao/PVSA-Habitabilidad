from django import forms
from django.forms import ModelForm
from ..models import CategoriaObjeto, Objeto, TipoObjeto


class CrearCategoriaObjeto(ModelForm):
    class Meta:
        model = CategoriaObjeto
        fields = ["nombre_de_categoria"]
        widgets = {
            "nombre_de_categoria": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Sanitarios",
                    "autocomplete": "off",
                }
            )
        }

    def clean_nombre_de_categoria(self):
        nombre = " ".join(
            (self.cleaned_data.get("nombre_de_categoria") or "").split()
        )

        if not nombre:
            return nombre

        if CategoriaObjeto.objects.filter(
            nombre_de_categoria__iexact=nombre
        ).exists():
            raise forms.ValidationError(
                "Ya existe una categoría con este nombre."
            )

        return nombre


class CrearObjeto(ModelForm):
    class Meta:
        model = Objeto
        fields = ["nombre_del_objeto", "objeto_categoria"]
        widgets = {
            "nombre_del_objeto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Lavamanos",
                    "autocomplete": "off",
                }
            ),
            "objeto_categoria": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

    def clean_nombre_del_objeto(self):
        nombre = " ".join(
            (self.cleaned_data.get("nombre_del_objeto") or "").split()
        )

        if not nombre:
            return nombre

        if Objeto.objects.filter(
            nombre_del_objeto__iexact=nombre
        ).exists():
            raise forms.ValidationError(
                "Ya existe un objeto con este nombre."
            )

        return nombre


class CrearTipoObjeto(ModelForm):
    class Meta:
        model = TipoObjeto
        fields = ["objeto", "marca", "material"]
        widgets = {
            "objeto": forms.Select(
                attrs={"class": "form-select"}
            ),
            "marca": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Fanaloza",
                    "autocomplete": "off",
                }
            ),
            "material": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Cerámica",
                    "autocomplete": "off",
                }
            ),
        }

    def clean_marca(self):
        valor = " ".join(
            (self.cleaned_data.get("marca") or "").split()
        )
        return valor or None

    def clean_material(self):
        valor = " ".join(
            (self.cleaned_data.get("material") or "").split()
        )
        return valor or None

    def clean(self):
        cleaned = super().clean()

        objeto = cleaned.get("objeto")
        marca = cleaned.get("marca")
        material = cleaned.get("material")

        if not objeto:
            return cleaned

        marca_normalizada = (marca or "").strip().casefold()
        material_normalizado = (material or "").strip().casefold()

        for existente in TipoObjeto.objects.filter(objeto=objeto):
            if (
                (existente.marca or "").strip().casefold() == marca_normalizada
                and
                (existente.material or "").strip().casefold() == material_normalizado
            ):
                raise forms.ValidationError(
                    "Esta variante ya existe para el objeto seleccionado."
                )

        return cleaned


class EditarCategoria(ModelForm):
    class Meta:
        model = CategoriaObjeto
        fields = ["nombre_de_categoria"]
        widgets = {
            "nombre_de_categoria": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            )
        }

    def clean_nombre_de_categoria(self):
        nombre = " ".join(
            (self.cleaned_data.get("nombre_de_categoria") or "").split()
        )

        if not nombre:
            return nombre

        existe = (
            CategoriaObjeto.objects
            .filter(nombre_de_categoria__iexact=nombre)
            .exclude(pk=self.instance.pk)
            .exists()
        )

        if existe:
            raise forms.ValidationError(
                "Ya existe otra categoría con este nombre."
            )

        return nombre


class EditarObjeto(ModelForm):
    class Meta:
        model = Objeto
        fields = ["nombre_del_objeto", "objeto_categoria"]
        widgets = {
            "nombre_del_objeto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "objeto_categoria": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

    def clean_nombre_del_objeto(self):
        nombre = " ".join(
            (self.cleaned_data.get("nombre_del_objeto") or "").split()
        )

        if not nombre:
            return nombre

        existe = (
            Objeto.objects
            .filter(nombre_del_objeto__iexact=nombre)
            .exclude(pk=self.instance.pk)
            .exists()
        )

        if existe:
            raise forms.ValidationError(
                "Ya existe otro objeto con este nombre."
            )

        return nombre


class EditarTipoObjeto(ModelForm):
    class Meta:
        model = TipoObjeto
        fields = ["objeto", "marca", "material"]
        widgets = {
            "objeto": forms.Select(
                attrs={"class": "form-select"}
            ),
            "marca": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "material": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
        }

    def clean_marca(self):
        valor = " ".join(
            (self.cleaned_data.get("marca") or "").split()
        )
        return valor or None

    def clean_material(self):
        valor = " ".join(
            (self.cleaned_data.get("material") or "").split()
        )
        return valor or None

    def clean(self):
        cleaned = super().clean()

        objeto = cleaned.get("objeto")
        marca = cleaned.get("marca")
        material = cleaned.get("material")

        if not objeto:
            return cleaned

        marca_normalizada = (marca or "").strip().casefold()
        material_normalizado = (material or "").strip().casefold()

        existentes = (
            TipoObjeto.objects
            .filter(objeto=objeto)
            .exclude(pk=self.instance.pk)
        )

        for existente in existentes:
            if (
                (existente.marca or "").strip().casefold() == marca_normalizada
                and
                (existente.material or "").strip().casefold() == material_normalizado
            ):
                raise forms.ValidationError(
                    "Ya existe otra variante con esta misma marca y material."
                )

        return cleaned