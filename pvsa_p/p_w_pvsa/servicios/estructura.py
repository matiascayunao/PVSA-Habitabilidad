from ..models import (
    Sector,
    Ubicacion,
    Piso,
    Lugar,
    TipoLugar,
    CategoriaObjeto,
    Objeto,
    TipoObjeto,
    ObjetoLugar,
)


def _clave_estructura(valor):
    return ' '.join((valor or '').split()).casefold()

def crear_estructura_con_inventario(cd, filas):
    sector = cd.get('sector_existente')
    if not sector:
        sector = Sector.objects.create(sector=(cd.get('sector_nuevo') or '').strip())
    ubicacion = cd.get('ubicacion_existente')
    if not ubicacion:
        ubicacion = Ubicacion.objects.create(ubicacion=(cd.get('ubicacion_nueva') or '').strip(), sector=sector)
    piso = cd.get('piso_existente')
    if not piso:
        piso = Piso.objects.create(piso=cd.get('piso_nuevo'), ubicacion=ubicacion)
    tipo_lugar = cd.get('tipo_lugar_existente')
    if not tipo_lugar:
        tipo_lugar = TipoLugar.objects.create(tipo_de_lugar=(cd.get('tipo_lugar_nuevo') or '').strip())
    lugar = cd.get('lugar_existente')
    if not lugar:
        lugar = Lugar.objects.create(nombre_del_lugar=(cd.get('lugar_nuevo') or '').strip(), piso=piso, lugar_tipo_lugar=tipo_lugar, es_area_comun=cd.get('lugar_es_area_comun', False))
    categorias_creadas = {}
    objetos_creados = {}
    variantes_creadas = {}
    for row in filas:
        if not row:
            continue
        if row.get('__empty__'):
            continue
        categoria = row.get('categoria_existente')
        if not categoria:
            nombre_categoria = (row.get('categoria_nueva') or '').strip()
            clave_categoria = _clave_estructura(nombre_categoria)
            categoria = categorias_creadas.get(clave_categoria)
            if categoria is None:
                categoria = CategoriaObjeto.objects.create(nombre_de_categoria=nombre_categoria)
                categorias_creadas[clave_categoria] = categoria
        objeto = row.get('objeto_existente')
        if not objeto:
            nombre_objeto = (row.get('objeto_nuevo') or '').strip()
            clave_objeto = _clave_estructura(nombre_objeto)
            objeto = objetos_creados.get(clave_objeto)
            if objeto is None:
                objeto = Objeto.objects.create(nombre_del_objeto=nombre_objeto, objeto_categoria=categoria)
                objetos_creados[clave_objeto] = objeto
        tipo_objeto = row.get('tipo_objeto_existente')
        if not tipo_objeto:
            marca = (row.get('marca') or '').strip() or None
            material = (row.get('material') or '').strip() or None
            clave_variante = (objeto.pk, _clave_estructura(marca), _clave_estructura(material))
            tipo_objeto = variantes_creadas.get(clave_variante)
            if tipo_objeto is None:
                tipo_objeto = TipoObjeto.objects.create(objeto=objeto, marca=marca, material=material)
                variantes_creadas[clave_variante] = tipo_objeto
        ObjetoLugar.objects.create(lugar=lugar, tipo_de_objeto=tipo_objeto, cantidad=row.get('cantidad'), detalle=(row.get('detalle') or '').strip(), importancia=row.get('importancia') or 1, cantidad_mala=row.get('cantidad_mala') or 0, cantidad_pendiente=row.get('cantidad_pendiente') or 0, minimo_operativo=row.get('minimo_operativo') or 1)
    return lugar
