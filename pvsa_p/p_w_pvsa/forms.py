from django.forms import ModelForm, formset_factory
from django import forms
from .models import (
    Sector,
    Ubicacion,
    Piso,
    Lugar,
    TipoLugar,
    TipoObjeto,
    CategoriaObjeto,
    ObjetoLugar,
    Objeto,
    HistoricoObjeto,
)

from .formularios.estructura import (
    _normalizar_nombre,
    CrearSector,
    CrearUbicacion,
    CrearPiso,
    EditarSector,
    EditarUbicacion,
    EditarPiso,
    EstructuraCompletaForm,
    ObjetoLugarFilaForm,
    ObjetoLugarFilaFormSet,
)

from .formularios.lugares import (
    CrearLugar,
    CrearTipoLugar,
    EditarTipoLugar,
    EditarLugar,
)

from .formularios.categorias import (
    CrearCategoriaObjeto,
    CrearObjeto,
    CrearTipoObjeto,
    EditarCategoria,
    EditarObjeto,
    EditarTipoObjeto,
)

from .formularios.inventario import (
    CrearObjetoLugar,
    CrearHistorico,
    EditarObjetoLugar,
    EditarHistorico,
)