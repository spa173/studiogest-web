# StudioGest

Sistema web de gestión administrativa y operativa para barberías y peluquerías
de Cartagena de Indias. Centraliza la gestión de citas, clientes, servicios,
profesionales, inventario, ventas/caja y reportes operativos.

Proyecto integrador de **Desarrollo de Software y Aplicaciones Web II**,
construido con **Python y Django 5**.

## Integrantes

- Luis Antonio Escudero Suarez
- Luisa Fernanda Gómez Andrade
- Brayan Camilo Merchan Maldonado

## Estado del proyecto

Aplicación en desarrollo activo con los módulos principales implementados y verificados:

- **Cuentas (`accounts`)**: inicio de sesión con correo o usuario, cierre por POST, perfil/configuración, roles `ADMIN`, `TRABAJADOR` y `CAJA_RECEPCION`, expiración de sesión por inactividad (30 min) y matriz RBAC centralizada aplicada por rol.
- **Clientes (`customers`)**: CRUD, búsqueda, marca VIP, consentimiento de tratamiento de datos (`data_consent`, Ley 1581) con trazabilidad operativa básica (fecha/método/notas/usuario) y detalle con historial de citas y ventas según permisos.
- **Servicios (`services`)**: gestión de servicios y profesionales (CRUD/estado, escritura administrativa), horarios laborales básicos por profesional (`work_start_time`/`work_end_time`, opcionales).
- **Agenda (`appointments`)**: agenda semanal con filtro por profesional, validación de solapamientos y de horario laboral, cálculo de precio/descuentos/duración, snapshot histórico de cita y **reserva pública** (`/appointments/reserva/`, MVP) para solicitudes pendientes sin autenticación.
- **Panel (`dashboard`)**: indicadores operativos y financieros según rol, próximas citas y alertas reales de stock bajo.
- **Inventario (`inventory`)**: productos, control de stock/mínimo, entradas/compras, consumo/restauración atómica, historial y alertas; visibilidad de costos según rol.
- **Ventas y caja (`sales`)**: apertura/cierre de caja condicionado, registro de ventas (servicios/productos) con sesión de caja, medios de pago, anulación con restauración de stock, recibo/comprobante imprimible y arqueo con conteo físico de efectivo y diferencia.
- **Reportes (`reports`)**: filtros por fechas, resúmenes de citas/ventas, ventas por medio de pago, servicios/productos populares y stock bajo (acceso admin y caja), con exportación **CSV**, **Excel (.xlsx)** e **Imprimir/PDF** (navegador).

**Estado verificado en este entorno (2026-11-15):** `manage.py check --settings=config.settings_test` correcto; `pytest -q` **345 passed, 86 subtests**; **13 pruebas frontend Node** aprobadas; migraciones sin pendientes. Commit de referencia remoto en `main`: `f91fa13` (el árbol de trabajo puede incluir cambios locales adicionales).

Para brechas y trabajo pendiente vigente, ver [`PENDIENTES_DESARROLLO.md`](PENDIENTES_DESARROLLO.md) y [`docs/despliegue_productivo.md`](docs/despliegue_productivo.md).

## Stack y herramientas

- **Backend:** Python, Django 5.x.
- **Base de datos:** configurable por `.env` (`sqlite` por defecto, `mysql` o
  `postgresql`).
- **Frontend:** plantillas Django + Tailwind CSS con **build local** (no CDN).
  - Fuente: `static/css/tailwind.css`
  - Salida compilada: `static/css/tailwind.out.css` (enlazada en
    `templates/base.html`)
  - Configuración: `tailwind.config.js`
  - Scripts npm: `build:css` y `dev:css`
- **Pruebas:** `pytest`/Django tests y pruebas frontend con `node --test`.
- **CI (GitHub Actions):** instalación Python y Node, `npm ci`,
  `npm run build:css`, `manage.py check` (settings de pruebas), `pytest` con
  cobertura (`coverage.xml`), pruebas frontend Node y análisis SonarCloud en
  `push` (`SonarSource/sonarcloud-github-action@v4`, requiere `secrets.SONAR_TOKEN`).

## Requisitos

- Python 3.10 o superior
- Node.js y npm (para compilar Tailwind CSS)
- Git
- Opcional según entorno: MySQL 8+ o PostgreSQL (si no se configura, se usa SQLite)

## Instalación y ejecución local

```bash
# 1. Clonar el repositorio
git clone https://github.com/spa173/studiogest-web.git
cd studiogest-web

# 2. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

# 3. Instalar dependencias de Python
pip install -r requirements.txt
# Para desarrollo/pruebas/CI local: pip install -r requirements-dev.txt

# 4. Instalar dependencias frontend y compilar Tailwind
npm ci
npm run build:css
# En desarrollo activo de estilos: npm run dev:css

# 5. Crear el archivo de variables de entorno
copy .env.example .env          # Windows
cp .env.example .env            # Linux / macOS

# 6. Crear las tablas de la base de datos
python manage.py migrate

# 7. Cargar usuarios y datos de prueba (opcional, recomendado en desarrollo)
python manage.py create_initial_users
python manage.py seed_initial_catalog

# 8. Iniciar el servidor
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ en el navegador (redirige al login o al panel según
la sesión).

## Usuarios iniciales

Los comandos de carga no incluyen contraseñas predeterminadas. Solicitan una
contraseña oculta y confirmación para cada cuenta nueva; no muestran sus valores
ni restablecen claves de usuarios existentes. En automatizaciones se requiere
configuración explícita mediante variables del proceso y `--no-input`.

Consulta [la guía de inicialización segura](docs/seguridad_inicializacion.md).
La carga de catálogo es para entornos de demostración, no para bases con datos reales.

## Variables de entorno

Se configuran en el archivo `.env` (no versionado). El archivo `.env.example`
sirve como base.

| Variable | Descripción |
|---|---|
| `DEBUG` | `True` en desarrollo, `False` en producción |
| `SECRET_KEY` | Clave secreta de Django (obligatoria cuando `DEBUG=False`) |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por coma |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables para CSRF, separados por coma |
| `DB_ENGINE` | `sqlite` (por defecto), `mysql` o `postgresql` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Datos de conexión a la base de datos |

### Configurar MySQL (opcional)

1. Instalar MySQL (MySQL Community Server 8+; XAMPP/MariaDB también puede servir)
   y verificar que el servicio esté activo.
2. Crear la base de datos y el usuario:

   ```sql
   CREATE DATABASE studiogest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'studiogest'@'localhost' IDENTIFIED BY 'una_contraseña_segura';
   GRANT ALL PRIVILEGES ON studiogest_db.* TO 'studiogest'@'localhost';
   -- Necesario solo para ejecutar pruebas que creen base temporal:
   GRANT ALL PRIVILEGES ON `test\_studiogest\_db`.* TO 'studiogest'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. Configurar `.env`:

   ```
   DB_ENGINE=mysql
   DB_NAME=studiogest_db
   DB_USER=studiogest
   DB_PASSWORD=una_contraseña_segura
   DB_HOST=localhost
   DB_PORT=3306
   ```

4. Aplicar migraciones y cargar datos de prueba:

   ```bash
   python manage.py migrate
   python manage.py create_initial_users
   python manage.py seed_initial_catalog
   ```

5. Verificar conexión y estado de datos:

   ```bash
   python manage.py check_database
   ```

**Comprobar persistencia:** crear un registro desde la interfaz, detener el
servidor (`Ctrl + C`), volver a ejecutar `python manage.py runserver` y confirmar
que el registro se mantiene.

**Si `pip install mysqlclient` falla en Windows** (requiere herramientas de
compilación MSVC), se puede usar PyMySQL:

```bash
pip install pymysql
```

y agregar en `config/__init__.py`:

```python
import pymysql

pymysql.version_info = (2, 2, 1, 'final', 0)
pymysql.install_as_MySQLdb()
```

## Rutas principales

| Ruta | Descripción |
|---|---|
| `/` | Redirección: panel (autenticado) o inicio de sesión |
| `/accounts/login/` | Inicio de sesión |
| `/accounts/logout/` | Cierre de sesión |
| `/accounts/configuracion/` | Perfil/configuración del usuario |
| `/dashboard/` | Panel principal |
| `/appointments/` | Agenda semanal y gestión de citas |
| `/customers/` | Listado, creación, detalle, edición y eliminación de clientes |
| `/services/` | Catálogo de servicios |
| `/services/profesionales/` | Gestión de profesionales |
| `/inventory/` | Inventario de productos, compras/entradas e historial |
| `/sales/` | Ventas y gestión de caja (apertura/cierre) |
| `/reports/` | Reportes (acceso administrador y caja/recepción) |
| `/appointments/reserva/` | Reserva pública de citas (MVP, sin autenticación) |
| `/admin/` | Panel de administración de Django |

## Verificación y calidad

Comandos útiles según el entorno del proyecto:

```bash
# Comprobación de configuración Django
python manage.py check

# Pruebas automáticas
pytest -q

# Pruebas con cobertura (como en CI)
python -m pytest --cov=apps --cov-report=term-missing --cov-report=xml

# Pruebas frontend (Node), según CI
node --test apps/inventory/frontend_test.cjs apps/sales/navigation_test.cjs apps/appointments/pricing_frontend_test.cjs

# Compilar CSS de Tailwind
npm run build:css
```

> Nota: los resultados de pruebas dependen del entorno, dependencias instaladas y
> configuración (`.env`, base de datos, settings). CI usa
> `DJANGO_SETTINGS_MODULE=config.settings_test` y `DB_ENGINE=sqlite`.

## Estructura del proyecto

```
config/               Configuración global (settings, urls)
apps/
  accounts/           Usuarios, roles, autenticación y perfil
  appointments/       Agenda y citas
  customers/          Clientes
  dashboard/          Panel principal e indicadores
  inventory/          Inventario, stock y movimientos
  reports/            Reportes operativos
  sales/              Ventas y caja
  services/           Servicios y profesionales
templates/            Plantillas (base, parciales y vistas por módulo)
static/               Recursos estáticos (CSS, JS, imágenes)
.github/workflows/    Integración continua (CI)
```

## Flujo de trabajo con Git

```bash
git checkout -b feature/nombre-de-la-tarea
git add .
git commit -m "feat: descripción corta del cambio"
git push origin feature/nombre-de-la-tarea
```

Cada integrante trabaja en su propia rama y los cambios se integran mediante
Pull Request.

## Documentación adicional

- [`PENDIENTES_DESARROLLO.md`](PENDIENTES_DESARROLLO.md): backlog vivo y brechas pendientes.
- [`docs/despliegue_productivo.md`](docs/despliegue_productivo.md): checklist de despliegue, configuración, backups y operación.
- [`.env.example`](.env.example): plantilla de variables de entorno.
- [`studiogest_technical_guide.md`](studiogest_technical_guide.md): guía técnica de implementación y diseño.
