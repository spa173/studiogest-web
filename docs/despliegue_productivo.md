# Despliegue productivo (StudioGest)

Guía operativa para preparar y ejecutar un despliegue de `studiogest-web` en un entorno de producción. Ajusta los pasos a tu proveedor (VM, PaaS, contenedor) y a las políticas del negocio.

## 1. Prerrequisitos

- Python 3.12+ (según entorno validado) y entorno virtual.
- Node.js 20+ para compilar Tailwind CSS (`npm ci` + `npm run build:css`).
- Base de datos soportada en producción: **PostgreSQL** o **MySQL** (SQLite solo para desarrollo/pruebas).
- Servidor WSGI (p. ej. `gunicorn`) y, recomendado, un proxy inverso (Nginx/Caddy) con HTTPS.
- Acceso a variables de entorno/secret manager del proveedor (no usar archivos `.env` versionados).

## 2. Variables de entorno y configuración

Define como mínimo (ver `.env.example`):

| Variable | Producción |
|---|---|
| `SECRET_KEY` | Valor largo, aleatorio y secreto. Obligatoria con `DEBUG=False`. |
| `DEBUG` | `False`. |
| `ALLOWED_HOSTS` | Dominio(s) del servicio, separados por coma. |
| `CSRF_TRUSTED_ORIGINS` | Orígenes con esquema (`https://...`), separados por coma. |
| `DB_ENGINE` | `postgresql` o `mysql`. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Credenciales y ubicación de la BD. |

**Comportamiento con `DEBUG=False`** (`config/settings.py`): se exigen `SECRET_KEY` y configuración coherente; se activan `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, HSTS, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY` y `X_FRAME_OPTIONS=DENY`. La app debe servirse detrás de HTTPS.

- No comitees `.env`, credenciales, tokens ni datos personales.
- Mantén secretos solo en el entorno/secret manager y rota ante cualquier exposición.

## 3. Checklist de despliegue

1. **Obtener código** de la versión/revisión aprobada (tag/commit).
2. **Instalar dependencias Python**: `python -m pip install -r requirements.txt` (en producción no se requieren dependencias de desarrollo).
3. **Instalar y compilar frontend**: `npm ci` y `npm run build:css` (genera `static/css/tailwind.out.css`).
4. **Configurar variables de entorno** (tabla anterior) y verificar conectividad a la BD.
5. **Migraciones**: `python manage.py migrate --noinput`.
6. **Archivos estáticos**: `python manage.py collectstatic --noinput` (sirve `STATIC_ROOT`/`staticfiles` desde el proxy/almacenamiento según tu arquitectura).
7. **Comprobación**: `python manage.py check --deploy` (y `manage.py check`) sin errores críticos.
8. **Usuarios/datos iniciales** (solo si aplica y con credenciales seguras): crear administrador, cargar catálogo/semillas necesarias. No reutilices contraseñas de ejemplo en producción.
9. **Arranque**: ejecutar con WSGI (ej. `gunicorn config.wsgi:application`) detrás de HTTPS.
10. **Smoke test**: inicio de sesión, navegación por módulos habilitados, registro de operación básica (cita/venta/caja) y exportes/reportes según permisos.

## 4. Base de datos, backups y rollback

- **Antes de migrar en producción**: respalda la base de datos (snapshot/dump) y define ventana de cambio.
- **Rollback básico**: conserva el artefacto/código de la versión anterior y el respaldo de BD; ante fallo, restaura servicio con la versión previa y, si la migración es incompatible, restaura el backup (valida compatibilidad de migraciones antes de aplicar en productivo).
- **Archivos/media**: si se usan uploads (`MEDIA_ROOT`), incluye su respaldo y almacenamiento persistente fuera del sistema de archivos efímero del contenedor.

## 5. Seguridad y operación

- Usa HTTPS extremo a extremo hasta el proxy; HSTS se activa con `DEBUG=False`.
- Revisa `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` para evitar errores 400/403 y rechazos CSRF.
- Supervisa logs de aplicación/proxy y errores 5xx; configura alertas según tu plataforma.
- Limita acceso administrativo (`/admin/` y cuentas privilegiadas) y aplica contraseñas robustas.
- Privacidad (Ley 1581): valida textos, evidencia de consentimiento y procedimientos operativos con el responsable del tratamiento antes de operar con datos reales.

## 6. Verificación local previa al despliegue (recomendada)

En un entorno similar a producción (o con `config.settings_test`/variables apropiadas):

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
npm ci && npm run build:css
python manage.py check
python -m pytest -q
node --test apps/inventory/frontend_test.cjs apps/sales/navigation_test.cjs apps/appointments/pricing_frontend_test.cjs
```

> No existe una garantía automática de que el entorno productivo sea idéntico; valida siempre con un smoke test real tras desplegar.
