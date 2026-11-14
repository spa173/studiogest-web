# Reporte de pruebas del módulo Servicios — StudioGest

Fecha de revisión: 13 de noviembre de 2026 (America/Bogota). Rama: `luisa`.

## 1. Objetivo y alcance

Verificar el CRUD de Servicios, su integración HTTP con Agenda y la coherencia
de sus validaciones. Reproducir defectos con datos sintéticos y dejar evidencia
automatizada para orientar las correcciones de la entrega de Aplicaciones Web II.

Se conservaron las 33 pruebas originales (21 de Servicios y 12 de Profesionales)
y las 3 pruebas de integración de la etapa 2. La reproducción inicial añadió
10 casos de regresión; tras la autorización de SVC-01 se ampliaron a 40 casos.
Posteriormente se autorizó la nueva regla de duración por cita y la corrección
de SVC-02. Se añadieron 29 casos en `apps/appointments/test_duration.py`.
La ampliación económica autorizada añadió seis campos, una migración y 53 casos
de precios, permisos, historial y migración, además de comprobaciones JavaScript.

Para la nueva regla se modificaron el formulario, el cálculo de finalización del
modelo y la plantilla de Agenda. La ampliación económica modifica también el
paso del usuario al formulario y protege los campos económicos en Django Admin.
No se modificaron Profesionales, Clientes, `.env` ni el módulo Ventas.
Se creó la migración autorizada `appointments.0002_appointment_pricing`.
No se realizaron commits, push ni merge. No se accedió a MySQL ni a registros
existentes. Los datos creados por los tests pertenecen exclusivamente a SQLite
en memoria y se descartan mediante el aislamiento del entorno de pruebas.

## 2. Herramientas y entorno

| Elemento | Configuración |
| --- | --- |
| Sistema | Windows, terminal PowerShell |
| Python del entorno `.venv` | 3.13.13 |
| Django | 5.2.18 |
| pytest | 9.2.0 |
| pytest-django | 4.14.0 |
| Ajustes | `config.settings_test`, seleccionados por `pytest.ini` |
| Base de datos | SQLite en memoria; no se usa `studiogest_db` |
| Cliente | Cliente de pruebas de Django, peticiones GET y POST |
| Evidencia | JUnit XML; registros capturados desactivados para la exportación |

La configuración de pruebas reemplaza completamente `DATABASES`. Heredar los
ajustes comunes no abre una conexión a MySQL. Las tablas se crean a partir de
las migraciones en la base temporal. La nueva migración económica solo se
ejecutó en SQLite en memoria, nunca en MySQL.

## 3. Casos automatizados y resultados

### Línea base ejecutada antes de añadir las regresiones

`36 passed, 31 subtests passed in 45.00s` (código de salida 0).

La suite original cubre autenticación, roles, restricciones HTTP, CSRF, altas,
ediciones, entradas inválidas, estados, navegación y protección del historial.
Las pruebas originales no se reescribieron ni eliminaron.

### Nuevos casos de esta etapa

| Prueba en `test_regressions.py` | Casos | Resultado esperado | Estado actual |
| --- | ---: | --- | --- |
| `test_model_validation_rejects_invalid_service_values` | 12 | `full_clean()` rechaza valores inválidos y respeta límites | Aprobadas; SVC-01 corregido |
| `test_direct_save_rejects_invalid_service_values` | 12 | Escritura individual inválida rechazada sin persistencia | Aprobadas; SVC-01 corregido |
| `test_form_and_crud_reject_invalid_values_without_partial_writes` | 2 | Formulario, alta y edición rechazan esos valores sin escrituras parciales | Aprobadas |
| `test_minimum_positive_duration_and_free_price_remain_allowed` | 1 | Duración 1 y precio 0 siguen permitidos | Aprobada |
| `test_invalid_direct_update_preserves_persisted_service` | 2 | Edición directa inválida no altera la fila persistida | Aprobadas |
| `test_valid_direct_creation_update_and_partial_save` | 1 | Alta, edición y `update_fields` válidos conservan su funcionamiento | Aprobada |
| `test_partial_save_validates_the_complete_instance` | 1 | Valor inválido en otro campo bloquea el guardado parcial | Aprobada; contrato documentado |
| `test_django_admin_rejects_invalid_service_values` | 5 | Alta HTTP en Django Admin muestra errores sin persistencia | Aprobadas |
| `test_django_admin_creates_and_edits_valid_service` | 1 | Alta y edición HTTP válidas en Django Admin | Aprobada |
| `test_unrepresentable_duration_does_not_cause_server_error` | 2 | Error de formulario controlado para intervalos no representables | Aprobadas; SVC-02 corregido |
| `test_saved_appointment_preserves_full_service_duration` | 1 | Rechazo controlado sin guardar una cita con días truncados | Aprobada; SVC-02 corregido |

Actualmente no quedan marcas `xfail` de SVC-01 ni SVC-02. Antes de corregir SVC-01
se ejecutaron con `--runxfail`
los diez casos originales para obtener evidencia explícita de siete fallos.
Después de modificar el modelo, se ejecutaron las siete comprobaciones de SVC-01
originales con `--runxfail`: todas aprobaron (3 casos de SVC-02 deseleccionados,
0,72 s). Solo entonces se retiraron las marcas de SVC-01.
Tras la nueva decisión funcional, los tres escenarios de SVC-02 se ejecutaron
sin efecto de `xfail`: 3 aprobadas en 0,77 s. Después se retiraron sus marcas y
se exigió error por campo con un mensaje que menciona el mismo día.

Los 29 casos nuevos de Agenda cubren duración personalizada menor y mayor que
la estimación, valor predeterminado cuando el campo se omite o queda vacío,
entradas inválidas, medianoche exacta y posterior, números muy grandes, fin a
las 23:59, servicios con estimaciones largas y citas más cortas, conflictos al
extender, intervalos adyacentes, cancelaciones, historial tras cambios del
catálogo, conservación al guardar notas, permiso de trabajador, cálculo directo
del modelo y renderizado del campo editable. La ejecución enfocada de estos
29 casos más las 40 regresiones terminó con **69 aprobadas en 4,42 s**.

## 4. Integración entre Servicios y Agenda

Las tres pruebas de `test_integration.py` permanecen aprobadas en la línea base:

1. Alta de servicio por HTTP, persistencia y registro de una cita por el
   formulario real de Agenda. Verifica claves relacionadas, usuario creador,
   precio, duración de 45 minutos, inicio 10:15 y fin 11:00. Cambiar el precio
   del catálogo de 35000 a 50000 conserva el precio de la cita en 35000.
2. Desactivación por el CRUD: el servicio desaparece del selector, el POST
   manual con su ID genera `invalid_choice` y no crea ni altera citas.
3. Intento de eliminación de un servicio con una cita creada por HTTP: se
   conservan los registros y se informa del bloqueo y la alternativa de desactivar.

Se usa el ORM únicamente para preparar usuarios, clientes y profesionales de
prueba. Las operaciones de Servicios y el alta de citas recorren vistas y
formularios reales. Estas pruebas no ejecutan JavaScript en un navegador.

## 5. Defectos reproducidos y causas

### SVC-01 — Reglas distintas según la vía de escritura

- **Entradas:** duración `0`, o precio `-1`, con el resto de campos válidos.
- **Resultado anterior a la corrección:** `Service.full_clean()` no generaba `ValidationError` y
  `Service.save()` permite la escritura individual en SQLite.
- **Comparación:** `ServiceForm` y las vistas de alta/edición sí rechazan esos
  valores y conservan los datos anteriores. Duración 1 y precio 0 son válidos.
- **Causa:** `PositiveIntegerField` admite cero. El campo decimal no tiene una
  validación de mínimo equivalente a la del formulario. `Service` no implementa
  validación adicional ni invoca `full_clean()` al guardar.
- **Impacto:** un consumidor que omita `ServiceForm` puede persistir valores
  incompatibles con las reglas que ya aplica el CRUD. No se comprobó si existen
  registros de ese tipo en MySQL; no se consultó esa base.
- **Estado actual:** corregido con autorización explícita del usuario. La
  validación y la escritura individual rechazan esos valores con errores por campo.

### SVC-02 — Pérdida del cambio de día al calcular la cita

Los servicios se crearon por el CRUD antes de intentar agendar:

| Duración | Inicio | Resultado observado |
| ---: | --- | --- |
| 1440 minutos | 10:00 | HTTP 500; fin calculado 10:00 y rechazado en `Appointment.save()` |
| 90 minutos | 23:30 | HTTP 500; el fin 01:00 del día siguiente no se representa con el modelo actual |
| 1500 minutos | 10:00 | HTTP 302 y cita persistida de 10:00 a 11:00: 60 minutos en lugar de 1500 |

- **Causa anterior a la corrección:** Agenda sumaba la duración y conservaba solamente `.time()`, perdiendo
  la fecha final. La cita contiene una sola fecha y dos horas. El modelo exige
  que la hora final sea posterior a la inicial, pero el formulario no transforma
  estos intervalos en un error controlado antes de guardar.
- **Impacto:** error de servidor o duración persistida incorrecta. El caso de
  90 minutos demuestra que un máximo fijo de 24 horas en Servicios no resolvería
  todos los cruces de medianoche. El servidor admite esa hora en el formulario;
  este ensayo no propone ampliar el horario de operación.
- **Estado actual:** corregido con la regla autorizada: cada cita puede tener
  una duración planificada propia y debe terminar el mismo día. Las observaciones
  de la tabla son la reproducción histórica, no el comportamiento actual.

## 6. Corrección implementada y compatibilidad

**SVC-01 corregido:** `Service.clean()` normaliza los espacios del nombre como
`ServiceForm`, rechaza el nombre vacío, duración menor o igual que cero, duración
superior a 2147483647 (el máximo que ya tenía el formulario) y precio negativo.
`Service.save()` ejecuta `full_clean()` antes de delegar al guardado de Django.
Los campos existentes siguen validando nombre de hasta 150 caracteres, precio
entero de hasta 12 dígitos, campos obligatorios y tipos numéricos finitos.
No se cambiaron campos, formularios, vistas, permisos ni Django Admin.

Se preserva precio cero y duración mínima 1. Las nuevas pruebas cubren nombres
vacíos, solo espacios y demasiado largos, duración cero/negativa/no numérica o
fuera del máximo, precio negativo/fraccionario/excesivo, NaN e Infinity.
Las conversiones inválidas mantienen sus errores de validación sin producir
errores de comparación en `clean()`.

**Cambio de contrato autorizado:** `save()` y `objects.create()` ahora lanzan
`ValidationError` antes de persistir valores inválidos. También se valida toda
la instancia en `save(update_fields=...)`, incluidos campos no seleccionados;
una instancia con otro campo inválido se rechaza. Las pruebas verifican tanto
este comportamiento como guardados parciales válidos. No se introdujeron rutas
alternativas de escritura ni se cambió el comportamiento de operaciones masivas.
La normalización del nombre modifica la instancia; en un guardado parcial solo
se persisten los campos indicados por el llamador, según el contrato de Django.

`bulk_create()`, `QuerySet.update()` y SQL directo omiten `save()` y no quedan
protegidos por esta corrección. No se añaden restricciones SQL ni se promete
integridad para esas vías. Una fila antigua inválida, si existiera, no podrá
guardarse mediante `save()` hasta corregir la instancia; no se inspeccionaron
ni modificaron registros reales.

La comprobación `makemigrations services --check --dry-run
--settings=config.settings_test` terminó con salida 0 y
`No changes detected in app 'services'`. No se generaron ni aplicaron
migraciones en la base real; los tests solo preparan tablas en memoria.

### SVC-02 y duración planificada independiente

La decisión del proyecto establece citas que comienzan y terminan el mismo día.
Se implementó `duration_minutes` como campo entero positivo del formulario, sin
añadir una columna: la duración se persiste mediante la diferencia entre las
horas `start_time` y `end_time` de la fecha existente.

- Al seleccionar un servicio, JavaScript carga su estimación como valor inicial.
  El usuario puede modificarla y ver la hora final antes de guardar.
- Si un cliente HTTP omite la duración o la envía vacía, se usa la estimación del
  servicio. Al reconstruir un formulario para una cita existente se usa su
  intervalo histórico, y no la estimación actual del catálogo.
- El formulario calcula la hora final usando la duración elegida. Si el
  intervalo llega a medianoche o la supera, devuelve un error comprensible en
  el campo de duración y conserva el modal abierto, sin guardar una cita nueva.
- La comprobación compara primero los segundos restantes del día, antes de
  construir un `timedelta`; evita desbordamientos para duraciones muy grandes.
- El cálculo automático de `Appointment.save()` reutiliza la misma función si
  no se proporciona una hora final. Un intervalo imposible genera
  `ValidationError` en esa vía de programación; el flujo HTTP lo valida en el
  formulario y no produce HTTP 500 por cruce de medianoche.
- Los conflictos se comprueban con la hora final personalizada. Se conserva
  la exclusión de citas canceladas y se permiten intervalos adyacentes.
- No se modifica el servicio al guardar la cita, ni se recalculan intervalos
  históricos al cambiar el catálogo o el estado de una cita.
- La duración personalizada se conserva cuando se vuelve a mostrar un formulario
  inválido; cambiar de servicio carga una nueva estimación, sin recortes automáticos.

No se añadió un máximo diario al catálogo. Se conserva el límite técnico ya
existente de 2147483647 minutos de Servicios. Una estimación larga puede usarse
en una cita con duración planificada más corta. No se incorporó soporte para
citas de varios días ni nuevas restricciones de horario de apertura.

La comprobación global `makemigrations --check --dry-run
--settings=config.settings_test` informó `No changes detected`, sin crear
migraciones. No se alteró la estructura de la base de datos.

## 7. Evidencias y reproducción

Desde la raíz `studiogest-web`, en PowerShell:

```powershell
# Línea base preservada: 36 casos.
.\.venv\Scripts\python.exe -m pytest apps/services/tests.py apps/services/test_integration.py -v

# Regresiones actuales y pruebas de duración personalizada.
.\.venv\Scripts\python.exe -m pytest apps/appointments/test_duration.py apps/services/test_regressions.py -q

# Suite completa actual del proyecto; no hay xfail.
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --junitxml=docs/evidencias/studiogest_suite.xml -o junit_logging=no -o junit_log_passing_tests=false
```

- [JUnit de defectos reproducidos](evidencias/servicios_defectos_reproducidos.xml):
  **7 fallos, 3 aprobadas en 1,22 s**, salida 1. Se conserva intacto como
  evidencia histórica anterior a la corrección; no describe el código actual.
- [JUnit de regresiones tras corregir SVC-01](evidencias/servicios_regresiones_svc01_corregido.xml):
  evidencia histórica: **37 aprobadas y 3 `xfail` en 8,81 s**, salida 0.
- [JUnit de Servicios tras SVC-01](evidencias/servicios_suite.xml): evidencia histórica
  **73 aprobadas, 3 `xfail` y 31 subpruebas aprobadas en 62,51 s**, salida 0.
  Se descubrieron 76 casos principales (36 anteriores y 40 de regresión).
  Cero fallos inesperados y cero errores de infraestructura. Los tres `xfail`
  correspondían exclusivamente a SVC-02 y no se contabilizan como aprobados.
  Como comparación histórica, antes de corregir SVC-01 se obtuvieron 39
  aprobadas, 7 `xfail` y 31 subpruebas aprobadas en 53,61 s.

- Resultado histórico tras SVC-02, antes de ampliar precios:
  **198 aprobadas y 74 subpruebas aprobadas en 34,09 s**, salida 0,
  **0 fallos, 0 errores y 0 `xfail`**. Incluye las 76 pruebas de Servicios,
  las 29 pruebas nuevas de duración de Agenda y las demás pruebas Python
  descubiertas del proyecto.

En los XML históricos, los `xfail` aparecen como `skipped` de tipo `pytest.xfail`, no como
aprobaciones. El contador `tests` incluye las subpruebas; los nodos `testcase`
representan los casos principales: el XML histórico de Servicios tiene `tests=107` (76 casos
más 31 subpruebas), 76 nodos `testcase`, 0 fallos, 0 errores y 3 `skipped`.
Los contadores actuales del proyecto se documentan en la sección de precios.
Los tiempos de consola incluyen una pequeña
sobrecarga respecto al atributo `time` del XML.

Los XML contienen nombres de pruebas y datos sintéticos, no contraseñas,
credenciales ni contenido de `.env`. Se desactivó la exportación de logs
capturados y se anonimiza el nombre del equipo en los artefactos entregados.
Regenerarlos con los comandos vuelve a añadir los metadatos propios de pytest.

Se comprobó además el JavaScript real de la plantilla mediante Node y un DOM
simulado: valor inicial, ajuste manual, conservación tras errores, cambio de
servicio y previsualización de medianoche. La primera ejecución de esa
comprobación externa tuvo una discrepancia de codificación del texto acentuado
al pasar por PowerShell; se corrigió el verificador, sin cambios de negocio, y
la comprobación terminó aprobada. Esto no sustituye una prueba de navegador.

## 8. Riesgos, exclusiones y conclusiones

**Errores comprobados y corregidos:** SVC-01 en escrituras individuales y SVC-02
en el cálculo temporal. Sus pruebas son normales y aprobaron; no quedan `xfail`.

**Riesgos no reproducidos aquí:** escrituras masivas, SQL externo, concurrencia
entre altas de citas y diferencias del motor MySQL. No se presentan como defectos
comprobados ni como corregidos. Django Admin sí se verificó por HTTP para
altas inválidas, alta válida y edición válida, sin cambiar su implementación.

**Fuera del alcance/requisitos confirmados:** búsqueda y paginación del catálogo,
asignación de especialidades a servicios, nuevos horarios de apertura y soporte
de citas de varios días. Su ausencia no se clasificó automáticamente como error.

La corrección alinea las reglas del formulario, el modelo y la escritura
individual, conservando el CRUD y Django Admin. La protección de historial y
los permisos se mantienen cubiertos por la suite original. Siguen sin garantizarse
las escrituras masivas. Los intervalos que cambian de día se rechazan conforme
a la nueva regla. No se probaron carreras entre escrituras simultáneas.
La cobertura automatizada no implica ausencia de
defectos. La entrega debe distinguir aprobaciones, fallos esperados y correcciones
pendientes; las aprobaciones con SQLite no acreditan comportamiento en MySQL.

## 9. Precios personalizados y descuentos autorizados

### Implementación y persistencia

`Appointment.price_cop` sigue siendo el total final que consumen Agenda,
Dashboard y Reportes. Se añadieron `catalog_price_cop`, `adjusted_price_cop`,
`discount_type`, `discount_value`, `discount_amount_cop` y `pricing_reason`.
Los cinco campos de valores/tipo admiten `NULL`; el motivo admite texto vacío.
La migración añade columnas sin operaciones de reconstrucción del historial.

Agenda toma el precio de catálogo desde la base, permite al administrador
personalizar la base y elegir descuento porcentual o fijo, y registra el motivo
opcional. Los cálculos se centralizan en `appointments/pricing.py`, con `Decimal`
y `ROUND_HALF_UP`. Se admiten porcentajes con dos decimales, COP enteros de hasta
12 dígitos, descuentos de hasta el 100 % y total cero. Los descuentos fijos no
pueden superar la base. El servidor ignora los importes derivados enviados por
un administrador y calcula el resultado por sí mismo.

El navegador presenta catálogo, base ajustable, valor descontado y total.
La previsualización usa enteros `BigInt` y redondeo equivalente, evitando pérdidas
de precisión al multiplicar importes grandes. Al mostrar errores del formulario,
se conservan los datos introducidos. La validación del servidor es autoritativa.

El defecto de tratar cero como un precio ausente se corrigió en formulario y
modelo: solo `None` activa el precio predeterminado. Guardar o completar una
cita de precio cero ya no lo reemplaza por el catálogo. El guardado valida el
desglose, pero no vuelve a aplicar descuentos ni consulta el catálogo para
recalcular importes ya existentes.

Los trabajadores conservan el alta de citas y la duración personalizada. No
reciben controles económicos y sus POST con campos económicos se rechazan con
errores de formulario, sin guardar citas. `is_staff` por sí solo no otorga
permisos de ajuste; se protege también la edición en Django Admin. Los
superusuarios mantienen el comportamiento de administrador existente.

Las ediciones de notas o de estado conservan el historial. Un formulario de
cita antigua no permite reconstruir un detalle económico desconocido desde el
catálogo actual. No se incorporó una nueva pantalla de edición económica de
citas antiguas.

### Evidencia automatizada de esta ampliación

| Grupo | Verificaciones |
| --- | --- |
| Precio y cálculo | Catálogo automático, base personalizada, porcentajes, importes fijos, 100 %, cero y redondeo de mitades |
| Validación | Negativos, fracciones COP, máximo, NaN/Infinity, porcentaje superior a 100, descuento fijo excesivo y desglose inconsistente |
| Permisos | POST manipulado por trabajador, controles ocultos, superusuario, campos derivados falsificados y trabajador staff en Django Admin |
| Historial | Cambios del catálogo, completar repetidamente, cancelar, editar notas y citas antiguas con importe cero o positivo |
| Integración | Precio final sumado una sola vez en Dashboard/Reportes; duración personalizada conservada |
| Migración | Pasar de `0001` a `0002` preserva importes previos y deja desconocidos los nuevos detalles |

La ejecución enfocada terminó con **53 aprobadas en 2,01 s**. Se ejecutó además
`node apps/appointments/pricing_frontend_test.cjs`: 8 escenarios de cálculo,
9 entradas inválidas y comprobaciones DOM aprobadas. Las pruebas usan el archivo
JavaScript real; no sustituyen una prueba visual de navegador.

La [suite completa actual en JUnit](evidencias/studiogest_suite.xml) terminó con
**251 pruebas aprobadas y 74 subpruebas aprobadas en 89,95 s**, salida 0.
Hubo **0 fallos, 0 errores, 0 omitidas y 0 `xfail`**. Incluye las 198 pruebas
anteriores y los 53 casos nuevos. El XML tiene 251 nodos `testcase` y el contador
`tests=325` al sumar las 74 subpruebas. Se conserva el conteo de subpruebas
separado para no presentarlas como pruebas principales adicionales.

Comando de reproducción de toda la suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --junitxml=docs/evidencias/studiogest_suite.xml -o junit_logging=no -o junit_log_passing_tests=false
```

`manage.py check --settings=config.settings_test` informó cero problemas.
`makemigrations --check --dry-run --settings=config.settings_test` indicó
`No changes detected`: la migración generada concuerda con los modelos.

### Ventas y aplicación pendiente en MySQL

Se documentó el [contrato de importes de citas y Ventas](contrato_importes_citas_ventas.md).
Ventas todavía no tiene operaciones de cobro. Su futura integración debe consumir
`price_cop` como total ya descontado, sin volver a aplicar el descuento. La
idempotencia de cobros reales se probará cuando exista esa funcionalidad.

La migración solo fue probada en SQLite. Antes de aplicar en MySQL se requiere
revisión del SQL y del plan, copia de seguridad, prueba de restauración y
evaluación de bloqueo/compatibilidad en una copia. El código actualizado necesita
las columnas nuevas; coordinar su despliegue con la migración. No se realizó
ninguna de esas operaciones sobre MySQL ni se autoriza implícitamente su ejecución.

## 10. Alcance de la publicación

Esta versión pública conserva los resultados automatizados con datos sintéticos. Los respaldos, las credenciales, las rutas privadas y las evidencias operativas de bases con datos reales se mantienen fuera del repositorio. Los ensayos locales de MySQL no se presentan como pruebas públicas ni como autorización para migrar una base real.
