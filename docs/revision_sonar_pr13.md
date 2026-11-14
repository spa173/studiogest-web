# Revisión de las observaciones de SonarCloud — PR #13

## Alcance

Refactorización en la rama `luisa`, sin cambiar precios, descuentos, duración,
permisos ni el modelo de datos. No se modificaron la configuración de SonarCloud,
`.env`, Inventario ni las migraciones existentes. No se añadieron supresiones.

Se revisaron los fragmentos locales señalados por el usuario. La API pública
de SonarCloud no fue accesible mediante la herramienta disponible, por lo que
no se confirmó la clave, categoría o estado remoto de cada observación. El
reanálisis del PR sigue siendo necesario para confirmar el resultado del Quality Gate.

## Cambios realizados

| Observación | Tratamiento |
| --- | --- |
| Ejecución dinámica en `pricing_frontend_test.cjs` | Eliminados `node:vm`, la lectura del archivo como texto y `runInContext`. Las pruebas importan estáticamente el módulo y llaman a su función exportada con un DOM y catálogo simulados. |
| Tuplas de longitudes diferentes en Django Admin | `get_readonly_fields()` devuelve listas nuevas en ambas ramas. Se mantienen los siete campos económicos de solo lectura para trabajadores y ninguno para administradores/superusuarios. `list_display` no cambia. |
| Complejidad de `Appointment.clean()` | Delega en `_validate_pricing()`, `_validate_interval()` y `_validate_conflicts()`, conservando el orden de validación, las condiciones y los mensajes. La cifra definitiva de complejidad deberá confirmarla SonarCloud. |
| Afirmaciones compuestas en `test_pricing.py` | Separadas tanto las expresiones con `and` señaladas como las comparaciones encadenadas, conservando cada comprobación individual. |
| Etiqueta accesible de la tarifa | La etiqueta incorpora `for="priceDisplay"`, correspondiente al identificador existente del campo. |
| `null=True` en `discount_type` | Se conserva por una necesidad funcional de historial. Se añade un comentario aclaratorio y se deja pendiente la revisión justificada del hallazgo en SonarCloud, sin suprimir la regla. |

La función JavaScript acepta opcionalmente el documento y el catálogo para
probarla. Sus valores predeterminados siguen siendo los objetos del navegador;
no cambia ningún cálculo ni el comportamiento del formulario. Se conservan los
8 escenarios numéricos, 9 entradas inválidas y las comprobaciones del DOM.

Se añadieron tres casos de regresión para verificar listas de campos de solo
lectura y columnas de Django Admin en los roles administrador, trabajador y
superusuario. La prueba HTTP existente de trabajador staff también se conserva.

## Evaluación de seguridad de la ejecución dinámica

Antes se ejecutaba el texto de un archivo local fijo del repositorio. No se
identificó una entrada de peticiones, clientes o usuarios que alcanzara ese
texto, ni se demostró una inyección explotable. Esto no justifica tratar `vm`
como un aislamiento seguro: Node explica que ese módulo no es un mecanismo de
seguridad. El patrón sensible era innecesario en estas pruebas y se eliminó,
en lugar de ocultarlo o declarar automáticamente un falso positivo.

La clasificación formal como vulnerabilidad o Security Hotspot debe revisarse
en el hallazgo de SonarCloud. Esta revisión local no cambia su estado remoto.

## Justificación de `null=True`: pendiente de revisión de SonarCloud

El campo es un `CharField`, para el que la recomendación general de Django
es evitar dos representaciones vacías. Aquí los estados tienen significados
distintos y explícitos:

- `NULL`: el detalle del descuento histórico no se conoce.
- `NONE`: se registró explícitamente una cita sin descuento.
- `PERCENT` o `FIXED`: se conoce el tipo de descuento registrado.

Las citas antiguas mantienen los cinco campos económicos nuevos en `NULL`;
no se reconstruyen datos desde el catálogo actual. Reemplazar `NULL` por `NONE`
inventaría información histórica. Reemplazarlo por una cadena vacía también
cambiaría el contrato de detalle económico completo o totalmente desconocido
que valida el modelo. Además, quitar la opción cambiaría el estado de migración
y requeriría un plan de conversión de los registros existentes.

No se realizó ese cambio. Las pruebas existentes de historial y de actualización
de `0001` a `0002` en SQLite verifican esta distinción. Una modificación futura
del modelo de datos requerirá autorización previa; no es una corrección de estilo.

## Verificación

Las comprobaciones se ejecutan sobre una copia temporal de los archivos
versionados más los cambios revisados. No se copia `.env`, no se proporcionan
credenciales MySQL y `config.settings_test` selecciona SQLite en memoria.

```text
node apps/appointments/pricing_frontend_test.cjs
python manage.py check --settings=config.settings_test
python manage.py makemigrations --check --dry-run --settings=config.settings_test
python -m pytest
git diff --check
```

JavaScript: aprobados los 8 cálculos, 9 escenarios inválidos y comportamiento
del DOM. Django check: cero problemas. La comprobación de migraciones informó
`No changes detected`, sin generar ni aplicar una migración de MySQL.
La suite completa terminó con **254 pruebas aprobadas en 101,70 s**, salida 0,
sin fallos ni errores. Son las 251 pruebas anteriores más los tres casos nuevos
de contrato de Django Admin. La ejecución local usó Python 3.13.13, Django
5.2.18, pytest 9.2.0 y pytest-django 4.14.0. `git diff --check` también terminó
sin errores. No se generó ninguna migración ni se modificó MySQL.

Referencias oficiales:

- [Node.js: VM](https://nodejs.org/api/vm.html).
- [Django 5.2: get_readonly_fields](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.get_readonly_fields).
- [Django 5.2: null](https://docs.djangoproject.com/en/5.2/ref/models/fields/#null).
