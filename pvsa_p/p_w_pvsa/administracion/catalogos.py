import nested_admin
from django.contrib import admin

from ..models import Objeto, TipoObjeto, TipoLugarObjetoTipico
from .estructura import UnicidadAdminMixin


class TipoObjetoInline(nested_admin.NestedTabularInline):
    model = TipoObjeto
    extra = 0
    fields = (
        "marca",
        "material",
    )


class ObjetoInline(nested_admin.NestedStackedInline):
    model = Objeto
    extra = 0
    inlines = [
        TipoObjetoInline,
    ]
    fields = (
        "nombre_del_objeto",
    )


class CategoriaObjetoAdmin(UnicidadAdminMixin, nested_admin.NestedModelAdmin):
    inlines = [
        ObjetoInline,
    ]
    list_display = (
        "nombre_de_categoria",
    )
    search_fields = (
        "nombre_de_categoria",
    )


class TipoLugarObjetoTipicoInline(admin.TabularInline):
    model = TipoLugarObjetoTipico
    extra = 0
    fields = (
        "tipo_objeto",
        "importancia",
        "orden",
        "activo",
    )
    autocomplete_fields = (
        "tipo_objeto",
    )


class TipoLugarAdmin(admin.ModelAdmin):
    inlines = [
        TipoLugarObjetoTipicoInline,
    ]
    list_display = (
        "tipo_de_lugar",
        "cantidad_tipicos_admin",
    )
    search_fields = (
        "tipo_de_lugar",
    )

    @admin.display(description="Objetos típicos")
    def cantidad_tipicos_admin(self, obj):
        return obj.tipicos.count()


class ObjetoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_del_objeto",
        "objeto_categoria",
    )
    list_filter = (
        "objeto_categoria",
    )
    search_fields = (
        "nombre_del_objeto",
        "objeto_categoria__nombre_de_categoria",
    )


class TipoObjetoAdmin(UnicidadAdminMixin, admin.ModelAdmin):
    list_display = (
        "objeto",
        "categoria_admin",
        "marca",
        "material",
    )
    list_filter = (
        "objeto__objeto_categoria",
        "marca",
        "material",
    )
    search_fields = (
        "objeto__nombre_del_objeto",
        "objeto__objeto_categoria__nombre_de_categoria",
        "marca",
        "material",
    )

    @admin.display(description="Categoría")
    def categoria_admin(self, obj):
        return obj.objeto.objeto_categoria
