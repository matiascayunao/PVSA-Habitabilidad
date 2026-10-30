from django import template

register = template.Library()


@register.filter
def es_administrador_pvsa(usuario):
    """Superadmin o usuario del grupo Administrador."""
    if not usuario or not usuario.is_authenticated:
        return False

    if usuario.is_superuser:
        return True

    return usuario.groups.filter(name="Administrador").exists()


@register.filter
def es_jefe_departamento_pvsa(usuario):
    """Se usa para mostrar al jefe solo sus enlaces en las plantillas.

    Las comprobaciones de permisos siguen estando en las vistas y en urls.py.
    """
    if not usuario or not usuario.is_authenticated or usuario.is_superuser:
        return False

    return usuario.groups.filter(name="Jefe de departamento").exists()
