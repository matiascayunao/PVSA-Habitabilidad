from .vistas.autenticacion import (
    signup,
    signin,
    signout,
    home,
)

from .vistas.sectores import (
    lista_sectores,
    detalle_sector,
    crear_sector,
    editar_sector,
    borrar_sector,
)

from .vistas.ubicaciones import (
    lista_ubicaciones,
    detalle_ubicacion,
    crear_ubicacion,
    editar_ubicacion,
    borrar_ubicacion,
)

from .vistas.pisos import (
    lista_pisos,
    detalle_piso,
    crear_piso,
    editar_piso,
    borrar_piso,
)

from .vistas.lugares import (
    lista_lugares,
    detalle_lugar,
    crear_lugar,
    editar_lugar,
    borrar_lugar,
)

from .vistas.inventario import (
    lista_objetos_lugar,
    detalle_objeto_lugar,
    crear_objeto_lugar,
    editar_objeto_lugar,
    borrar_objeto_lugar,
)

from .vistas.categorias import (
    lista_tipos_lugar,
    detalle_tipo_lugar,
    crear_tipo_lugar,
    editar_tipo_lugar,
    borrar_tipo_lugar,
    lista_categorias,
    detalle_categoria,
    crear_categoria_objeto,
    editar_categoria,
    borrar_categoria,
    lista_objetos,
    detalle_objeto,
    crear_objeto,
    editar_objeto,
    borrar_objeto,
    lista_tipos_objeto,
    detalle_tipo_objeto,
    crear_tipo_objeto,
    editar_tipo_objeto,
    borrar_tipo_objeto,
)

from .vistas.historicos import (
    lista_historicos,
    detalle_historico,
    crear_historico,
    editar_historico,
    borrar_historico,
)

from .vistas.resumen import (
    _acumular_objeto_en_resumen,
    _cerrar_resumen,
    resumen_general,
)

from .vistas.consultas_dinamicas import (
    ajax_ubicaciones_por_sector,
    ajax_pisos_por_ubicacion,
    ajax_lugares_por_piso,
    ajax_objetos_por_categoria,
    ajax_tipos_por_objeto,
    objetos_tipicos_por_tipo_lugar,
    ajax_filtros_dependientes,
    TIPICOS_POR_TIPO_LUGAR,
)

from .vistas.estructura import (
    crear_estructura,
)

from .vistas.excel import (
    descargar_excel_sectores,
    _norm_header,
    _clean_text,
    _to_int,
    _importancia_to_int,
    _row_first_text,
    _find_sector_ubicacion,
    _parse_normalizado,
    _parse_exportado,
    parse_excel,
    _split_tipo,
    import_from_rows,
    carga_masiva,
    descargar_plantilla_carga_masiva,
    HEADER_ALIASES,
    REQUIRED_HEADERS_NORMALIZADO,
    RE_SECTOR_UBI,
    RE_PISO,
    RE_TIPO_LUGAR,
)

from .vistas.qr import (
    qr_lugar,
    consulta_qr,
)

from .vistas.eliminacion import (
    _confirm_delete,
)
