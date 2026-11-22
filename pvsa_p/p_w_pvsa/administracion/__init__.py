import nested_admin
from django.core.exceptions import ValidationError


class FormsetAnidadoSeguro(nested_admin.NestedInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if (
                self.model._meta.label_lower == "p_w_pvsa.objetolugar"
                and form.cleaned_data.get("DELETE") and form.instance.pk
                and form.instance.historicoobjeto.exists()
            ):
                raise ValidationError("No se puede eliminar un inventario con históricos asociados.")
            identificador = form.cleaned_data.get(self.model._meta.pk.name)
            if identificador is not None and not self.model._default_manager.filter(
                pk=getattr(identificador, "pk", identificador),
                **{self.fk.attname: self.instance.pk},
            ).exists():
                raise ValidationError("El registro seleccionado no pertenece a este formulario. No se guardaron cambios.")
