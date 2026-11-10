from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import CategoriaObjeto, Objeto, TipoObjeto


def resolver_catalogo_inventario(*, modo, objeto_existente_id, objeto_nuevo_nombre, categoria_existente_id, categoria_nueva_nombre):
    objeto = None
    categoria = None
    if modo == 'variante':
        if not objeto_existente_id.isdigit():
            raise ValidationError('Selecciona el objeto al que quieres agregar una nueva marca o material.')
        else:
            objeto = Objeto.objects.filter(pk=int(objeto_existente_id)).first()
            if not objeto:
                raise ValidationError('El objeto seleccionado ya no existe.')
    elif not objeto_nuevo_nombre:
        raise ValidationError('Escribe el nombre del nuevo objeto.')
    else:
        objeto = Objeto.objects.filter(nombre_del_objeto__iexact=objeto_nuevo_nombre).first()
        if not objeto:
            if categoria_existente_id.isdigit():
                categoria = CategoriaObjeto.objects.filter(pk=int(categoria_existente_id)).first()
                if not categoria:
                    raise ValidationError('La categoría seleccionada ya no existe.')
            elif categoria_nueva_nombre:
                categoria = CategoriaObjeto.objects.filter(nombre_de_categoria__iexact=categoria_nueva_nombre).first()
            else:
                raise ValidationError('Selecciona una categoría o escribe una nueva.')
    return (objeto, categoria)

def obtener_o_crear_variante(*, objeto, categoria, objeto_nuevo_nombre, categoria_nueva_nombre, marca, material):
    campos = [(TipoObjeto, 'marca', marca), (TipoObjeto, 'material', material)]
    if not objeto:
        campos.append((Objeto, 'nombre_del_objeto', objeto_nuevo_nombre))
        if not categoria:
            campos.append((CategoriaObjeto, 'nombre_de_categoria', categoria_nueva_nombre))
    errores = []
    for modelo, nombre, valor in campos:
        campo = modelo._meta.get_field(nombre)
        try:
            campo.clean(valor, None)
        except ValidationError as error:
            errores.extend(f'{campo.verbose_name}: {mensaje}' for mensaje in error.messages)
    if errores:
        raise ValidationError(errores)
    if not objeto:
        if not categoria:
            categoria = CategoriaObjeto.objects.create(nombre_de_categoria=categoria_nueva_nombre)
        objeto = Objeto.objects.create(nombre_del_objeto=objeto_nuevo_nombre, objeto_categoria=categoria)
    tipos_qs = TipoObjeto.objects.filter(objeto=objeto)
    if marca:
        tipos_qs = tipos_qs.filter(marca__iexact=marca)
    else:
        tipos_qs = tipos_qs.filter(Q(marca__isnull=True) | Q(marca__exact=''))
    if material:
        tipos_qs = tipos_qs.filter(material__iexact=material)
    else:
        tipos_qs = tipos_qs.filter(Q(material__isnull=True) | Q(material__exact=''))
    tipo_objeto = tipos_qs.first()
    if not tipo_objeto:
        tipo_objeto = TipoObjeto.objects.create(objeto=objeto, marca=marca, material=material)
    return tipo_objeto
