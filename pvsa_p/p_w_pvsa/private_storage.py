
from pathlib import Path
import posixpath
import tempfile

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


class GuardadoEvidencia:
    def __init__(self, storage):
        self.storage = storage
        self.directorios = []

    def __getattr__(self, nombre):
        return getattr(self.storage, nombre)

    def save(self, name, content, max_length=None):
        carpeta = posixpath.dirname(name)
        raiz = Path(self.storage.path(carpeta)).resolve()
        raiz.mkdir(parents=True, exist_ok=True)
        directorio = Path(tempfile.mkdtemp(prefix="foto_", dir=raiz)).resolve()
        self.directorios.append(directorio)
        nombre = posixpath.join(carpeta, directorio.name, posixpath.basename(name))
        return self.storage.save(nombre, content, max_length=max_length)

    def limpiar(self):
        raiz = Path(self.storage.location).resolve()
        for directorio in self.directorios:
            directorio.relative_to(raiz)
            for archivo in directorio.rglob("*"):
                if archivo.is_file():
                    self.storage.delete(archivo.relative_to(raiz).as_posix())
            for carpeta in sorted(directorio.rglob("*"), key=lambda ruta: len(ruta.parts), reverse=True):
                if carpeta.is_dir():
                    carpeta.rmdir()
            directorio.rmdir()


@deconstructible
class EvidenciaPrivadaStorage(FileSystemStorage):
    """
    Guarda fotografías de incidencias fuera de MEDIA_ROOT.
    No permite generar enlaces públicos a las imágenes.
    """

    def __init__(self):
        super().__init__(
            location=getattr(settings, "PRIVATE_EVIDENCE_ROOT", Path(settings.BASE_DIR) / "pvsa_evidencias_privadas"),
            base_url=None,
        )

    def url(self, name):
        raise ValueError(
            "Las evidencias privadas no tienen una URL pública."
        )
