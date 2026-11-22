# PVSA — Sistema de Gestión de Habitabilidad e Inventarios

PVSA es una aplicación web desarrollada para centralizar y facilitar la gestión de habitabilidad, inventarios e incidencias de las instalaciones portuarias.

El proyecto surge de la necesidad de reemplazar una administración basada principalmente en planillas Excel por un sistema que permita mantener la información organizada, actualizada y disponible para las personas responsables.

PVSA permite registrar espacios físicos, administrar sus inventarios, conocer el estado de los objetos, conservar históricos, gestionar incidencias y analizar la información mediante un resumen general con indicadores y gráficos.

El sistema está desarrollado con **Python, Django, HTML, CSS y JavaScript**, y utiliza SQLite como base de datos en el entorno de desarrollo.

---

# 1. Instalación

## 1.1. Requisitos básicos

Para ejecutar PVSA en un equipo Windows se necesita:

- Python compatible con las dependencias del proyecto.
- Los archivos del proyecto.
- Una terminal PowerShell o CMD.
- Conexión a Internet para instalar las bibliotecas.
- Un navegador web actualizado.

Para comprobar Python, ejecutar:

```powershell
py --version
```

Para verificar que pip está disponible:

```powershell
py -m pip --version
```

No es obligatorio utilizar Visual Studio Code para ejecutar PVSA.

## 1.2. Instalación de dependencias y ejecución

Existen dos alternativas para instalar las bibliotecas necesarias. **Solo se debe utilizar una de ellas.**

### Opción A — Instalación manual

Desde la carpeta principal del proyecto, ejecutar:

```powershell
py -m pip install Django==6.0.10 django-axes==9.0.0 django-nested-admin==4.1.6 openpyxl==3.1.5 Pillow==13.0.0 qrcode==8.2 tzdata==2026.2 sqlparse==0.6.1
```

Este comando instala las dependencias utilizadas por PVSA sin necesidad de leer `requirements.txt`.

### Opción B — Instalación mediante requirements.txt

Desde la carpeta que contiene `requirements.txt`, ejecutar:

```powershell
py -m pip install -r requirements.txt
```

Python instalará automáticamente las dependencias declaradas en el archivo.

### Comprobar la instalación

Después de cualquiera de las dos opciones:

```powershell
py -m pip check
```

Si las dependencias están correctamente instaladas, el comando no debería informar conflictos.

### Ejecutar PVSA

Entrar en la carpeta que contiene `manage.py`:

```powershell
cd pvsa_p
```

Iniciar el servidor local:

```powershell
py manage.py runserver
```

Abrir en el navegador:

**http://127.0.0.1:8000/**

Una vez realizada la instalación inicial, el arranque habitual consiste únicamente en ejecutar:

```powershell
py manage.py runserver
```

**Importante:** en una instalación completamente nueva, el responsable técnico debe configurar previamente las variables de entorno y la seguridad, preparar la base de datos mediante las migraciones de Django y crear la primera cuenta administrativa. Estos procedimientos no deben repetirse en cada inicio ni aplicarse indiscriminadamente sobre bases de datos restauradas.

`runserver` corresponde al entorno de desarrollo. La instalación empresarial requiere un servidor de aplicación apropiado.

---

# 2. ¿Qué es PVSA y cómo funciona?

## 2.1. Propósito del sistema

Las instalaciones portuarias están compuestas por diferentes sectores, edificios, oficinas, salas, baños, comedores, vestidores y otras dependencias.

Cada espacio puede contener mobiliario, equipamiento y elementos que necesitan ser registrados, inspeccionados y mantenidos en condiciones adecuadas.

Cuando esta información se administra únicamente mediante planillas Excel, pueden presentarse dificultades para:

- Identificar dónde se encuentra cada elemento.
- Conocer las cantidades existentes en cada lugar.
- Detectar objetos dañados o pendientes de revisión.
- Mantener información actualizada.
- Consultar modificaciones anteriores.
- Organizar las responsabilidades entre departamentos.
- Registrar problemas detectados en los espacios.
- Obtener una visión general del estado de las instalaciones.

**PVSA centraliza esta información en una aplicación web y permite administrarla desde un único sistema.**

Su usuario principal es el **Encargado de habitabilidad**, quien supervisa la información general y realiza las tareas habituales de gestión.

Opcionalmente, la organización puede incorporar jefes de departamento para que mantengan actualizados los inventarios de sus propios espacios.

## 2.2. Estructura de las instalaciones

PVSA organiza los espacios mediante una jerarquía de cuatro niveles:

```text
Sector
  └── Ubicación
        └── Piso
              └── Lugar
```

### Sector

Representa una división general de las instalaciones portuarias.

### Ubicación

Corresponde a una instalación o dependencia perteneciente a un sector.

### Piso

Permite organizar los distintos niveles de una ubicación.

### Lugar

Representa el espacio físico específico donde se administra el inventario.

Un lugar puede ser:

- Baño.
- Comedor.
- Vestidor.
- Oficina.
- Sala de reuniones.
- Bodega.
- Sala técnica.
- Otra dependencia registrada.

Los tipos de lugar se administran mediante los catálogos de PVSA.

### Ejemplo de organización

```text
Sector Administrativo
│
└── Edificio de Oficinas
    │
    ├── Piso 1
    │   ├── Oficina de Recursos Humanos
    │   ├── Sala de Reuniones
    │   └── Baño
    │
    └── Piso 2
        ├── Oficina de Informática
        ├── Sala Técnica
        └── Comedor
```

Este ejemplo es ilustrativo. Los nombres reales dependen de la estructura registrada por la organización.

Cada lugar puede tener un inventario propio, una clasificación como área común y una configuración de acceso mediante código QR.

## 2.3. Gestión de inventarios

Los inventarios permiten conocer qué elementos existen en cada lugar y en qué condiciones se encuentran.

Para cada registro, PVSA contempla información como:

- Objeto y categoría.
- Variante, marca o material, cuando corresponda.
- Cantidad total.
- Unidades con fallas.
- Unidades pendientes de revisión.
- Mínimos operativos.
- Importancia.
- Estado de operatividad.
- Observaciones.

### Ejemplo

Una oficina tiene ocho sillas.

De esas ocho unidades:

- Cinco funcionan correctamente.
- Dos presentan fallas.
- Una está pendiente de revisión.

PVSA permite registrar estas cantidades y reflejar su estado en los resúmenes correspondientes.

De esta forma, el encargado de habitabilidad puede identificar qué elementos requieren atención sin revisar manualmente diversas planillas.

## 2.4. Objetos habituales

El sistema permite configurar los objetos que normalmente corresponden a determinados tipos de lugar.

Por ejemplo, una oficina puede requerir ciertos elementos habituales, mientras que un comedor puede necesitar otros.

La configuración permite seleccionar objetos, establecer su importancia y definir su orden.

Esto facilita el registro y la revisión de inventarios según las características de cada espacio.

## 2.5. Históricos y trazabilidad

PVSA conserva antecedentes de modificaciones relevantes realizadas en los inventarios.

Los históricos permiten consultar información anterior y revisar la evolución de determinados registros.

También se conserva la trazabilidad correspondiente cuando se realizan traslados de inventarios.

Para proteger la información histórica, el sistema impide la eliminación ordinaria de inventarios con históricos asociados.

El acceso a estos antecedentes depende de los permisos del usuario y de los lugares autorizados.

## 2.6. Áreas propias y áreas comunes

PVSA diferencia los lugares asignados a departamentos de los espacios compartidos.

### Áreas propias

Son los espacios asignados a una jefatura determinada.

Por ejemplo, la jefatura de Informática podría tener asignadas las oficinas y salas utilizadas por su equipo.

Esa jefatura puede administrar los inventarios correspondientes dentro de sus permisos.

### Áreas comunes

Son espacios compartidos por distintas personas o departamentos.

Por ejemplo:

- Baños.
- Comedores.
- Vestidores.

Los usuarios con los permisos correspondientes pueden consultar o reportar incidencias en las áreas comunes autorizadas.

Las áreas comunes no se convierten automáticamente en lugares propios de una jefatura.

## 2.7. Códigos QR y reportes de incidencias

PVSA permite asociar un código QR a los lugares.

Los códigos pueden configurarse como públicos, privados o desactivados.

### QR público

Permite que una persona informe una incidencia sin iniciar sesión.

Por ejemplo:

1. Un trabajador detecta un lavamanos dañado.
2. Escanea el QR del baño.
3. Accede al formulario público.
4. Describe el problema.
5. Adjunta una fotografía, si corresponde.
6. Envía el reporte.

La incidencia queda registrada para su gestión dentro de PVSA.

La persona que utiliza el QR público **no necesita una cuenta ni pertenece a un perfil interno del sistema**.

### QR privado

Requiere autenticación y permisos para acceder a las funciones correspondientes.

### Configuración de visibilidad

La clasificación de un lugar como área común determina inicialmente la visibilidad del QR.

Posteriormente, el personal administrativo autorizado puede cambiar su visibilidad sin modificar la clasificación física del lugar.

Las fotografías privadas se protegen mediante controles de acceso.

## 2.8. Gestión de incidencias

Las incidencias permiten registrar y realizar seguimiento de problemas asociados a los lugares.

Un reporte puede contener:

- Lugar afectado.
- Descripción del problema.
- Fotografía.
- Estado.
- Información de seguimiento.

El personal autorizado puede consultar y gestionar las incidencias recibidas.

## 2.9. Excel como herramienta complementaria

PVSA incorpora funciones de importación y exportación de información mediante Excel.

Esto permite facilitar la transición desde las planillas utilizadas anteriormente y realizar operaciones de carga masiva cuando corresponda.

La importación contempla validaciones y previsualización antes de confirmar los cambios.

**Excel funciona como una herramienta complementaria; PVSA es el sistema central de gestión.**

## 2.10. Resumen general y análisis visual

PVSA dispone de una sección denominada **Resumen general**, destinada a facilitar la interpretación del estado de habitabilidad.

Esta sección combina indicadores, gráficos, tablas y filtros.

### Estado de sectores

Permite visualizar cuántos sectores se encuentran:

- Operativos.
- Requieren atención.
- Críticos.

### Estado de ubicaciones

Presenta una clasificación equivalente para las ubicaciones registradas.

### Cantidad de lugares por tipo

Muestra cuántos espacios físicos existen según su tipo, por ejemplo:

- Baños.
- Comedores.
- Vestidores.
- Oficinas.
- Otros tipos registrados.

Los indicadores se calculan utilizando lugares físicos reales, **incluidos aquellos que todavía no tienen inventario**.

### Ubicaciones prioritarias

Permite identificar las ubicaciones que presentan una mayor cantidad de unidades con fallas.

Esto facilita reconocer dónde se concentra la necesidad de atención.

### Tablas de análisis

Se conservan las tablas de:

- Estado por sector.
- Estado por ubicación.
- Objetos que requieren atención.

### Filtros

El Resumen general incluye filtros por:

- Sector.
- Ubicación.
- Piso.
- Tipo de lugar.
- Categoría.
- Objeto.
- Variante.
- Condición.
- Marca.
- Material.

También incorpora opciones de ordenamiento, selección de secciones visibles y restablecimiento.

Los recuentos de lugares físicos utilizan los filtros estructurales correspondientes, mientras que el análisis de inventarios mantiene sus propios criterios.

El objetivo del dashboard es que **el encargado de habitabilidad pueda comprender rápidamente el estado de las instalaciones y reconocer qué necesita atención**.

## 2.11. Funcionamiento general de PVSA

```text
Encargado de habitabilidad
          │
          ▼
Organiza sectores, ubicaciones,
pisos y lugares
          │
          ▼
Registra y administra
los inventarios
          │
          ▼
Consulta cantidades,
estados e históricos
          │
          ├──────────────────────────┐
          │                          │
          ▼                          ▼
Jefaturas opcionales          Reportes mediante QR
gestionan sus espacios        y gestión de incidencias
          │                          │
          └────────────┬─────────────┘
                       │
                       ▼
             Resumen general
          indicadores y gráficos
                       │
                       ▼
          Seguimiento y gestión
              de habitabilidad
```

La finalidad es mantener una administración organizada y facilitar que las personas responsables dispongan de información actualizada para realizar su trabajo.

---

# 3. Usuarios y responsabilidades

PVSA contempla **tres perfiles internos**, uno de ellos opcional, y un mecanismo de acceso público sin autenticación.

## 3.1. Administrador técnico del sistema

Es la persona responsable de la administración informática de PVSA.

Dispone de acceso completo para:

- Utilizar todas las funciones del sistema.
- Crear y administrar usuarios.
- Gestionar perfiles y permisos.
- Crear y administrar jefaturas.
- Asignar lugares.
- Realizar intervenciones técnicas.
- Acceder a Django Admin.

Su función principal es mantener la capacidad de administración completa y prestar soporte cuando sea necesario.

**Identificación técnica:** cuenta Django con privilegios de superusuario (`is_superuser=True`).

## 3.2. Encargado de habitabilidad

Es **el usuario principal para quien se desarrolló PVSA**.

Su trabajo consiste en mantener organizada y actualizada la información de habitabilidad de las instalaciones portuarias.

Puede utilizar todas las funcionalidades operativas disponibles dentro de PVSA, incluyendo:

- Gestión de sectores, ubicaciones, pisos y lugares.
- Administración de categorías y objetos.
- Configuración de objetos habituales.
- Gestión de inventarios.
- Consultas e históricos.
- Importación y exportación Excel.
- Configuración operativa de QR.
- Gestión de incidencias.
- Consulta del Resumen general y sus indicadores.

No tiene autorización para:

- Crear o administrar cuentas de usuario.
- Gestionar perfiles o permisos.
- Administrar jefaturas y asignaciones de otros usuarios.
- Acceder a Django Admin.
- Realizar funciones técnicas reservadas al administrador del sistema.

**Identificación técnica:** grupo Django `Administrador`.

El nombre funcional de este perfil es **Encargado de habitabilidad**.

## 3.3. Jefe de departamento — opcional

Este perfil permite distribuir responsabilidades entre distintas jefaturas, si la organización decide utilizarlo.

Por ejemplo:

- Jefatura de Informática.
- Jefatura de Recursos Humanos.
- Otras jefaturas.

Cada jefe puede tener espacios específicos asignados.

Dentro de sus permisos, puede gestionar los inventarios de esos lugares y consultar los históricos autorizados.

También puede consultar y reportar incidencias en las áreas comunes permitidas.

No tiene acceso global a los inventarios de otros departamentos ni a la administración de usuarios.

**Identificación técnica:** grupo Django `Jefe de departamento`.

**El uso de jefaturas no es obligatorio.** PVSA puede funcionar con el encargado de habitabilidad administrando directamente toda la operación.

## 3.4. Visitante anónimo — acceso público

Corresponde a cualquier persona que utiliza una función pública de PVSA sin iniciar sesión.

Por ejemplo, un trabajador que escanea un QR público para reportar una incidencia.

El visitante anónimo:

- No necesita una cuenta.
- No utiliza contraseña.
- Puede acceder al formulario público habilitado.
- Puede reportar una incidencia y adjuntar una fotografía cuando corresponda.
- No puede administrar inventarios.
- No puede consultar información privada.
- No puede acceder a Django Admin.

**No es un perfil interno registrado en Django.** Es una modalidad de acceso público controlado.

## 3.5. Resumen de permisos

| Funcionalidad | Administrador técnico | Encargado de habitabilidad | Jefe de departamento | Visitante anónimo |
|---|---|---|---|---|
| Gestión general de inventarios | Completa | Completa | Solo lugares propios | No |
| Sectores, ubicaciones y lugares | Completa | Completa | Según permisos asignados | No |
| Objetos habituales | Completa | Completa | Sin administración global | No |
| Históricos | Global | Global | Autorizados | No |
| Incidencias | Completa | Gestión operativa | Según permisos | Reporte mediante QR público |
| Configuración QR | Completa | Operativa completa | Según permisos | No |
| Excel y resumen | Completa | Completa | Según funciones autorizadas | No |
| Administración de usuarios | Sí | No | No | No |
| Administración de jefaturas | Sí | No | No | No |
| Django Admin | Sí | No | No | No |

Los permisos se verifican en el servidor y están sujetos a las validaciones de integridad del sistema.

---

# 4. Organización del proyecto

PVSA utiliza una estructura modular basada en Django.

```text
p_-main/
├── README.md
├── requirements.txt
└── pvsa_p/
    ├── manage.py
    ├── mysite/
    └── p_w_pvsa/
        ├── administracion/
        ├── formularios/
        ├── modelos/
        ├── servicios/
        ├── vistas/
        ├── migrations/
        ├── templates/
        └── static/
```

| Componente | Función |
|---|---|
| `manage.py` | Administración y ejecución de Django. |
| `mysite` | Configuración principal del proyecto. |
| `modelos` | Entidades y relaciones de datos. |
| `vistas` | Procesamiento de solicitudes y respuestas. |
| `formularios` | Entrada y validación de información. |
| `servicios` | Reglas y operaciones del sistema. |
| `administracion` | Configuración administrativa de Django. |
| `templates` | Interfaz HTML. |
| `static` | Archivos CSS y JavaScript. |
| `migrations` | Evolución de la estructura de la base de datos. |

Los nombres internos de los módulos corresponden a la implementación y no deben modificarse sin revisar sus referencias.

---

# 5. Seguridad y conservación de información

PVSA incorpora controles de seguridad orientados a proteger los registros y restringir las funciones según las responsabilidades de cada usuario.

Entre los controles se encuentran:

- Autenticación.
- Restricciones por perfil.
- Validación de lugares asignados.
- Protección contra intentos reiterados de inicio de sesión mediante `django-axes`.
- Comprobaciones de permisos en el servidor.
- Protección de fotografías privadas.
- Validación de formularios.
- Conservación de históricos.
- Controles de integridad sobre inventarios.
- Validación de acceso mediante códigos QR.

## 5.1. Base de datos

En el entorno de desarrollo, PVSA utiliza SQLite.

Los datos operativos no deben publicarse en el repositorio de código.

La empresa deberá establecer una política de respaldo y recuperación acorde con su infraestructura.

## 5.2. Fotografías privadas

Las fotografías asociadas a incidencias deben conservarse en almacenamiento privado y entregarse exclusivamente a través de funciones autorizadas.

No deben exponerse como archivos públicos accesibles directamente desde el servidor web.

## 5.3. Históricos

Los registros históricos deben conservarse para garantizar la trazabilidad de los inventarios.

Las operaciones de eliminación y modificación están sujetas a las restricciones de integridad existentes.

## 5.4. Respaldos

Para recuperar una instalación correctamente es necesario conservar de manera coherente:

- Base de datos.
- Fotografías privadas.
- Configuración y claves necesarias.
- Versión compatible del código.

El respaldo definitivo del desarrollo se mantiene separado del repositorio GitHub.

La recuperación de datos existentes debe realizarse con procedimientos controlados y respaldos verificados.

---

# 6. Instalación en la infraestructura de la empresa

El desarrollo de PVSA se ha comprobado funcionalmente en un entorno local.

Su instalación definitiva corresponde al personal técnico de la empresa.

El administrador responsable deberá configurar, según la infraestructura disponible:

- Servidor de aplicación compatible con Django.
- Dominio o dirección de acceso.
- HTTPS.
- Configuración segura de Django.
- Variables de entorno y secretos.
- Base de datos y almacenamiento persistente.
- Archivos estáticos.
- Almacenamiento privado de fotografías.
- Permisos de acceso.
- Respaldos y recuperación.
- Monitoreo y registros.
- Correo SMTP, si se requieren funciones que dependen de ese servicio.

La configuración de seguridad inicial, las migraciones y las cuentas administrativas deben prepararse según se trate de una instalación nueva o de una restauración.

La empresa debe realizar las comprobaciones correspondientes antes de habilitar el acceso a sus usuarios.

**El servidor `runserver` de Django no está destinado a producción.**

El proyecto entrega las funcionalidades de la aplicación; la infraestructura definitiva, su mantenimiento y su seguridad operacional corresponden a la organización que la implemente.

---

# 7. Problemas frecuentes

## Python no reconoce el comando

Comprobar:

```powershell
py --version
```

Verificar que Python esté correctamente disponible en el equipo.

## Faltan dependencias

Instalar nuevamente las dependencias mediante una de las alternativas de la sección 1.2.

Para comprobar conflictos:

```powershell
py -m pip check
```

## No se encuentra manage.py

Comprobar que la terminal esté ubicada en la carpeta correcta:

```powershell
cd pvsa_p
```

Después ejecutar:

```powershell
py manage.py runserver
```

## Aparece un error de configuración de Django

La instalación puede necesitar variables de entorno, migraciones o configuración inicial.

Estas operaciones deben revisarse según las instrucciones del administrador técnico y el entorno utilizado.

## El puerto 8000 está ocupado

Comprobar si existe otro proceso utilizando ese puerto.

No finalizar procesos desconocidos sin identificar su función.

## Los acentos o la letra ñ se muestran incorrectamente

Guardar los archivos de texto y documentación con codificación **UTF-8**.

---

# 8. Validación y estado de entrega

El desarrollo de PVSA ha pasado por comprobaciones funcionales y técnicas relacionadas con:

- Organización de sectores, ubicaciones, pisos y lugares.
- Inventarios y catálogos.
- Objetos habituales.
- Históricos y traslados.
- Autenticación y permisos.
- Incidencias.
- Fotografías privadas.
- Códigos QR públicos y privados.
- Importación y exportación Excel.
- Resumen general.
- Gráficos e indicadores.
- Filtros dependientes.
- Lugares con y sin inventario.
- Integridad de la base de datos.

La última mejora incorporada corresponde al **dashboard visual del Resumen general**, que permite analizar el estado de sectores, ubicaciones, tipos de lugar y prioridades de atención.

Los filtros estructurales fueron comprobados también con espacios que no contienen inventario.

Las pruebas automatizadas y las comprobaciones en navegador realizadas durante el desarrollo finalizaron sin defectos técnicos pendientes conocidos en el alcance verificado.

La validación local no reemplaza las pruebas de instalación, aceptación y seguridad que correspondan a los servidores definitivos de la empresa.

## Repositorio

**GitHub:** https://github.com/matiascayunao/p_-main

**Rama principal:** `main`

La rama principal contiene el código fuente destinado a la entrega una vez publicados los cambios finales.

---

**PVSA — Sistema de Gestión de Habitabilidad e Inventarios**

Documentación de instalación, funcionamiento, perfiles, seguridad y entrega técnica.

**Noviembre de 2026.**