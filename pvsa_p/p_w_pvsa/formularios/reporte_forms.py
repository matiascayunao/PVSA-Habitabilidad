from django import forms

from ..models import ReporteIncidencia


ELEMENTOS = [
    ("", "Selecciona un elemento..."),
    ("Lavamanos / grifería", "Lavamanos / grifería"),
    ("WC / urinario", "WC / urinario"),
    ("Ducha", "Ducha"),
    ("Iluminación", "Iluminación"),
    ("Puerta / cerradura", "Puerta / cerradura"),
    ("Mesa / silla / mobiliario", "Mesa / silla / mobiliario"),
    ("Limpieza / higiene", "Limpieza / higiene"),
    ("otro", "Otro elemento"),
]


class ReportePublicoForm(forms.ModelForm):

    elemento_opcion = forms.ChoiceField(
        choices=ELEMENTOS,
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
    )

    otro_elemento = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Escribe el nombre del elemento...",
            }
        ),
    )

    class Meta:
        model = ReporteIncidencia

        fields = (
            "tipo_problema",
            "descripcion",
            "foto",
        )

        widgets = {
            "tipo_problema": forms.Select(
                attrs={"class": "form-select"}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Describe el problema, si quieres..."
                    ),
                }
            ),
            "foto": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
        }

    def clean(self):
        datos = super().clean()

        if datos.get("elemento_opcion") == "otro":
            nombre = (
                datos.get("otro_elemento") or ""
            ).strip()

            if not nombre:
                self.add_error(
                    "otro_elemento",
                    "Indica qué elemento presenta el problema.",
                )

        return datos

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")

        if foto:
            if foto.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "La fotografía no puede superar 5 MB."
                )

            imagen = getattr(foto, "image", None)

            if (
                imagen is None
                or imagen.format not in {"JPEG", "PNG", "WEBP"}
            ):
                raise forms.ValidationError(
                    "Solo se permiten fotografías JPG, PNG o WebP."
                )

            if imagen.width * imagen.height > 20_000_000:
                raise forms.ValidationError(
                    "La fotografía tiene una resolución demasiado alta."
                )

        return foto
