# PVSA

PVSA permite administrar inventarios por sector, ubicaci?n, piso y lugar, conservar su historial y gestionar incidencias con evidencia privada. El usuario final utiliza un navegador y sus credenciales; la instalaci?n y el mantenimiento corresponden al administrador del servidor.

## Requisitos

- Python 3.12?3.14 compatible con Django 6.0 y un entorno virtual.
- SQLite y almacenamiento persistente con permisos para la cuenta del servicio. Las migraciones incluyen restricciones y triggers espec?ficos de SQLite.
- Para producci?n: dominio o IP, certificado HTTPS, proxy y servidor WSGI compatibles con el hosting, y respaldo verificado.
- Acceso desde los navegadores a jsDelivr, usado para Bootstrap e iconos.

## Instalaci?n

Desde la ra?z del repositorio:

```text
python -m venv .venv
```

Activar con `.venv\Scripts\activate` en Windows o `source .venv/bin/activate` en Linux/macOS. Despu?s:

```text
python -m pip install -r requirements.txt
```

El manifiesto re?ne las dependencias directas verificadas. El administrador instala adem?s el servidor WSGI que corresponda a su plataforma; `runserver` se limita al desarrollo.

## Configuraci?n y arranque

Existe una ?nica configuraci?n: `mysite.settings`, y una entrada WSGI: `mysite.wsgi:application`. Se conserva tambi?n `mysite.asgi:application`. Las variables se definen en el entorno del proceso; no se cargan archivos `.env` autom?ticamente. No guardar secretos en Git.

En desarrollo, `PVSA_ENV=development` es el valor predeterminado. Definir `DJANGO_SECRET_KEY` con una clave propia y estable. Se conserva la base local `pvsa_p/db.sqlite3`, los hosts locales existentes y `DJANGO_DEBUG` (predeterminado `True`). No se fuerzan HTTPS ni cookies seguras en este modo.

```text
python pvsa_p/manage.py check
python pvsa_p/manage.py migrate --plan
python pvsa_p/manage.py migrate
python pvsa_p/manage.py runserver
```

Revisar y respaldar antes de aplicar migraciones sobre una instalaci?n existente. Para una instalaci?n nueva, el administrador puede crear su cuenta con `python pvsa_p/manage.py createsuperuser`. No restablecer usuarios existentes.

### Producci?n

Definir estas variables en el servicio antes de iniciar sus procesos:

| Variable | Configuraci?n |
|---|---|
| `PVSA_ENV` | `production` |
| `DJANGO_SETTINGS_MODULE` | `mysite.settings` |
| `DJANGO_SECRET_KEY` | Clave aleatoria estable de al menos 50 caracteres; no usar claves `django-insecure-`. |
| `PVSA_ALLOWED_HOSTS` | Dominios o IPv4 expl?citos separados por comas, sin esquema, puerto ni comodines. |
| `PVSA_DATA_ROOT` | Directorio absoluto persistente y privado para `db.sqlite3`, `pvsa_evidencias_privadas` y `media`. |
| `PVSA_STATIC_ROOT` | Directorio absoluto p?blico destinado exclusivamente a `collectstatic`. |

C?digo, datos y est?ticos deben estar separados, sin contenerse entre s?. Se rechazan rutas relativas, rutas que identifican archivos y configuraciones obligatorias ausentes. Producci?n fuerza `DEBUG=False`, HTTPS, cookies seguras y almacenamiento est?tico con manifiesto, aunque exista `DJANGO_DEBUG=True` en el entorno.

`PVSA_CSRF_TRUSTED_ORIGINS` es opcional: or?genes HTTPS expl?citos separados por comas, solo cuando el despliegue los requiera. El mismo origen no necesita excepciones.

`PVSA_TRUST_PROXY_HTTPS` vale `false`. Activarlo solo si un proxy confiable elimina el encabezado `X-Forwarded-Proto` del cliente y establece su propio valor, y el backend no es accesible directamente.

`PVSA_HSTS_SECONDS` vale `0`. Mantenerlo as? hasta verificar dominio, certificado, HTTPS y renovaci?n. Despu?s habilitarlo gradualmente. Subdominios y preload permanecen desactivados. `check --deploy` advierte de HSTS mientras est? pendiente; no ocultar esa advertencia.

Con `PVSA_ENV=production` y las variables anteriores ya definidas:

```text
python pvsa_p/manage.py check
python pvsa_p/manage.py migrate --plan
python pvsa_p/manage.py migrate
python pvsa_p/manage.py collectstatic --noinput
python pvsa_p/manage.py check --deploy
```

No se ejecutan migraciones al importar WSGI. Configurar su ruta de importaci?n con `pvsa_p`, iniciar `mysite.wsgi:application` y publicar ?nicamente `PVSA_STATIC_ROOT` en `/static/`. No publicar c?digo, base, directorios de datos ni evidencias. Las fotograf?as se sirven mediante vistas autenticadas; no requieren una ruta p?blica `/media/`.

Para trasladar una instalaci?n existente, detener la aplicaci?n y respaldar conjuntamente base, evidencias y secretos. Colocar los datos bajo `PVSA_DATA_ROOT`, conservando los nombres relativos de las fotograf?as y los tokens existentes. No iniciar accidentalmente sobre un directorio vac?o. Comprobar permisos, restauraci?n y funcionamiento desde la red de usuarios.

## Funcionalidades y roles

- Estructura de sectores, ubicaciones, pisos y lugares; cat?logo de objetos y variantes.
- Inventarios con cantidades, estado, m?nimos operativos y resumen de operatividad.
- Hist?ricos con identidad de variantes conservada aunque desaparezcan del cat?logo.
- QR p?blicos para reportar incidencias y privados con autenticaci?n y autorizaci?n.
- Incidencias con fotograf?as privadas y gesti?n interna.
- Importaci?n Excel con previsualizaci?n y confirmaci?n, y exportaci?n de inventarios.

El Superadmin gestiona cuentas y asignaciones. Mini-Admin usa el grupo `Administrador` y accede a funciones administrativas, sin gestionar jefes. El Operador dispone de funciones internas no administrativas. El Jefe de departamento trabaja en sus vistas y lugares autorizados. Las cuentas con roles incompatibles son rechazadas. El visitante an?nimo accede al login y a QR p?blicos habilitados.

## Organizaci?n

`pvsa_p/mysite/` contiene configuraci?n, URL ra?z, WSGI y ASGI. `pvsa_p/p_w_pvsa/` contiene las fachadas Django y los m?dulos `administracion`, `formularios`, `modelos`, `servicios` y `vistas`, adem?s de plantillas, est?ticos fuente, permisos, almacenamiento privado y migraciones. `staticfiles/` es una salida regenerable de `collectstatic`, no una fuente editable. Las herramientas temporales de QA se mantienen en un archivo externo y no son requisitos del usuario final.

## Seguridad y operaci?n

El cierre de sesi?n exige POST y CSRF. Los permisos se verifican en el servidor, incluidas las rutas directas y las fotograf?as. `private_storage.py` impide generar URL p?blicas de evidencias. No exponer su directorio en el servidor web.

Respaldar base y fotograf?as de forma coherente, proteger los secretos y ensayar la restauraci?n. Mantener dependencias y sistema operativo actualizados, registrar errores y supervisar el servicio. El limitador de reportes QR utiliza cach? local; con varios procesos se requiere protecci?n adicional de frecuencia en el servidor.

Quedan a cargo del despliegue definitivo: dominio, certificado y renovaciones, hosting y WSGI, proxy HTTPS, directorios persistentes y permisos, respaldos y restauraci?n, y lectura de QR con un dispositivo real. La preparaci?n del c?digo no sustituye estas comprobaciones.
