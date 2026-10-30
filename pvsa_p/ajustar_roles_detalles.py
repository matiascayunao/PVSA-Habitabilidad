
from pathlib import Path
import re
import shutil


# Carpeta de las plantillas del proyecto
CARPETA = (
    Path(__file__).resolve().parent
    / "p_w_pvsa"
    / "templates"
)

# Archivos que debemos modificar y sus rutas de borrado
ARCHIVOS = {
    "detalle_ubicacion.html": "borrar_ubicacion",
    "detalle_piso.html": "borrar_piso",
    "detalle_categoria.html": "borrar_categoria",
    "detalle_objeto.html": "borrar_objeto",
    "detalle_tipo_objeto.html": "borrar_tipo_objeto",
    "detalle_historico.html": "borrar_historico",
    "detalle_objeto_lugar.html": "borrar_objeto_lugar",
}


PATRONES = {
    "a": re.compile(
        r"(?P<indent>^[ \t]*)<a\b[\s\S]*?</a>",
        re.MULTILINE,
    ),
    "button": re.compile(
        r"(?P<indent>^[ \t]*)<button\b[\s\S]*?</button>",
        re.MULTILINE,
    ),
}


def ajustar(contenido, nombre_url, boton=False):

    patron = PATRONES["button" if boton else "a"]

    url_patron = re.compile(
        r"{%\s*url\s+['\"]"
        + re.escape(nombre_url)
        + r"['\"]"
    )

    encontrados = [
        m for m in patron.finditer(contenido)
        if url_patron.search(m.group())
    ]

    if len(encontrados) != 1:
        raise ValueError(
            f"Se esperaba 1 botón/enlace '{nombre_url}', "
            f"pero se encontraron {len(encontrados)}."
        )

    m = encontrados[0]
    inicio, fin = m.span()

    prefijo = contenido[:inicio]

    # No repetir el cambio si ya fue realizado.
    if re.search(
        r"{%\s*if\s+user\|es_administrador_pvsa\s*%}\s*$",
        prefijo,
    ):
        return contenido, False

    salto = "\r\n" if "\r\n" in contenido else "\n"
    ident = m.group("indent")

    # Envolver el botón con la comprobación de rol.
    bloque = (
        ident
        + "{% if user|es_administrador_pvsa %}"
        + salto
        + m.group()
        + salto
        + ident
        + "{% endif %}"
    )

    contenido = (
        contenido[:inicio]
        + bloque
        + contenido[fin:]
    )

    # Cargar el filtro de roles si todavía no existe.
    if not re.search(
        r"{%\s*load\s+[^%]*\bpvsa_roles\b[^%]*%}",
        contenido,
    ):
        extiende = re.search(
            r"{%\s*extends\s+[^%]*%}",
            contenido,
        )

        if not extiende:
            raise ValueError(
                "No se encontró la declaración extends."
            )

        pos = extiende.end()

        contenido = (
            contenido[:pos]
            + salto
            + "{% load pvsa_roles %}"
            + contenido[pos:]
        )

    return contenido, True


def main():

    if not CARPETA.is_dir():
        raise SystemExit(
            f"No existe la carpeta: {CARPETA}"
        )

    preparados = []

    # Primero validar todos los archivos.
    # Si falta alguno, no se modifica ninguno.
    for nombre_archivo, nombre_url in ARCHIVOS.items():

        encontrados = list(
            CARPETA.rglob(nombre_archivo)
        )

        if len(encontrados) != 1:
            raise SystemExit(
                f"No se encontró un único {nombre_archivo}. "
                "No se modificó ningún archivo."
            )

        archivo = encontrados[0]

        original = archivo.read_bytes().decode(
            "utf-8-sig"
        )

        try:
            cambiado, necesita_guardar = ajustar(
                original,
                nombre_url,
                boton=(
                    nombre_archivo
                    == "detalle_objeto_lugar.html"
                ),
            )

        except ValueError as error:
            raise SystemExit(
                f"Error en {nombre_archivo}: {error}. "
                "No se modificó ningún archivo."
            )

        if necesita_guardar:

            copia = archivo.with_name(
                archivo.name + ".bak_roles"
            )

            if copia.exists():
                raise SystemExit(
                    f"Ya existe la copia {copia}. "
                    "No se modificó ningún archivo."
                )

            preparados.append(
                (archivo, copia, cambiado)
            )

        else:
            print(
                f"Ya estaba protegido: {nombre_archivo}"
            )

    # Crear copias de seguridad antes de modificar.
    for archivo, copia, _ in preparados:
        shutil.copy2(archivo, copia)

    # Aplicar los cambios.
    for archivo, _, cambiado in preparados:

        archivo.write_bytes(
            cambiado.encode("utf-8")
        )

        print(
            f"Actualizado: {archivo.name}"
        )

    print(
        f"\nListo. Archivos actualizados: "
        f"{len(preparados)} de {len(ARCHIVOS)}."
    )

    print(
        "Se creó una copia .bak_roles "
        "por cada archivo modificado."
    )


if __name__ == "__main__":
    main()
