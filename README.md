# PVSA

PVSA permite administrar inventarios por sector, ubicación, piso y lugar, conservar su historial y gestionar incidencias con evidencia privada. El usuario final utiliza un navegador y sus credenciales; la instalación y el mantenimiento corresponden al administrador del servidor.

## Requisitos

- Git para clonar el repositorio.
- Python 3.12–3.14 compatible con Django 6.0 y un entorno virtual.
- SQLite y almacenamiento persistente con permisos para la cuenta del servicio. Las migraciones incluyen restricciones y triggers específicos de SQLite.
- Para producción: dominio o IP, certificado HTTPS, proxy y servidor WSGI compatibles con el hosting, y respaldo verificado.
- Acceso desde los navegadores a jsDelivr, usado para Bootstrap e iconos.

## Instalación

Clonar la rama del proyecto y entrar en el directorio creado:

```text
git clone --branch refactor/arquitectura-modular https://github.com/matiascayunao/p_-main.git pvsa
cd pvsa
```

Desde esa raíz, con la versión de Python indicada:

```text
python -m venv .venv
```

Activar según la terminal:

| Terminal | Comando |
|---|---|
| PowerShell | `.\.venv\Scripts\Activate.ps1` |
| CMD | `.venv\Scripts\activate.bat` |
| Bash en Linux/macOS | `source .venv/bin/activate` |

Si la política de PowerShell impide activar, se puede utilizar `.\.venv\Scripts\python.exe` en lugar de `python` en los comandos siguientes, sin cambiar la política global. Después:

```text
python -m pip install -r requirements.txt
```

El manifiesto reúne las dependencias directas verificadas. El administrador instala además el servidor WSGI que corresponda a su plataforma; `runserver` se limita al desarrollo.

## Configuración y arranque

Existe una única configuración: `mysite.settings`, y una entrada WSGI: `mysite.wsgi:application`. Se conserva también `mysite.asgi:application`. Las variables se definen en el entorno del proceso; no se cargan archivos `.env` automáticamente. No guardar secretos en Git.

En desarrollo, `PVSA_ENV=development` es el valor predeterminado. Definir `DJANGO_SECRET_KEY` con una clave propia y estable. Se conserva la base local `pvsa_p/db.sqlite3`, los hosts locales existentes y `DJANGO_DEBUG` (predeterminado `True`). No se fuerzan HTTPS ni cookies seguras en este modo.

Para una instalación nueva, estos ejemplos generan una clave sin mostrarla en la terminal. Ejecutar solo el bloque correspondiente:

```powershell
$env:PVSA_ENV = "development"
$env:DJANGO_DEBUG = "True"
$env:DJANGO_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(64))"
$env:PVSA_LOGIN_PROTECTION_ENABLED = "true"
```

```bash
export PVSA_ENV=development
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
export PVSA_LOGIN_PROTECTION_ENABLED=true
```

Las variables anteriores duran esta sesión de terminal. Conservar la clave en un gestor de secretos o configuración privada del servicio y cargar el mismo valor en sesiones posteriores; no regenerarla en cada arranque ni ejecutar estos ejemplos sobre una instalación existente. No guardarla en el repositorio ni incluirla en capturas o informes. Una clave nueva invalida las firmas y sesiones que dependan de la anterior.

Preparar el almacenamiento privado local con permisos de lectura y escritura para la cuenta que ejecutará PVSA:

```text
python -c "from pathlib import Path; Path('pvsa_p/pvsa_evidencias_privadas').mkdir(parents=True, exist_ok=True)"
```

En una instalación nueva, ejecutar en este orden:

```text
python pvsa_p/manage.py check
python pvsa_p/manage.py migrate --plan
python pvsa_p/manage.py migrate
python pvsa_p/manage.py createsuperuser
python pvsa_p/manage.py runserver
```

Abrir `http://127.0.0.1:8000/` y configurar los roles descritos más abajo. `createsuperuser` solicita las credenciales del primer Superadmin de forma interactiva; elegir una contraseña propia que cumpla los validadores. No restablecer usuarios existentes.

Clonar GitHub no copia la SQLite local, inventarios, fotografías, cuentas ni registros QA: una instalación nueva comienza sin esos datos. En una instalación existente, revisar y respaldar antes de migrar. Para recuperar datos, seguir la sección de restauración antes de iniciar el servidor o crear una base vacía.

### Producción

Definir estas variables en el servicio antes de iniciar sus procesos:

| Variable | Configuración |
|---|---|
| `PVSA_ENV` | `production` |
| `DJANGO_SETTINGS_MODULE` | `mysite.settings` |
| `DJANGO_SECRET_KEY` | Clave aleatoria estable de al menos 50 caracteres; no usar claves `django-insecure-`. |
| `PVSA_ALLOWED_HOSTS` | Dominios o IPv4 explícitos separados por comas, sin esquema, puerto ni comodines. |
| `PVSA_DATA_ROOT` | Directorio absoluto persistente y privado para `db.sqlite3`, `pvsa_evidencias_privadas` y `media`. |
| `PVSA_STATIC_ROOT` | Directorio absoluto público destinado exclusivamente a `collectstatic`. |

Código, datos y estáticos deben estar separados, sin contenerse entre sí. Se rechazan rutas relativas, rutas que identifican archivos y configuraciones obligatorias ausentes. Producción fuerza `DEBUG=False`, HTTPS, cookies seguras y almacenamiento estático con manifiesto, aunque exista `DJANGO_DEBUG=True` en el entorno.

`PVSA_CSRF_TRUSTED_ORIGINS` es opcional: orígenes HTTPS explícitos separados por comas, solo cuando el despliegue los requiera. El mismo origen no necesita excepciones.

`PVSA_TRUST_PROXY_HTTPS` vale `false`. Activarlo solo si un proxy confiable elimina el encabezado `X-Forwarded-Proto` del cliente y establece su propio valor, y el backend no es accesible directamente.

`PVSA_HSTS_SECONDS` vale `0`. Mantenerlo así hasta verificar dominio, certificado, HTTPS y renovación. Después habilitarlo gradualmente. Subdominios y preload permanecen desactivados. `check --deploy` advierte de HSTS mientras está pendiente; no ocultar esa advertencia.

Definir las variables en el entorno del servicio elegido, con la misma clave estable para todos sus procesos. Los nombres `PVSA_DATA_ROOT` y `PVSA_STATIC_ROOT` no cambian las rutas de desarrollo: solo se aplican en producción. Crear los directorios, fuera del checkout y de cualquier raíz web que exponga datos privados, con permisos limitados a la cuenta del servicio y administradores autorizados. Con las variables de producción ya definidas, se pueden preparar así:

```text
python -c "import os; from pathlib import Path; d=Path(os.environ['PVSA_DATA_ROOT']); s=Path(os.environ['PVSA_STATIC_ROOT']); [p.mkdir(parents=True, exist_ok=True) for p in (d, d/'pvsa_evidencias_privadas', d/'media', s)]"
```

Comprobar primero que las rutas absolutas elegidas cumplen la separación anterior. En una instalación nueva de producción:

```text
python pvsa_p/manage.py check
python pvsa_p/manage.py migrate --plan
python pvsa_p/manage.py migrate
python pvsa_p/manage.py createsuperuser
python pvsa_p/manage.py collectstatic --noinput
python pvsa_p/manage.py check --deploy
```

No volver a crear el Superadmin si se trasladó una base existente. No se ejecutan migraciones al importar WSGI/ASGI. Configurar la ruta de importación con `pvsa_p` e iniciar `mysite.wsgi:application` o `mysite.asgi:application` con un servidor compatible con la plataforma elegida. Publicar únicamente `PVSA_STATIC_ROOT` en `/static/`. No publicar código, base, directorios de datos ni evidencias. Las fotografías se sirven mediante vistas autenticadas; no requieren una ruta pública `/media/`.

Para trasladar una instalación existente, detener la aplicación y respaldar conjuntamente base, evidencias y secretos. Colocar los datos bajo `PVSA_DATA_ROOT`, conservando los nombres relativos de las fotografías y los tokens existentes. No iniciar accidentalmente sobre un directorio vacío. Comprobar permisos, restauración y funcionamiento desde la red de usuarios.

## Funcionalidades y roles

- Estructura de sectores, ubicaciones, pisos y lugares; catálogo de objetos y variantes.
- Inventarios con cantidades, estado, mínimos operativos y resumen de operatividad.
- Históricos con identidad de variantes conservada aunque desaparezcan del catálogo.
- QR públicos para reportar incidencias y privados con autenticación y autorización.
- Incidencias con fotografías privadas y gestión interna.
- Importación Excel con previsualización y confirmación, y exportación de inventarios.

| Perfil | Asignación y alcance |
|---|---|
| Superadmin | Cuenta activa con `is_superuser=True`; el primer `createsuperuser` también habilita `is_staff` para Django Admin. Gestiona cuentas y asignaciones. No necesita un grupo llamado «Superadmin». |
| Mini-Admin | Grupo exacto `Administrador`. Funciones administrativas de PVSA, sin gestión de jefes ni creación de cuentas. |
| Jefe de departamento | Grupo exacto `Jefe de departamento` y asignaciones de lugares propios. Consulta comunes de las ubicaciones autorizadas, sin administrarlos. Históricos de solo lectura con lugar actual y origen comprobable autorizados; los antiguos sin origen permanecen disponibles para administración. |
| Operador | Grupo exacto `Operador`. Consulta interna, sin modificaciones administrativas. Puede utilizar los reportes QR habilitados. |
| Visitante anónimo | Sin cuenta ni grupo. Login y QR públicos habilitados, sin inventario interno ni fotografías privadas. |

### Inicialización y asignación de roles

Las migraciones crean las tablas y los permisos Django estándar, pero no inicializan los tres grupos de negocio. En una instalación nueva, entrar como Superadmin en `/admin/`:

1. En **Autenticación y autorización → Grupos** (`/admin/auth/group/`), crear únicamente los grupos que falten: `Administrador`, `Operador` y `Jefe de departamento`, respetando espacios y mayúsculas. Dejar vacío el selector de permisos Django.
2. Para Mini-Admin y Operador, entrar en **Usuarios** (`/admin/auth/user/`), añadir una cuenta con contraseña propia y, después de guardarla, editar sus permisos. Mantener **Activo**, asignar únicamente el grupo correspondiente y dejar desmarcados **Es staff** y **Estado de superusuario**. No asignar permisos individuales. Para una cuenta existente, editar esa cuenta y revisar sus privilegios previos; no crear un duplicado ni cambiar su contraseña por este motivo.
3. Para un Jefe nuevo, utilizar `/superadmin/jefes/crear/`, completar su formulario y seleccionar sus lugares propios no comunes. Este mecanismo crea el grupo `Jefe de departamento` si falta y guarda las asignaciones; no es necesario otorgarle privilegios de Django Admin. Gestionar cambios de lugares desde `/superadmin/jefes/`.
4. Si se habilita como Jefe una cuenta ya existente, el Superadmin debe revisar primero que no sea superusuario ni conserve otros privilegios, asignarle solo `Jefe de departamento` desde Django Admin y después abrirla en `/superadmin/jefes/` para definir sus lugares. No asignar áreas comunes como propias.
5. Comprobar la entrada con la cuenta destinataria y el alcance de sus pantallas. Una cuenta creada en Usuarios o mediante el formulario general de registro no recibe automáticamente un rol: sin grupo reconocido no tiene acceso interno. Un Jefe sin asignaciones tampoco tiene lugares propios habilitados.

Los permisos de negocio se verifican en las rutas, vistas y servicios de PVSA, y las asignaciones se comprueban en el servidor. Agregar permisos Django arbitrariamente no inicializa estos roles. `is_staff` habilita la entrada al sitio Django Admin y no equivale a Mini-Admin; `is_superuser` concede privilegios mucho más amplios. No combinar roles: Jefe con `Administrador` u `Operador` es rechazado; `Administrador` tiene precedencia sobre `Operador` en las cuentas que conserven ambos.

## Organización

`pvsa_p/mysite/` contiene configuración, URL raíz, WSGI y ASGI. `pvsa_p/p_w_pvsa/` contiene las fachadas Django y los módulos `administracion`, `formularios`, `modelos`, `servicios` y `vistas`, además de plantillas, estáticos fuente, permisos, almacenamiento privado y migraciones. `staticfiles/` es una salida regenerable de `collectstatic`, no una fuente editable. Las herramientas temporales de QA se mantienen en un archivo externo y no son requisitos del usuario final.

## Seguridad y operación

El cierre de sesión exige POST y CSRF. Los permisos se verifican en el servidor, incluidas las rutas directas y las fotografías. `private_storage.py` impide generar URL públicas de evidencias. No exponer su directorio en el servidor web.

Respaldar base y fotografías de forma coherente, proteger los secretos y ensayar la restauración. Mantener dependencias y sistema operativo actualizados, registrar errores y supervisar el servicio. El limitador de reportes QR utiliza caché local; con varios procesos se requiere protección adicional de frecuencia en el servidor.

La protección de login descrita a continuación cubre `/signin/`, `/accounts/login/` y `/admin/login/`. Definir además cómo el servidor recoge y rota los errores de Django y del proceso, quién recibe alertas, cómo reinicia el servicio y quién aplica actualizaciones. `LOGGING` y `ADMINS` no tienen configuración propia; no asumir que ya existen archivos de log persistentes o alertas por correo. Las copias automáticas necesitan programación, supervisión de fallos y una política de retención y recuperación. Elegir esos mecanismos según el entorno definitivo.

SMTP no es necesario para inventarios e incidencias. Si se ofrece recuperación de contraseña por las rutas de `/accounts/` o correo de alertas, configurar y comprobar ese servicio antes de ofrecerlo. Revisar las cuentas de prueba y la duración de sesiones según el uso previsto. No eliminar QA ni restablecer contraseñas como parte de la instalación o actualización.

### Protección de los inicios de sesión

Se utiliza `django-axes==9.0.0`, compatible con Django 6.0 y Python 3.12–3.14. Su backend de control se ejecuta antes de `ModelBackend`, que conserva la autenticación y los permisos existentes. Los intentos se comparten entre las tres rutas y se almacenan en tablas `axes_*` de la misma SQLite que utiliza la instalación, no en la caché local por proceso. Las sesiones continúan en las tablas estándar de Django. No se necesitan Redis ni cambios en los modelos de negocio.

| Variable | Política |
|---|---|
| `PVSA_LOGIN_PROTECTION_ENABLED` | `true` o `false`. Desarrollo usa `false` si se omite, para permitir preparar las tablas antes de activar una instalación existente. Producción usa `true` y rechaza desactivarla. Los ejemplos de instalación nueva la habilitan explícitamente. |
| `PVSA_LOGIN_FAILURE_LIMIT` | Entero positivo; predeterminado `5`. |
| `PVSA_LOGIN_COOLOFF_MINUTES` | Entero positivo; predeterminado `15`. No se admite bloqueo permanente. |

Se cuentan fallos por combinación **nombre de usuario e IP de conexión (`REMOTE_ADDR`)**. Un éxito previo al límite reinicia los fallos de esa combinación; una pausa completa del tiempo configurado también permite empezar de nuevo. Al alcanzar el límite se responde HTTP 429 con un mensaje genérico y `Retry-After`. Durante la restricción tampoco se admite una contraseña correcta; los intentos bloqueados no prolongan el plazo. El formulario permanece accesible por GET. No se cambia `is_active` ni se distingue en el mensaje entre una cuenta existente y una inexistente.

Otras cuentas de la misma IP conservan su acceso, y el mismo usuario desde otra IP constituye otra combinación. No se usa `User-Agent` para eludir el contador ni se confía en `X-Forwarded-For`, `X-Real-IP` o `Forwarded`. Detrás de un proxy, Django puede ver la IP del proxy: definir con el responsable del despliegue una identidad de cliente fiable antes de cambiar esa política; nunca confiar directamente en encabezados enviados por el navegador. La protección de la combinación no sustituye límites de tráfico o defensa frente a ataques distribuidos y pruebas de muchas cuentas desde el servidor frontal.

Solo se guardan identificadores y contadores temporales necesarios, sin cuerpos GET/POST, contraseñas, tokens CSRF, `next`, `User-Agent` ni `Accept`. Se deshabilitan los registros adicionales de éxitos y fallos de Axes y su interfaz administrativa. Los intentos vencidos se limpian al procesar eventos posteriores de autenticación. Proteger también estas tablas en copias y almacenamiento. CSRF, logout y la validación de `next` permanecen en Django/PVSA.

Para una instalación existente, detener el servicio y obtener antes un respaldo actualizado. Tras instalar `requirements.txt`, revisar y aplicar **solo con autorización sobre esa base** las diez migraciones suministradas por Axes:

```text
python pvsa_p/manage.py migrate axes --plan
python pvsa_p/manage.py migrate axes
```

Las migraciones de Axes crean y ajustan sus tablas; no sustituyen usuarios ni alteran inventarios, fotografías o permisos PVSA. No fueron aplicadas sobre la base activa durante la implementación. En una instalación nueva, el `migrate` general ya las incluye. No habilitar el control antes de disponer de las tablas: no existe una omisión automática del límite ante errores de base de datos.

Después de migrar, establecer `PVSA_LOGIN_PROTECTION_ENABLED=true` en el entorno de todos los procesos y reiniciarlos. En PowerShell puede definirse para la terminal actual con `$env:PVSA_LOGIN_PROTECTION_ENABLED = "true"`; en Bash, con `export PVSA_LOGIN_PROTECTION_ENABLED=true`. Ejecutar `python pvsa_p/manage.py check` y comprobar el comportamiento en QA aislada. Los valores de umbral y espera deben ser iguales en todos los trabajadores.

Varios procesos que acceden a la misma base comparten el contador y no lo reinician al arrancar. SQLite serializa las escrituras y puede presentar contención bajo carga; esta medida no sustituye protección de tráfico en el frontal. Varias máquinas con bases SQLite independientes no comparten límites: ese despliegue exige un almacenamiento realmente centralizado y validado, sin improvisar un archivo SQLite sobre una carpeta de red. No se ha elegido servidor ni instalado infraestructura de producción.

## Respaldo y restauración

Los bloques siguientes son ejemplos operativos revisados contra las rutas y modelos del proyecto; no se ejecutaron al actualizar esta documentación. La instalación limpia y una restauración con fotografías ya cuentan con evidencia previa, pero eso no valida automáticamente nuevas rutas, permisos o servicios de otro equipo. Ensayar el procedimiento en recuperación aislada antes de adoptarlo como rutina.

### Preparación y respaldo coherente

1. Identificar el checkout y el commit desplegados, las variables del servicio y las rutas efectivas. En desarrollo la base es `pvsa_p/db.sqlite3` y las evidencias están en `pvsa_p/pvsa_evidencias_privadas`; en producción están bajo `PVSA_DATA_ROOT`. Conservar por separado, mediante un canal privado, `DJANGO_SECRET_KEY` y la configuración del servicio. El ejemplo no copia secretos ni código; conservar el commit y archivar aparte cualquier cambio local necesario para reproducirlo.
2. Detener todos los procesos que puedan escribir: servidor, trabajadores, tareas programadas y sesiones administrativas de consola. Mantener la parada durante la copia de base y archivos. La API de respaldo de SQLite obtiene una base coherente, pero no sincroniza por sí sola las fotografías con una aplicación que continúa escribiendo.
3. Elegir un directorio absoluto **nuevo y privado**, fuera del checkout, datos, estáticos y directorios publicados por el servidor web. Usar un padre privado con permisos restrictivos que herede la copia; contendrá hashes de contraseñas, datos personales y fotografías. No reutilizar ni sobrescribir respaldos verificados. Preparar el directorio de evidencias de origen si se trata de una instalación aún sin fotografías, según las instrucciones de instalación; no crear ni reemplazar una base de origen ausente.
4. Desde la raíz del checkout y con las variables de la instalación detenida, abrir una consola Django:

```text
python pvsa_p/manage.py shell -i python
```

Pegar el bloque completo. Solicita la ruta nueva del respaldo; debe introducirse sin comillas:

```python
exec(r"""
import hashlib
import json
import sqlite3
import subprocess
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from django.conf import settings
from p_w_pvsa.modelos.estructura import clave_normalizada

db = Path(settings.DATABASES['default']['NAME']).resolve()
private = Path(getattr(settings, 'PRIVATE_EVIDENCE_ROOT', settings.BASE_DIR / 'pvsa_evidencias_privadas')).resolve()
media = Path(settings.MEDIA_ROOT).resolve() if settings.MEDIA_ROOT else None
target = Path(input('Directorio absoluto NUEVO del respaldo: ')).expanduser()
if not target.is_absolute():
    raise ValueError('La ruta debe ser absoluta.')
target = target.resolve()
roots = [settings.BASE_DIR.parent.resolve(), db.parent, private, Path(settings.STATIC_ROOT).resolve()]
if media is not None:
    roots.append(media)
if target.exists() or any(target.is_relative_to(p) or p.is_relative_to(target) for p in roots):
    raise ValueError('El destino debe ser nuevo y estar separado del código y almacenamiento.')
if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3' or not db.is_file():
    raise ValueError('No se encontró la SQLite de origen; revisar configuración.')
for folder in [private] + ([media] if media is not None else []):
    if not folder.is_dir() or any(p.is_symlink() for p in folder.rglob('*')):
        raise ValueError('Revisar el directorio de archivos y sus enlaces antes de respaldar.')
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
(target / 'data').mkdir(parents=True)
with closing(sqlite3.connect(db.as_uri() + '?mode=ro', uri=True)) as source:
    with closing(sqlite3.connect(target / 'data' / 'db.sqlite3')) as dest:
        source.backup(dest)
        dest.execute('PRAGMA journal_mode=DELETE')
        dest.create_function('PVSA_CLAVE', 1, clave_normalizada, deterministic=True)
        if dest.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Falló integrity_check del respaldo.')
        if dest.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('El respaldo tiene infracciones de claves foráneas.')
copytree(private, target / 'data' / 'pvsa_evidencias_privadas')
if media is not None:
    copytree(media, target / 'data' / 'media')
files = {p.relative_to(target).as_posix(): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
         for p in sorted((target / 'data').rglob('*')) if p.is_file()}
manifest = {'created_utc': datetime.now(timezone.utc).isoformat(), 'git_commit': commit, 'files': files}
raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
(target / 'manifest.json').write_bytes(raw)
(target / 'manifest.sha256').write_text(hashlib.sha256(raw).hexdigest() + '\n', encoding='ascii')
print('Copia creada; verificar el manifiesto antes de declararla válida:', target)
""")
```

5. Verificar los hashes con el bloque de la sección siguiente, sin copiar todavía a ningún destino. Si algo falla, conservar el diagnóstico y no declarar válido el directorio parcial ni sobrescribir una copia anterior. Tras comprobar la copia, puede reanudarse la instalación original. Mantener una copia protegida en otro dispositivo o ubicación y conservar también su checksum mediante un canal independiente. SHA-256 detecta cambios, pero no demuestra autenticidad si un atacante puede sustituir archivos y manifiesto juntos.

No basta con copiar una SQLite abierta mientras hay escrituras. En modo WAL, los cambios confirmados pueden estar en `db.sqlite3-wal`; no copiar solo `db.sqlite3`, ni borrar WAL/SHM de una instalación abierta. La API anterior incorpora el estado confirmado y normaliza **la copia** a journal `DELETE`; no cambia el modo de la base original. Las fotografías mantienen sus nombres relativos. No copiar un directorio `staticfiles` como sustituto de los datos: los estáticos se regeneran con `collectstatic`.

### Verificación y recuperación aislada

1. Preparar otro checkout con el commit del respaldo, su entorno virtual y dependencias. Conservar el original detenido o separado del ensayo. No iniciar PVSA, ejecutar migraciones ni crear usuarios antes de colocar los datos recuperados. Las comprobaciones de hashes pueden hacerse desde la consola de respaldo ya abierta; el código no abre ni modifica una SQLite.
2. En `python pvsa_p/manage.py shell -i python`, verificar todos los archivos del respaldo:

```python
exec(r"""
import hashlib
import json
from pathlib import Path

backup = Path(input('Ruta absoluta del respaldo a verificar: ')).expanduser()
if not backup.is_absolute():
    raise ValueError('La ruta debe ser absoluta.')
backup = backup.resolve(strict=True)
raw = (backup / 'manifest.json').read_bytes()
if hashlib.sha256(raw).hexdigest() != (backup / 'manifest.sha256').read_text(encoding='ascii').split()[0]:
    raise ValueError('El manifiesto no coincide con su checksum.')
manifest = json.loads(raw)
if 'data/db.sqlite3' not in manifest['files']:
    raise ValueError('El manifiesto no contiene la base esperada.')
if any(p.is_symlink() for p in backup.rglob('*')):
    raise ValueError('Revisar enlaces del respaldo antes de copiar.')
actual = {p.relative_to(backup).as_posix() for p in (backup / 'data').rglob('*') if p.is_file()}
expected = {name for name in manifest['files'] if name.startswith('data/')}
if actual != expected:
    raise ValueError('Hay archivos de datos ausentes o no incluidos en el manifiesto.')
for relative, meta in manifest['files'].items():
    file = (backup / relative).resolve(strict=True)
    if not file.is_relative_to(backup) or not file.is_file():
        raise ValueError('Ruta de archivo no válida en el manifiesto.')
    if file.stat().st_size != meta['bytes'] or hashlib.sha256(file.read_bytes()).hexdigest() != meta['sha256']:
        raise ValueError('Archivo alterado o incompleto: ' + relative)
print('Manifiesto y archivos correctos. Commit del respaldo:', manifest['git_commit'])
""")
```

3. En el **checkout de recuperación**, configurar la clave y el modo que correspondan. En producción, elegir `PVSA_DATA_ROOT` y `PVSA_STATIC_ROOT` nuevos, separados del código, originales y respaldo. En desarrollo, SQLite siempre se busca en `pvsa_p/db.sqlite3` de ese checkout: `PVSA_DATA_ROOT` no redirige la base. Si el respaldo incluye `media`, usar una configuración de recuperación que tenga `MEDIA_ROOT` definido, como el perfil de producción. Proteger los destinos con permisos apropiados. No ejecutar los bloques de inicialización de una instalación nueva: la copia creará sus destinos de datos y rechazará los que ya existan.
4. En una consola Django nueva de ese checkout, volver a verificar el respaldo con el bloque anterior y luego copiar con este bloque. Rechaza destinos existentes: no usarlo para sobrescribir una instalación ni reutilizar la consola del original.

```python
exec(r"""
import subprocess
from pathlib import Path
from shutil import copy2, copytree
from django.conf import settings

if subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() != manifest['git_commit']:
    raise ValueError('Utilizar primero el commit correspondiente al respaldo.')
db = Path(settings.DATABASES['default']['NAME']).resolve()
private = Path(getattr(settings, 'PRIVATE_EVIDENCE_ROOT', settings.BASE_DIR / 'pvsa_evidencias_privadas')).resolve()
media = Path(settings.MEDIA_ROOT).resolve() if settings.MEDIA_ROOT else None
has_media = (backup / 'data' / 'media').is_dir()
if has_media and media is None:
    raise ValueError('El respaldo incluye media y esta configuración no define MEDIA_ROOT.')
targets = [db, private] + ([media] if has_media else [])
if any(p.exists() for p in targets):
    raise ValueError('La recuperación requiere destinos nuevos; no se sobrescriben datos.')
if any(p.is_relative_to(backup) or backup.is_relative_to(p) for p in targets):
    raise ValueError('Los destinos no deben solaparse con el respaldo.')
if any(a.is_relative_to(b) or b.is_relative_to(a) for i, a in enumerate(targets) for b in targets[i + 1:]):
    raise ValueError('Los destinos de base y archivos deben estar separados.')
if db.parent.exists() and any(p.name.startswith(db.name + '-') for p in db.parent.iterdir()):
    raise ValueError('Revisar auxiliares SQLite existentes antes de recuperar.')
db.parent.mkdir(parents=True, exist_ok=True)
copytree(backup / 'data' / 'pvsa_evidencias_privadas', private)
if has_media:
    copytree(backup / 'data' / 'media', media)
copy2(backup / 'data' / 'db.sqlite3', db)
print('Datos copiados a recuperación; falta comprobar SQLite y fotografías.')
""")
```

5. En esa misma consola, comprobar la base recuperada y que cada fotografía registrada puede abrirse desde el almacenamiento privado:

```python
exec(r"""
from pathlib import Path
from django.conf import settings
from django.db import connection
from p_w_pvsa.models import ReporteIncidencia

if not Path(settings.DATABASES['default']['NAME']).is_file():
    raise ValueError('No existe la base recuperada; no abrir una base vacía.')
with connection.cursor() as cursor:
    cursor.execute('PRAGMA integrity_check')
    if cursor.fetchall() != [('ok',)]:
        raise ValueError('Falló integrity_check.')
    cursor.execute('PRAGMA foreign_key_check')
    if cursor.fetchall():
        raise ValueError('Se encontraron infracciones de claves foráneas.')
photos = 0
for report in ReporteIncidencia.objects.exclude(foto='').exclude(foto__isnull=True).iterator():
    with report.foto.open('rb') as image:
        if not image.read(1):
            raise ValueError('Fotografía vacía en incidencia ' + str(report.pk))
    photos += 1
print('SQLite íntegra y fotografías accesibles:', photos)
""")
```

La conexión Django registra la función SQLite `PVSA_CLAVE` que requieren los índices del proyecto; ejecutar `integrity_check` con una herramienta SQLite genérica sin registrar esa función puede producir un error de función desconocida.

6. Salir de la consola y ejecutar `python pvsa_p/manage.py check` y `python pvsa_p/manage.py migrate --plan`. Con el mismo código y respaldo completo no deben aparecer migraciones pendientes inesperadas. Detenerse ante diferencias; no migrar automáticamente para ocultarlas. En producción, regenerar estáticos con `python pvsa_p/manage.py collectstatic --noinput` y ejecutar `python pvsa_p/manage.py check --deploy`.
7. Iniciar únicamente la recuperación: `runserver` si es desarrollo local o el servicio HTTPS si es producción. Comprobar login, cantidades, variantes e históricos recuperados y abrir fotografías desde incidencias con una cuenta autorizada. Comprobar que la misma URL de fotografía rechaza al anónimo y a perfiles sin permiso. No publicar directamente la carpeta privada. Preservar los tokens QR guardados; un ensayo aislado no sustituye la verificación del dominio real al volver a operar.
8. Solo después de validar la recuperación, planificar la sustitución del servicio original, el acceso de usuarios y una prueba de retorno a la copia anterior. Antes de cualquier limpieza QA, generar un respaldo actualizado y aprobar por separado qué registros, cuentas y archivos se eliminarían. No eliminar QA como parte de este procedimiento.

Quedan a cargo del despliegue definitivo: dominio, certificado y renovaciones, hosting y WSGI, proxy HTTPS, directorios persistentes y permisos, respaldos y restauración, y lectura de QR con un dispositivo real. La preparación del código no sustituye estas comprobaciones.
