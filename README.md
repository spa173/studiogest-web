# StudioGest

Sistema web de gestión administrativa y operativa para barberías y peluquerías
de Cartagena de Indias. Permite organizar la agenda de citas, los clientes, los
servicios y los profesionales en una sola herramienta.

Proyecto integrador de **Desarrollo de Software y Aplicaciones Web II**,
construido con **Python, Django y Tailwind CSS**.

## Integrantes

- Luis Antonio Escudero Suarez
- Luisa Fernanda Gómez Andrade
- Brayan Camilo Merchan Maldonado

## Estado del proyecto

**Clase 1 (entorno y frontend): completada.** Incluye:

- Proyecto Django configurado y ejecutable.
- Plantilla base (`base.html`) con menú lateral, barra superior y navegación
  inferior para celular.
- Inicio de sesión con correo electrónico o usuario, y cierre de sesión.
- Roles de usuario: Administrador y Trabajador.
- Panel principal (dashboard) con indicadores y próximas citas.
- Agenda semanal con ventana emergente para registrar citas, filtro por
  profesional y validación de cruces de horario.
- Datos de prueba para clientes, servicios, profesionales y citas.

Módulos pendientes: clientes y servicios (pantallas propias), inventario, ventas
y caja, y reportes.

## Requisitos

- Python 3.10 o superior
- Git
- Conexión a internet (Tailwind CSS se carga desde un CDN)
- PostgreSQL (opcional; por defecto se usa SQLite)

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/spa173/studiogest-web.git
cd studiogest-web

# 2. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

# 3. Instalar las dependencias
pip install -r requirements.txt

# 4. Crear el archivo de variables de entorno
copy .env.example .env          # Windows
cp .env.example .env            # Linux / macOS

# 5. Crear las tablas de la base de datos
python manage.py migrate

# 6. Cargar usuarios y datos de prueba
python manage.py create_initial_users
python manage.py seed_initial_catalog

# 7. Iniciar el servidor
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ en el navegador.

## Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | admin@studiogest.co | admin123 |
| Trabajador | julian@studiogest.co | barbero123 |

Estas credenciales son solo para desarrollo y deben cambiarse antes del
despliegue.

## Variables de entorno

Se configuran en el archivo `.env` (que no se sube al repositorio). El archivo
`.env.example` sirve de modelo.

| Variable | Descripción |
|---|---|
| `DEBUG` | `True` en desarrollo, `False` en producción |
| `SECRET_KEY` | Clave secreta de Django |
| `USE_POSTGRES` | `True` para usar PostgreSQL; `False` usa SQLite |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Datos de conexión a PostgreSQL |

### Usar PostgreSQL

1. Crear la base de datos: `CREATE DATABASE studiogest_db;`
2. En `.env`, poner `USE_POSTGRES=True` y completar los datos de conexión.
3. Ejecutar `python manage.py migrate`.

## Estructura del proyecto

```
config/               Configuración global (settings, urls)
apps/
  accounts/           Usuarios, roles, inicio y cierre de sesión
  dashboard/          Panel principal con indicadores
  customers/          Modelo de clientes
  services/           Servicios y profesionales
  appointments/       Agenda y registro de citas
templates/            base.html, fragmentos y pantallas
static/               Archivos estáticos (logotipo)
```

## Rutas principales

| Ruta | Descripción |
|---|---|
| `/accounts/login/` | Inicio de sesión |
| `/dashboard/` | Panel principal |
| `/appointments/` | Agenda semanal y registro de citas |
| `/admin/` | Panel de administración de Django |

## Flujo de trabajo con Git

```bash
git checkout -b feature/nombre-de-la-tarea
git add .
git commit -m "feat: descripción corta del cambio"
git push origin feature/nombre-de-la-tarea
```

Cada integrante trabaja en su propia rama con su propia cuenta, y los cambios se
integran mediante Pull Request.

## Documentación de diseño

La guía técnica de implementación está en `studiogest_technical_guide.md`.
