"""Consultas seguras de lugares para jefes de departamento.

El QR público/privado no define los permisos de un jefe.
Un área común nunca se administra como lugar propio.
"""

from django.db.models import Q

from .models import AsignacionLugarJefe, Lugar


def es_jefe_departamento(usuario):
    """Rol jefe sin privilegios heredados de otros grupos."""
    if not usuario or not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return False
    grupos = set(usuario.groups.values_list("name", flat=True))
    return (
        "Jefe de departamento" in grupos
        and "Administrador" not in grupos
        and "Operador" not in grupos
    )


def lugares_propios_jefe(usuario):
    """Solo los lugares privados/no comunes asignados directamente."""
    if not es_jefe_departamento(usuario):
        return Lugar.objects.none()

    ids = AsignacionLugarJefe.objects.filter(
        usuario=usuario,
        lugar__es_area_comun=False,
    ).values("lugar_id")
    return Lugar.objects.filter(pk__in=ids, es_area_comun=False)


def lugares_visibles_jefe(usuario):
    """Propios + comunes de ubicaciones donde tiene lugares propios.

    No da acceso a otras oficinas de esa ubicación, ni usa visibilidad_qr.
    """
    if not es_jefe_departamento(usuario):
        return Lugar.objects.none()

    asignaciones = AsignacionLugarJefe.objects.filter(
        usuario=usuario,
        lugar__es_area_comun=False,
    )
    ids_propios = asignaciones.values("lugar_id")
    ubicaciones = asignaciones.values("lugar__piso__ubicacion_id")

    return Lugar.objects.filter(
        Q(pk__in=ids_propios, es_area_comun=False)
        | Q(es_area_comun=True, piso__ubicacion_id__in=ubicaciones)
    ).distinct()


def puede_editar_inventario_jefe(usuario, lugar):
    """No dar escritura sobre comunes, aunque exista una asignación antigua."""
    if not es_jefe_departamento(usuario) or lugar.es_area_comun:
        return False
    return AsignacionLugarJefe.objects.filter(
        usuario=usuario,
        lugar=lugar,
    ).exists()
