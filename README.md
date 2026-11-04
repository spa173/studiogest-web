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
- MySQL 8.0 o superior (motor de base de datos del proyecto; si no se configura, se usa SQLite)

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
| `DB_ENGINE` | `mysql`, `postgresql` o `sqlite` (por defecto) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Datos de conexión a la base de datos (MySQL usa el puerto 3306) |

### Configurar MySQL

1. **Instalar MySQL** (MySQL Community Server 8.0 o superior; XAMPP con MariaDB también sirve) y
   comprobar que el servicio está iniciado.
2. **Crear la base de datos y el usuario.** Abrir el cliente de MySQL (MySQL Command Line Client o
   Workbench) y ejecutar:

   ```sql
   CREATE DATABASE studiogest_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'studiogest'@'localhost' IDENTIFIED BY 'una_contraseña_segura';
   GRANT ALL PRIVILEGES ON studiogest_db.* TO 'studiogest'@'localhost';
   -- Necesario solo para ejecutar las pruebas automáticas (Django crea una base temporal):
   GRANT ALL PRIVILEGES ON `test\_studiogest\_db`.* TO 'studiogest'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Configurar `.env`** con los mismos datos:

   ```
   DB_ENGINE=mysql
   DB_NAME=studiogest_db
   DB_USER=studiogest
   DB_PASSWORD=una_contraseña_segura
   DB_HOST=localhost
   DB_PORT=3306
   ```

4. **Crear las tablas y cargar datos de prueba:**

   ```bash
   python manage.py migrate
   python manage.py create_initial_users
   python manage.py seed_initial_catalog
   ```

5. **Verificar la conexión y los registros guardados:**

   ```bash
   python manage.py check_database
   ```

   El comando muestra el motor, la versión del servidor, si hay migraciones pendientes y cuántos
   registros tiene cada modelo.

**Comprobar que los datos persisten:** crear un registro desde la interfaz, detener el servidor
(`Ctrl + C`), volver a ejecutar `python manage.py runserver` y comprobar que el registro sigue ahí.

**Si `pip install mysqlclient` falla en Windows** (pide compilar con Microsoft C++ Build Tools), usar
la alternativa PyMySQL:

```bash
pip install pymysql
```

y agregar estas líneas en `config/__init__.py`:

```python
import pymysql

pymysql.version_info = (2, 2, 1, 'final', 0)
pymysql.install_as_MySQLdb()
```

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
