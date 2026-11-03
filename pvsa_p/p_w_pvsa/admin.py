from django.contrib import admin

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
