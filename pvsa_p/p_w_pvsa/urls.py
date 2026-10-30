from functools import wraps

from django.contrib.auth.views import redirect_to_login

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from django.urls import path as django_path, reverse

from . import views, incidencias_views, jefes_views, jefes_inventario_views, superadmin_jefes_views, jefes_reportes_views

# =========================================================

# RUTAS PÚBLICAS

# =========================================================

RUTAS_PUBLICAS = {

    "signin",

    "consulta_qr",

}

# =========================================================

# FUNCIONES EXCLUSIVAS PARA ADMINISTRADORES

# =========================================================

RUTAS_ADMINISTRADOR = {

    # Usuarios

    "signup",

    # Eliminación de estructura

    "borrar_sector",

    "borrar_ubicacion",

    "borrar_piso",

    "borrar_lugar",

    # Eliminación de objetos

    "borrar_objeto_lugar",

    "borrar_tipo_lugar",

    "borrar_categoria",

    "borrar_objeto",

    "borrar_tipo_objeto",

    # Eliminación de históricos

    "borrar_historico",

    # Carga masiva

    "carga_masiva",

    "descargar_plantilla_carga_masiva",

    # Reportes

    "descargar_excel_sectores",

    "lista_incidencias",

    "detalle_incidencia",

    "foto_incidencia"

}

# =========================================================
# RUTAS SEGURAS HABILITADAS PARA JEFE DE DEPARTAMENTO
# Se habilitan de forma gradual. El resto continúa bloqueado.
# =========================================================

RUTAS_JEFE = {
    "panel_jefe",
    "detalle_lugar_jefe",
    "jefe_crear_objeto",
    "jefe_editar_objeto",
    "jefe_reportar_incidencia",
    "jefe_mis_reportes",
    "jefe_foto_reporte",
    "signout",
}

# =========================================================

# VERIFICACIÓN CENTRALIZADA DE ROLES

# =========================================================

def proteger_vista(vista, nombre_ruta):

    @wraps(vista)

    def vista_protegida(request, *args, **kwargs):

        # Las rutas públicas no requieren autenticación.

        if nombre_ruta in RUTAS_PUBLICAS:

            return vista(request, *args, **kwargs)

        # Los visitantes deben iniciar sesión.

        if not request.user.is_authenticated:

            return redirect_to_login(

                request.get_full_path(),

                login_url=reverse("signin"),

            )

        # El superusuario tiene acceso completo.

        if request.user.is_superuser:

            return vista(request, *args, **kwargs)

        # Cuenta y asignaciones: solo Superadmin (no Mini-Admin).
        if nombre_ruta in {
            "superadmin_lista_jefes",
            "superadmin_crear_jefe",
            "superadmin_editar_jefe",
        }:
            raise PermissionDenied("Solo el Superadmin puede gestionar jefes.")

        # Obtener los grupos asignados al usuario.

        grupos = set(

            request.user.groups.values_list(

                "name",

                flat=True,

            )

        )

        # Jefe: acceso mínimo y segmentado por lugares.
        # La precedencia evita que una cuenta Jefe+Operador
        # herede accidentalmente los permisos amplios de Operador.
        if "Jefe de departamento" in grupos:
            if "Administrador" in grupos or "Operador" in grupos:
                raise PermissionDenied(
                    "La cuenta tiene roles incompatibles. "
                    "Solicita al Superadmin corregir sus grupos."
                )

            # El inicio normal después del login lleva al panel propio.
            if nombre_ruta == "home":
                return redirect("panel_jefe")

            if nombre_ruta in RUTAS_JEFE:
                return vista(request, *args, **kwargs)

            raise PermissionDenied(
                "Este apartado no está disponible para tu rol."
            )

        # Administrador: acceso a las vistas internas.

        if "Administrador" in grupos:

            return vista(request, *args, **kwargs)

        # Operador: no puede utilizar rutas administrativas.

        if "Operador" in grupos:

            if nombre_ruta in RUTAS_ADMINISTRADOR:

                raise PermissionDenied(

                    "Esta función está reservada "

                    "para administradores."

                )

            return vista(request, *args, **kwargs)

        # Los usuarios sin rol no tienen acceso interno.

        raise PermissionDenied(

            "Tu cuenta no tiene un rol asignado."

        )

    return vista_protegida

# =========================================================

# REGISTRO DE RUTAS CON PROTECCIÓN AUTOMÁTICA

# =========================================================

def path(route, view, kwargs=None, name=None):

    vista = proteger_vista(view, name)

    return django_path(

        route,

        vista,

        kwargs=kwargs,

        name=name,

    )

# =========================================================

# URLS ORIGINALES DEL PROYECTO

# =========================================================

urlpatterns = [

    # EXCEL

    path(

        "excel/sectores/",

        views.descargar_excel_sectores,

        name="descargar_excel_sectores",

    ),

    # INICIO Y USUARIOS

    path("", views.home, name="home"),

    path("signin/", views.signin, name="signin"),

    path("signup/", views.signup, name="signup"),

    path("logout/", views.signout, name="signout"),

    # SECTORES

    path("sectores/", views.lista_sectores, name="lista_sectores"),

    path("sector/crear/", views.crear_sector, name="crear_sector"),

    path("sectores/<int:sector_id>/", views.detalle_sector, name="detalle_sector"),

    path("sectores/<int:sector_id>/editar/", views.editar_sector, name="editar_sector"),

    path("sectores/<int:sector_id>/borrar/", views.borrar_sector, name="borrar_sector"),

    # UBICACIONES

    path("ubicaciones/", views.lista_ubicaciones, name="lista_ubicaciones"),

    path("ubicacion/crear/", views.crear_ubicacion, name="crear_ubicacion"),

    path("ubicaciones/<int:ubicacion_id>/", views.detalle_ubicacion, name="detalle_ubicacion"),

    path("ubicaciones/<int:ubicacion_id>/editar/", views.editar_ubicacion, name="editar_ubicacion"),

    path("ubicaciones/<int:ubicacion_id>/borrar/", views.borrar_ubicacion, name="borrar_ubicacion"),

    # PISOS

    path("pisos/", views.lista_pisos, name="lista_pisos"),

    path("piso/crear/", views.crear_piso, name="crear_piso"),

    path("pisos/<int:piso_id>/", views.detalle_piso, name="detalle_piso"),

    path("pisos/<int:piso_id>/editar/", views.editar_piso, name="editar_piso"),

    path("pisos/<int:piso_id>/borrar/", views.borrar_piso, name="borrar_piso"),

    # LUGARES

    path("lugares/", views.lista_lugares, name="lista_lugares"),

    path("lugar/crear/", views.crear_lugar, name="crear_lugar"),

    path("lugar/<int:lugar_id>/", views.detalle_lugar, name="detalle_lugar"),

    path("lugar/<int:lugar_id>/editar/", views.editar_lugar, name="editar_lugar"),

    path("lugar/<int:lugar_id>/borrar/", views.borrar_lugar, name="borrar_lugar"),

    # OBJETOS REGISTRADOS EN LUGARES

    path("objetos-lugar/", views.lista_objetos_lugar, name="lista_objetos_lugar"),

    path("objetos-lugar/<int:objeto_lugar_id>/", views.detalle_objeto_lugar, name="detalle_objeto_lugar"),

    path("objetos-lugar/<int:objeto_lugar_id>/editar/", views.editar_objeto_lugar, name="editar_objeto_lugar"),

    path("objetos-lugar/<int:objeto_lugar_id>/borrar/", views.borrar_objeto_lugar, name="borrar_objeto_lugar"),

    path("lugar/<int:lugar_id>/objeto/crear/", views.crear_objeto_lugar, name="crear_objeto_lugar"),

    # TIPOS DE LUGAR

    path("tipo-lugar/", views.lista_tipos_lugar, name="lista_tipos_lugar"),

    path("tipo-lugar/crear/", views.crear_tipo_lugar, name="crear_tipo_lugar"),

    path("tipo-lugar/<int:tipo_lugar_id>/", views.detalle_tipo_lugar, name="detalle_tipo_lugar"),

    path("tipo-lugar/<int:tipo_lugar_id>/editar/", views.editar_tipo_lugar, name="editar_tipo_lugar"),

    path("tipo-lugar/<int:tipo_lugar_id>/borrar/", views.borrar_tipo_lugar, name="borrar_tipo_lugar"),

    # CATEGORÍAS

    path("categorias/", views.lista_categorias, name="lista_categorias"),

    path("categoria/crear/", views.crear_categoria_objeto, name="crear_categoria_objeto"),

    path("categoria/<int:categoria_id>/", views.detalle_categoria, name="detalle_categoria"),

    path("categoria/<int:categoria_id>/editar/", views.editar_categoria, name="editar_categoria"),

    path("categoria/<int:categoria_id>/borrar/", views.borrar_categoria, name="borrar_categoria"),

    # OBJETOS DEL CATÁLOGO

    path("objetos/", views.lista_objetos, name="lista_objetos"),

    path("objeto/crear/", views.crear_objeto, name="crear_objeto"),

    path("objeto/<int:objeto_id>/", views.detalle_objeto, name="detalle_objeto"),

    path("objeto/<int:objeto_id>/editar/", views.editar_objeto, name="editar_objeto"),

    path("objeto/<int:objeto_id>/borrar/", views.borrar_objeto, name="borrar_objeto"),

    # TIPOS DE OBJETO

    path("tipos-objeto/", views.lista_tipos_objeto, name="lista_tipos_objeto"),

    path("tipo-objeto/crear/", views.crear_tipo_objeto, name="crear_tipo_objeto"),

    path("tipo-objeto/<int:tipo_objeto_id>/", views.detalle_tipo_objeto, name="detalle_tipo_objeto"),

    path("tipo-objeto/<int:tipo_objeto_id>/editar/", views.editar_tipo_objeto, name="editar_tipo_objeto"),

    path("tipo-objeto/<int:tipo_objeto_id>/borrar/", views.borrar_tipo_objeto, name="borrar_tipo_objeto"),

    # HISTÓRICOS

    path("historicos/", views.lista_historicos, name="lista_historicos"),

    path("historico/", views.lista_historicos),

    path("historico/<int:historico_id>/", views.detalle_historico, name="detalle_historico"),

    path("historico/<int:historico_id>/editar/", views.editar_historico, name="editar_historico"),

    path("historico/<int:historico_id>/borrar/", views.borrar_historico, name="borrar_historico"),

    path("objetos-lugar/<int:objeto_lugar_id>/historico/crear/", views.crear_historico, name="crear_historico"),

    # ESTRUCTURA Y ESTADO GENERAL

    path("estructura/crear/", views.crear_estructura, name="crear_estructura"),

    path("resumen/", views.resumen_general, name="resumen_general"),

    # AJAX

    path("ajax/ubicaciones-por-sector/", views.ajax_ubicaciones_por_sector, name="ajax_ubicaciones_por_sector"),

    path("ajax/pisos-por-ubicacion/", views.ajax_pisos_por_ubicacion, name="ajax_pisos_por_ubicacion"),

    path("ajax/lugares-por-piso/", views.ajax_lugares_por_piso, name="ajax_lugares_por_piso"),

    path("ajax/objetos-por-categoria/", views.ajax_objetos_por_categoria, name="ajax_objetos_por_categoria"),

    path("ajax/tipos-por-objeto/", views.ajax_tipos_por_objeto, name="ajax_tipos_por_objeto"),

    path("api/objetos-tipicos/<int:tipo_lugar_pk>/", views.objetos_tipicos_por_tipo_lugar, name="objetos_tipicos_por_tipo_lugar"),

    # CARGA MASIVA

    path("carga-masiva", views.carga_masiva, name="carga_masiva"),

    path("excel/plantilla-carga-masiva/", views.descargar_plantilla_carga_masiva, name="descargar_plantilla_carga_masiva"),

    # GESTIÓN INTERNA DE INCIDENCIAS

    path(

        "incidencias/",

        incidencias_views.lista_incidencias,

        name="lista_incidencias",

    ),

    path(

        "incidencias/<int:incidencia_id>/",

        incidencias_views.detalle_incidencia,

        name="detalle_incidencia",

    ),

    path(

        "incidencias/<int:incidencia_id>/foto/",

        incidencias_views.foto_incidencia,

        name="foto_incidencia",

    ),

    # CÓDIGOS QR

    path("lugar/<int:lugar_id>/qr/", views.qr_lugar, name="qr_lugar"),

    path("consulta/qr/<str:token>/", views.consulta_qr, name="consulta_qr"),

    # SUPERADMIN: CUENTAS Y ASIGNACIONES DE JEFES (VISTAS PROTEGIDAS)
    path(
        "superadmin/jefes/",
        superadmin_jefes_views.lista_jefes,
        name="superadmin_lista_jefes",
    ),
    path(
        "superadmin/jefes/crear/",
        superadmin_jefes_views.crear_jefe,
        name="superadmin_crear_jefe",
    ),
    path(
        "superadmin/jefes/<int:usuario_id>/editar/",
        superadmin_jefes_views.editar_jefe,
        name="superadmin_editar_jefe",
    ),

    # JEFES DE DEPARTAMENTO: PANTALLAS PROPIAS CON DATOS FILTRADOS.
    path("jefe/", jefes_views.panel_jefe, name="panel_jefe"),
    path(
        "jefe/lugar/<int:lugar_id>/",
        jefes_views.detalle_lugar_jefe,
        name="detalle_lugar_jefe",
    ),

    # INVENTARIO DEL JEFE: LAS VISTAS VALIDAN LA ASIGNACIÓN EN EL SERVIDOR.
    path(
        "jefe/lugar/<int:lugar_id>/objeto/crear/",
        jefes_inventario_views.crear_objeto_jefe,
        name="jefe_crear_objeto",
    ),
    path(
        "jefe/objeto/<int:objeto_lugar_id>/editar/",
        jefes_inventario_views.editar_objeto_jefe,
        name="jefe_editar_objeto",
    ),

    # REPORTES INTERNOS DEL JEFE: solo lugares visibles y reportes propios.
    path(
        "jefe/lugar/<int:lugar_id>/reportar/",
        jefes_reportes_views.reportar_incidencia_jefe,
        name="jefe_reportar_incidencia",
    ),
    path(
        "jefe/reportes/",
        jefes_reportes_views.mis_reportes_jefe,
        name="jefe_mis_reportes",
    ),
    path(
        "jefe/reporte/<int:reporte_id>/foto/",
        jefes_reportes_views.foto_reporte_jefe,
        name="jefe_foto_reporte",
    ),

    # FILTROS DEPENDIENTES

    path("ajax/filtros-dependientes/", views.ajax_filtros_dependientes, name="ajax_filtros_dependientes"),

]
