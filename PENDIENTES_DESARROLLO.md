# StudioGest — Backlog vivo y estado de desarrollo

**Proyecto:** StudioGest · Sistema Web de Gestión para Barberías y Peluquerías  
**Asignatura:** Desarrollo de Software y Aplicaciones Web II (Cartagena de Indias, 2026)  
**Equipo:** Luis Antonio Escudero Suárez · Luisa Fernanda Gómez Andrade · Brayan Camilo Merchan Maldonado  
**Última actualización:** 2026-11-15  
**Referencia base remota:** commit `f91fa13` en `main`; el árbol de trabajo contiene cambios locales adicionales verificados (sin commit al momento de esta actualización).

---

## 1. Resumen del estado actual

Base funcional en Django 5.x con módulos separados (`accounts`, `customers`, `services`, `appointments`, `dashboard`, `inventory`, `sales`, `reports`) que cubren la operación principal del negocio.

**Estado verificado en este entorno (2026-11-15):**
- `python manage.py check --settings=config.settings_test`: correcto (0 issues).
- `python -m pytest -q`: **345 passed, 86 subtests**.
- Frontend (Node): **13 passed** (`apps/inventory/frontend_test.cjs`, `apps/sales/navigation_test.cjs`, `apps/appointments/pricing_frontend_test.cjs`).
- `python manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- Migraciones aplicadas en entorno local de desarrollo: incluye `customers.0003_customer_consent_traceability`, `sales.0002_add_cash_count_fields`, `services.0002_professional_work_schedule`.
- Frontend: Tailwind con build local (`npm run build:css`, salida `static/css/tailwind.out.css`).
- CI (`.github/workflows/ci.yml`): `npm ci` + `npm run build:css` + `manage.py check` + `pytest` con cobertura + pruebas frontend Node + `coverage.xml` + SonarCloud en `push` (requiere `secrets.SONAR_TOKEN`).

> Los resultados dependen del entorno, dependencias y configuración; deben confirmarse al ejecutar los comandos correspondientes.

---

## 2. Matriz de requisitos funcionales (RF)

| ID | Requisito | Prioridad | Estado | Observaciones (estado vigente) |
| :--- | :--- | :---: | :---: | :--- |
| **RF-01** | Inicio de sesión y control de acceso por rol | Alta | 🟢 Implementado (operativo) | Autenticación y roles `ADMIN`, `TRABAJADOR`, `CAJA_RECEPCION`. Matriz RBAC centralizada en `apps/accounts/permissions.py` y aplicada en vistas/UI (dashboard, agenda, clientes, inventario, catálogo/servicios/profesionales, ventas/caja, reportes). Reportes y ventas/caja restringidos según rol; historial comercial de cliente oculto a trabajador; costos/acciones sensibles condicionados por rol. `/admin/` Django restringido a administradores. Mantener revisión ante nuevos flujos. |
| **RF-02** | Gestión y búsqueda de clientes | Alta | 🟢 Implementado | CRUD, búsqueda, marca VIP y consentimiento (`data_consent`) con trazabilidad operativa básica (`data_consent_at`, método, notas, registrado por) y UI/admin asociada. |
| **RF-03** | Crear, modificar y cancelar citas | Alta | 🟢 Implementado | Gestión de citas en `appointments` (creación, completado/cancelación según permisos y reglas existentes). |
| **RF-04** | Validación de citas solapadas por profesional | Alta | 🟢 Implementado | Validación de solapamientos en la lógica/modelo de agenda. |
| **RF-05** | Vista de agenda por día/profesional (operativa) | Media | 🟢 Implementado | Agenda semanal con filtro por profesional. |
| **RF-06** | Catálogo de servicios (duración y precio) | Alta | 🟢 Implementado | Servicios con duración, precio y estado activo; gestión según permisos. |
| **RF-07** | Horarios laborales de barberos y estilistas | Media | 🟢 Implementado (básico) | `Professional` define franja laboral (`work_start_time`/`work_end_time`, opcional para compatibilidad). Las citas se validan dentro del horario cuando está configurado; configuración disponible en gestión de profesionales. Pendientes reglas avanzadas (ver baja prioridad). |
| **RF-08** | Inventario con stock actual y mínimo (no negativo) | Alta | 🟢 Implementado | Productos, stock, mínimo, entradas/compras, consumo/restauración atómica y validaciones de inventario. |
| **RF-09** | Alertas automáticas de stock mínimo en panel | Alta | 🟢 Implementado | Dashboard muestra alertas reales de stock bajo desde inventario. |
| **RF-10** | Venta de servicios y productos con detalle y medios de pago | Alta | 🟢 Implementado | Ventas con servicios/productos, medios de pago, sesión de caja asociada, descuento/restauración de stock y anulación de ventas registradas (con restauración de stock y liberación de cita cobrada para re-cobro cuando aplica). Comprobante/recibo imprimible por venta disponible. |
| **RF-11** | Apertura y cierre diario de caja | Media | 🟢 Implementado | Sesiones de caja con apertura y cierre; arqueo detallado con base, ventas por medio de pago, total ventas, efectivo esperado y **conteo físico de efectivo con diferencia persistida** (`counted_cash`, `cash_difference`). |
| **RF-12** | Historial del cliente (citas y compras) | Media | 🟢 Implementado | Detalle de cliente con historial de citas; historial de ventas/compras visible según permisos (admin/caja). |
| **RF-13** | Reportes de ventas, servicios y stock bajo | Media | 🟢 Implementado | Filtros por fechas, resumen de citas/ingresos, ventas por medio de pago, servicios/productos populares y stock bajo (acceso admin y caja/recepción). |
| **RF-14** | Reserva pública de citas para clientes | Baja | 🟢 Implementado (MVP) | Página pública `/appointments/reserva/` (sin autenticación) para solicitar cita: captura datos de contacto y selección de servicio/profesional/fecha/hora, valida disponibilidad y horario laboral, crea/actualiza cliente y registra la cita en estado **Pendiente**. Pendientes de definición/ampliación: confirmación/notificación, reglas de disponibilidad pública avanzadas, gestión de spam y políticas operativas. |
| **RF-15** | Exportación de reportes a PDF o Excel | Baja | 🟢 Implementado (operativo) | Exportación **CSV** y **Excel (.xlsx)** desde `/reports/` respetando filtros y permisos, más opción **Imprimir / PDF** vía navegador. No se genera PDF server-side. |

---

## 3. Matriz de requisitos no funcionales (RNF)

| ID | Categoría | Requisito | Estado | Observaciones (estado vigente) |
| :--- | :--- | :--- | :---: | :--- |
| **RNF-01** | Compatibilidad / responsive | Adaptable desde 360 px en móviles | 🟡 Parcial | UI con Tailwind y componentes responsive; persiste validación visual/manual en dispositivos y resoluciones objetivo. |
| **RNF-04** | Seguridad de acceso | Cifrado de contraseñas y expiración de sesión tras 30 min de inactividad | 🟢 Implementado | Django gestiona contraseñas; `SESSION_COOKIE_AGE=1800` y `SESSION_SAVE_EVERY_REQUEST=True`; endurecimiento adicional con `DEBUG=False` (cookies seguras, HSTS, HTTPS redirect, headers). Logout por POST y controles de acceso reforzados. |
| **RNF-05** | Privacidad (Ley 1581 de 2012) | Autorización explícita para tratamiento de datos personales | 🟡 Parcial | `data_consent` con evidencia operativa básica (fecha, método, notas, usuario que registra) y flujo de otorgamiento/revocación en UI. Falta validación de textos/política definitiva, versionado probatorio formal y procedimiento institucional. |
| **RNF-07** | Licenciamiento / stack | Uso de tecnologías abiertas sin licencias de pago obligatorias | 🟢 Cumplido | Stack basado en Python/Django y herramientas abiertas; Tailwind compilado localmente. Se agregó `openpyxl` (licencia abierta) para exportación Excel. |
| **RNF-08** | Mantenibilidad y pruebas | Cobertura/pruebas suficientes en módulos críticos | 🟡 Parcial | Suite amplia (345 passed, 86 subtests, 13 frontend) y CI con cobertura/SonarCloud configurados; conviene seguir reforzando E2E de flujos críticos, casos límite y umbrales de calidad. |

---

## 4. Brechas y trabajo pendiente (backlog priorizado)

### Alta prioridad (operación/calidad)

1. **Validación E2E y robustez del flujo ventas–inventario–caja (RF-08/10/11)**
   - Seguir cubriendo escenarios integrales: combinaciones servicio/producto, concurrencia básica, rechazos por stock, caja abierta/cerrada, anulaciones y consistencia de totales/arqueo.
2. **Privacidad operativa final (RNF-05)**
   - Acordar y aplicar textos/política definitiva de tratamiento de datos, evidencia formal requerida, obligatoriedad por flujo y procedimiento operativo (Ley 1581) con el responsable del proyecto/institución.
3. **Calidad continua (RNF-08)**
   - Revisar umbrales de cobertura/calidad en CI y SonarCloud, y ampliar pruebas de casos límite y regresiones en módulos críticos.

### Media prioridad

1. **Comprobantes y numeración fiscal/operativa**
   - Existe recibo/comprobante imprimible por venta; evaluar necesidad de PDF server-side, numeración formal/fiscal o formato exigido por el negocio.
2. **UX e historial operativo**
   - Mejorar consistencia y feedback en flujos largos (venta, caja, inventario) y enriquecer historiales (caja/movimientos) con filtros/resúmenes cuando aporte valor.
3. **Robustez funcional y de datos**
   - Revisar validaciones cruzadas, mensajes de error, transacciones en operaciones compuestas y documentar supuestos (redondeos, unidades, anulaciones, cierres).
4. **Higiene frontend/build/CI**
   - Mantener artefacto CSS alineado con cambios, evitar duplicidad de configuración en plantillas y vigilar pipeline (incl. análisis SonarCloud con token configurado en el repositorio remoto).

### Baja prioridad

1. **Reserva pública de citas (RF-14, evolución del MVP)**
   - Añadir confirmación/notificación al cliente y al negocio, gestión de solicitudes (aprobar/rechazar/reprogramar), controles anti-spam/abuso y reglas de disponibilidad pública más finas según política operativa.
2. **Horarios y reglas avanzadas de agenda**
   - Excepciones por fecha, bloqueos, festivos, días laborables específicos, tiempos de preparación y reglas de capacidad.
3. **Ampliaciones de analítica/reportes**
   - Indicadores adicionales, comparativos por periodo y vistas ejecutivas.

### Operación / despliegue

- Se agregó `docs/despliegue_productivo.md` y `.env.example` con checklist de configuración, migraciones, estáticos, `check --deploy`, backups/rollback y consideraciones de seguridad.
- Antes de producción: validar `DEBUG=False`, secretos, `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`, HTTPS/proxy, base de datos gestionada, `collectstatic`, backups, cuentas seguras y smoke tests en entorno real.

---

## 5. Cambios relevantes recientes (verificados en árbol de trabajo)

- **RBAC (RF-01):** permisos centralizados y aplicados por rol en módulos y navegación/UI.
- **Ventas/Caja (RF-10/11):** registro condicionado a caja abierta, anulación de ventas con restauración de stock/re-cobro de cita, recibo imprimible, arqueo detallado y conteo físico con diferencia.
- **Privacidad (RNF-05):** trazabilidad operativa del consentimiento de clientes.
- **Reportes (RF-13/15):** acceso por rol (admin/caja), exportación CSV/Excel y opción de impresión/PDF.
- **Agenda/Profesionales (RF-07, RF-14):** horarios laborales básicos por profesional, validación de citas y MVP de reserva pública de citas (`/appointments/reserva/`).
- **Documentación operativa:** guía de despliegue productivo y plantilla de entorno.

---

## 6. Contexto histórico (referencia)

Las secciones históricas previas se conservan como referencia en el historial del documento/repositorio y **no** deben interpretarse como estado actual sin contrastar con el código y las verificaciones vigentes.

---

## 7. Criterio de actualización

- Marcar como **implementado** solo lo verificable en código, rutas, modelos, migraciones y/o pruebas.
- Mantener como **parcial** lo que existe pero requiere endurecimiento, validación integral, definición legal/operativa o cobertura adicional.
- Registrar brechas con prioridad, módulo afectado y siguiente acción concreta.
