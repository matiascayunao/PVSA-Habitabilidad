import nested_admin
from django import forms
from django.contrib import admin

from ..models import HistoricoObjeto, ObjetoLugar


def texto_importancia(valor):
    if valor == 3:
        return "Alta / Crítica"
    if valor == 2:
        return "Media"
    return "Baja"


class HistoricoObjetoInline(nested_admin.NestedTabularInline):
    model = HistoricoObjeto
    extra = 0
    can_delete = False
    fields = (
        "identidad_variante",
        "cantidad_anterior",
        "cantidad_mala_anterior",
        "cantidad_pendiente_anterior",
        "minimo_operativo_anterior",
        "importancia_anterior",
        "estado_anterior",
        "detalle_anterior",
        "fecha_anterior",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class ObjetoLugarInline(nested_admin.NestedTabularInline):
    model = ObjetoLugar
    extra = 0
    inlines = [
        HistoricoObjetoInline,
    ]
    fields = (
        "tipo_de_objeto",
        "cantidad",
        "cantidad_buena_admin",
        "cantidad_mala",
        "cantidad_pendiente",
        "minimo_operativo",
        "importancia",
        "operatividad_objeto_admin",
        "estado_calculado_admin",
        "detalle",
        "fecha",
    )
    readonly_fields = (
        "cantidad_buena_admin",
        "operatividad_objeto_admin",
        "estado_calculado_admin",
        "fecha",
    )
    autocomplete_fields = (
        "tipo_de_objeto",
    )

    @admin.display(description="Buenas")
    def cantidad_buena_admin(self, obj):
        if obj and obj.pk:
            return obj.cantidad_buena
        return "-"

    @admin.display(description="Operatividad")
    def operatividad_objeto_admin(self, obj):
        if obj and obj.pk:
            return f"{obj.operatividad_objeto}%"
        return "-"

    @admin.display(description="Condición")
    def estado_calculado_admin(self, obj):
        if not obj or not obj.pk:
            return "-"
        return obj.get_estado_display()


class ObjetoLugarAdmin(nested_admin.NestedModelAdmin):
    inlines = [
        HistoricoObjetoInline,
    ]
    list_display = (
        "objeto_admin",
        "lugar",
        "cantidad",
        "cantidad_buena_admin",
        "cantidad_mala",
        "cantidad_pendiente",
        "minimo_operativo",
        "importancia_admin",
        "operatividad_objeto_admin",
        "estado_calculado_admin",
        "fecha",
    )
    list_filter = (
        "estado",
        "importancia",
        "lugar__lugar_tipo_lugar",
        "lugar__piso__ubicacion__sector",
        "lugar__piso__ubicacion",
        "tipo_de_objeto__objeto__objeto_categoria",
    )
    search_fields = (
        "tipo_de_objeto__objeto__nombre_del_objeto",
        "tipo_de_objeto__marca",
        "tipo_de_objeto__material",
        "lugar__nombre_del_lugar",
        "lugar__piso__ubicacion__ubicacion",
        "lugar__piso__ubicacion__sector__sector",
        "detalle",
    )
    autocomplete_fields = (
        "lugar",
        "tipo_de_objeto",
    )
    readonly_fields = (
        "cantidad_buena_admin",
        "operatividad_objeto_admin",
        "estado_calculado_admin",
        "fecha",
    )
    fieldsets = (
        (
            "Objeto y lugar",
            {
                "fields": (
                    "lugar",
                    "tipo_de_objeto",
                )
            },
        ),
        (
            "Cantidades y cálculo",
            {
                "fields": (
                    "cantidad",
                    "cantidad_buena_admin",
                    "cantidad_mala",
                    "cantidad_pendiente",
                    "minimo_operativo",
                    "importancia",
                    "operatividad_objeto_admin",
                    "estado_calculado_admin",
                )
            },
        ),
        (
            "Detalle",
            {
                "fields": (
                    "detalle",
                    "fecha",
                )
            },
        ),
    )
    date_hierarchy = "fecha"

    @admin.display(description="Objeto")
    def objeto_admin(self, obj):
        if (
            obj
            and obj.tipo_de_objeto
            and obj.tipo_de_objeto.objeto
        ):
            return obj.tipo_de_objeto.objeto.nombre_del_objeto
        return "-"

    @admin.display(description="Buenas")
    def cantidad_buena_admin(self, obj):
        return obj.cantidad_buena

    @admin.display(description="Importancia")
    def importancia_admin(self, obj):
        return obj.get_importancia_display()

    @admin.display(description="Operatividad")
    def operatividad_objeto_admin(self, obj):
        return f"{obj.operatividad_objeto}%"

    @admin.display(description="Condición")
    def estado_calculado_admin(self, obj):
        return obj.get_estado_display()


class HistoricoObjetoAdminForm(forms.ModelForm):
    importancia_anterior = forms.TypedChoiceField(
        label="Importancia anterior",
        required=True,
        coerce=int,
        choices=ObjetoLugar.IMPORTANCIA,
        widget=forms.Select,
    )
    estado_anterior = forms.ChoiceField(
        label="Condición anterior",
        required=True,
        choices=ObjetoLugar.ESTADO,
        widget=forms.Select,
    )
    class Meta:
        model = HistoricoObjeto
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        cantidad = (
            cleaned.get("cantidad_anterior")
            or 0
        )
        cantidad_mala = (
            cleaned.get("cantidad_mala_anterior")
            or 0
        )
        cantidad_pendiente = (
            cleaned.get("cantidad_pendiente_anterior")
            or 0
        )
        minimo_operativo = (
            cleaned.get("minimo_operativo_anterior")
            or 1
        )
        if cantidad <= 0:
            raise forms.ValidationError(
                "La cantidad anterior debe ser mayor a 0."
            )
        if cantidad_mala < 0:
            raise forms.ValidationError(
                "Las unidades malas no pueden ser negativas."
            )
        if cantidad_pendiente < 0:
            raise forms.ValidationError(
                "Las unidades pendientes no pueden ser negativas."
            )
        if (
            cantidad_mala
            + cantidad_pendiente
            > cantidad
        ):
            raise forms.ValidationError(
                "La suma de unidades malas y pendientes "
                "no puede superar la cantidad total."
            )
        if minimo_operativo < 1:
            raise forms.ValidationError(
                "El mínimo operativo debe ser al menos 1."
            )
        if minimo_operativo > cantidad:
            raise forms.ValidationError(
                "El mínimo operativo no puede ser mayor "
                "que la cantidad total."
            )
        return cleaned


class HistoricoObjetoAdmin(admin.ModelAdmin):
    form = HistoricoObjetoAdminForm
    readonly_fields = ("identidad_variante",)
    fieldsets = (
        (
            "Objeto asociado",
            {
                "fields": (
                    "objeto_del_lugar",
                    "identidad_variante",
                )
            },
        ),
        (
            "Unidades anteriores",
            {
                "fields": (
                    "cantidad_anterior",
                    "cantidad_mala_anterior",
                    "cantidad_pendiente_anterior",
                    "minimo_operativo_anterior",
                )
            },
        ),
        (
            "Condición anterior",
            {
                "fields": (
                    "importancia_anterior",
                    "estado_anterior",
                    "detalle_anterior",
                    "fecha_anterior",
                )
            },
        ),
    )
    list_display = (
        "objeto_admin",
        "lugar_admin",
        "cantidad_anterior",
        "cantidad_mala_anterior",
        "cantidad_pendiente_anterior",
        "minimo_operativo_anterior",
        "importancia_anterior_admin",
        "estado_anterior_admin",
        "fecha_anterior",
    )
    list_filter = (
        "estado_anterior",
        "importancia_anterior",
        "fecha_anterior",
        "objeto_del_lugar__lugar__piso__ubicacion__sector",
        "objeto_del_lugar__lugar__piso__ubicacion",
    )
    search_fields = (
        "variante_anterior__objeto",
        "variante_anterior__marca",
        "variante_anterior__material",
        "objeto_del_lugar__lugar__nombre_del_lugar",
        "detalle_anterior",
    )
    autocomplete_fields = (
        "objeto_del_lugar",
    )
    date_hierarchy = "fecha_anterior"

    @admin.display(description="Objeto")
    def objeto_admin(self, obj):
        return obj.identidad_variante

    @admin.display(description="Lugar")
    def lugar_admin(self, obj):
        if (
            obj.objeto_del_lugar
            and obj.objeto_del_lugar.lugar
        ):
            return obj.objeto_del_lugar.lugar
        return "-"

    @admin.display(description="Importancia anterior")
    def importancia_anterior_admin(self, obj):
        return texto_importancia(
            obj.importancia_anterior
        )

    @admin.display(description="Condición anterior")
    def estado_anterior_admin(self, obj):
        return obj.get_estado_anterior_display()
