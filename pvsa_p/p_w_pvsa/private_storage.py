
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class EvidenciaPrivadaStorage(FileSystemStorage):
    """
    Guarda fotografías de incidencias fuera de MEDIA_ROOT.
    No permite generar enlaces públicos a las imágenes.
    """

    def __init__(self):
        super().__init__(
            location=Path(settings.BASE_DIR) / "pvsa_evidencias_privadas",
            base_url=None,
        )

    def url(self, name):
        raise ValueError(
            "Las evidencias privadas no tienen una URL pública."
        )
