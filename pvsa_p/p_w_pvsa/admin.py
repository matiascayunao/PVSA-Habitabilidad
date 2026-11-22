from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError

from .models import (
    Sector,
    Ubicacion,
    Piso,
    TipoLugar,
    Lugar,
    CategoriaObjeto,
    Objeto,
    TipoObjeto,
    TipoLugarObjetoTipico,
    ObjetoLugar,
    HistoricoObjeto,
    AccesoQR,
)

from .administracion.estructura import (
    LugarInline,
    PisoInline,
    UbicacionInline,
    SectorAdmin,
    UbicacionAdmin,
    PisoAdmin,
    LugarAdmin,
)

from .administracion.catalogos import (
    TipoObjetoInline,
    ObjetoInline,
    CategoriaObjetoAdmin,
    TipoLugarObjetoTipicoInline,
    TipoLugarAdmin,
    ObjetoAdmin,
    TipoObjetoAdmin,
)

from .administracion.inventario import (
    texto_importancia,
    HistoricoObjetoInline,
    ObjetoLugarInline,
    ObjetoLugarAdmin,
    HistoricoObjetoAdminForm,
    HistoricoObjetoAdmin,
)

from .administracion.qr import (
    AccesoQRAdmin,
)

class AutenticacionAdminTecnico(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )


def _acceso_admin_tecnico(request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = _acceso_admin_tecnico
admin.site.login_form = AutenticacionAdminTecnico

admin.site.site_header = "Administración PVSA"

admin.site.site_title = "PVSA"

admin.site.index_title = "Panel de administración"

admin.site.register(
    Sector,
    SectorAdmin,
)

admin.site.register(
    Ubicacion,
    UbicacionAdmin,
)

admin.site.register(
    Piso,
    PisoAdmin,
)

admin.site.register(
    TipoLugar,
    TipoLugarAdmin,
)

admin.site.register(
    Lugar,
    LugarAdmin,
)

admin.site.register(
    CategoriaObjeto,
    CategoriaObjetoAdmin,
)

admin.site.register(
    Objeto,
    ObjetoAdmin,
)

admin.site.register(
    TipoObjeto,
    TipoObjetoAdmin,
)

admin.site.register(
    TipoLugarObjetoTipico,
)

admin.site.register(
    ObjetoLugar,
    ObjetoLugarAdmin,
)

admin.site.register(
    HistoricoObjeto,
    HistoricoObjetoAdmin,
)

admin.site.register(
    AccesoQR,
    AccesoQRAdmin,
)
