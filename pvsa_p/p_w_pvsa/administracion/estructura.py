import uuid

import nested_admin
from django.contrib import admin
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html

from ..models import Lugar, Piso, Ubicacion
from .inventario import ObjetoLugarInline


class LugarInline(nested_admin.NestedStackedInline):
    model = Lugar
    extra = 0
    inlines = [
        ObjetoLugarInline,
    ]
    fields = (
        "nombre_del_lugar",
        "lugar_tipo_lugar",
        "operatividad_lugar_admin",
    )
    readonly_fields = (
        "operatividad_lugar_admin",
    )
    autocomplete_fields = (
        "lugar_tipo_lugar",
    )

    @admin.display(description="Operatividad del lugar")
    def operatividad_lugar_admin(self, obj):
        if obj and obj.pk:
            return f"{obj.operatividad_lugar}%"
        return "-"


class PisoInline(nested_admin.NestedStackedInline):
    model = Piso
    extra = 0
    inlines = [
        LugarInline,
    ]


class UbicacionInline(nested_admin.NestedStackedInline):
    model = Ubicacion
    extra = 0
    inlines = [
        PisoInline,
    ]
    fields = (
        "ubicacion",
    )


class SectorAdmin(nested_admin.NestedModelAdmin):
    inlines = [
        UbicacionInline,
    ]
    list_display = (
        "sector",
    )
    search_fields = (
        "sector",
    )


class UbicacionAdmin(admin.ModelAdmin):
    list_display = (
        "ubicacion",
        "sector",
    )
    list_filter = (
        "sector",
    )
    search_fields = (
        "ubicacion",
        "sector__sector",
    )


class PisoAdmin(admin.ModelAdmin):
    list_display = (
        "piso",
        "ubicacion",
        "sector_admin",
    )
    list_filter = (
        "ubicacion__sector",
        "ubicacion",
    )
    search_fields = (
        "=piso",
        "ubicacion__ubicacion",
        "ubicacion__sector__sector",
    )

    @admin.display(description="Sector")
    def sector_admin(self, obj):
        return obj.ubicacion.sector


class LugarAdmin(nested_admin.NestedModelAdmin):
    inlines = [
        ObjetoLugarInline,
    ]
    list_display = (
        "nombre_del_lugar",
        "tipo_lugar_admin",
        "piso",
        "ubicacion_admin",
        "sector_admin",
        "operatividad_lugar_admin",
        "qr_estado_admin",
    )
    list_filter = (
        "lugar_tipo_lugar",
        "piso__ubicacion__sector",
        "piso__ubicacion",
        "piso",
        "qr_activo",
    )
    search_fields = (
        "nombre_del_lugar",
        "lugar_tipo_lugar__tipo_de_lugar",
        "piso__ubicacion__ubicacion",
        "piso__ubicacion__sector__sector",
    )
    readonly_fields = (
        "operatividad_lugar_admin",
    )
    fields = (
        "nombre_del_lugar",
        "piso",
        "lugar_tipo_lugar",
        "operatividad_lugar_admin",
    )

    
    
    actions = (
        "activar_qr_seleccionados",
        "desactivar_qr_seleccionados",
        "regenerar_qr_seleccionados",
    )

    def has_gestionar_qr_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def get_fields(self, request, obj=None):
        campos = list(super().get_fields(request, obj))
        if request.user.is_superuser:
            campos.extend(("qr_estado_admin", "qr_enlace_admin"))
        return campos

    def get_readonly_fields(self, request, obj=None):
        campos = list(super().get_readonly_fields(request, obj))
        if request.user.is_superuser:
            campos.extend(("qr_estado_admin", "qr_enlace_admin"))
        return campos

    @admin.display(description="QR público activo", boolean=True)
    def qr_estado_admin(self, obj):
        if obj is None or obj.pk is None:
            return None
        return obj.qr_activo

    @admin.display(description="Enlace de consulta QR")
    def qr_enlace_admin(self, obj):
        if obj is None or obj.pk is None:
            return "Disponible después de guardar el lugar."
        ruta = reverse("consulta_qr", kwargs={"token": str(obj.qr_token)})
        if not obj.qr_activo:
            return format_html(
                "{} — QR desactivado. Actívalo desde la lista de lugares.", ruta
            )
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            ruta,
            ruta,
        )

    @admin.action(
        description="QR: activar consultas para los lugares seleccionados",
        permissions=["gestionar_qr"],
    )
    def activar_qr_seleccionados(self, request, queryset):
        actualizados = 0
        with transaction.atomic():
            for lugar in queryset.select_related("piso__ubicacion").iterator():
                if not lugar.qr_activo:
                    lugar.qr_activo = True
                    lugar.save(update_fields=["qr_activo"])
                    self.log_change(request, lugar, "Activó la consulta pública QR.")
                    actualizados += 1
        self.message_user(request, f"QR activados: {actualizados}.")

    @admin.action(
        description="QR: desactivar consultas para los lugares seleccionados",
        permissions=["gestionar_qr"],
    )
    def desactivar_qr_seleccionados(self, request, queryset):
        actualizados = 0
        with transaction.atomic():
            for lugar in queryset.select_related("piso__ubicacion").iterator():
                if lugar.qr_activo:
                    lugar.qr_activo = False
                    lugar.save(update_fields=["qr_activo"])
                    self.log_change(request, lugar, "Desactivó la consulta pública QR.")
                    actualizados += 1
        self.message_user(request, f"QR desactivados: {actualizados}.")

    @admin.action(
        description="QR: REGENERAR tokens (invalida los QR anteriores)",
        permissions=["gestionar_qr"],
    )
    def regenerar_qr_seleccionados(self, request, queryset):
        actualizados = 0
        with transaction.atomic():
            for lugar in queryset.select_related("piso__ubicacion").iterator():
                
                lugar.qr_token = uuid.uuid4()
                lugar.save(update_fields=["qr_token"])
                self.log_change(request, lugar, "Regeneró el token QR público.")
                actualizados += 1
        self.message_user(
            request,
            f"Tokens QR regenerados: {actualizados}. "
            "Los anteriores ya no sirven; el estado activo/inactivo no cambió.",
        )

    @admin.display(description="Tipo de lugar")
    def tipo_lugar_admin(self, obj):
        return obj.lugar_tipo_lugar

    @admin.display(description="Ubicación")
    def ubicacion_admin(self, obj):
        return obj.piso.ubicacion

    @admin.display(description="Sector")
    def sector_admin(self, obj):
        return obj.piso.ubicacion.sector

    @admin.display(description="Operatividad")
    def operatividad_lugar_admin(self, obj):
        if obj and obj.pk:
            return f"{obj.operatividad_lugar}%"
        return "-"
