from django.contrib import admin


class AccesoQRAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_hora",
        "lugar_admin",
        "ip",
        "resultado",
        "navegador_admin",
    )
    list_filter = ("resultado", "fecha_hora")
    search_fields = (
        "lugar__nombre_del_lugar",
        "ip",
        "user_agent",
        "token_huella",
    )
    fields = (
        "fecha_hora",
        "lugar",
        "ip",
        "user_agent",
        "token_huella",
        "resultado",
    )
    readonly_fields = fields
    date_hierarchy = "fecha_hora"
    list_per_page = 50
    ordering = ("-fecha_hora", "-pk")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "lugar__piso__ubicacion"
        )

    
    
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Lugar")
    def lugar_admin(self, obj):
        return obj.lugar if obj.lugar_id is not None else "Sin lugar asociado"

    @admin.display(description="Navegador / dispositivo")
    def navegador_admin(self, obj):
        agente = obj.user_agent or "-"
        return agente[:80] + ("…" if len(agente) > 80 else "")
