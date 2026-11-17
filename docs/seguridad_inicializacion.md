# Inicialización segura de cuentas

Los comandos `create_initial_users` y `seed_initial_catalog` no incluyen claves
predeterminadas ni imprimen contraseñas. Este cambio no rota credenciales de
cuentas existentes ni borra su historial.

## Uso interactivo

Desde una terminal local, ejecutar el comando correspondiente. Cada cuenta nueva
requiere una contraseña oculta y su confirmación. Se aplican los validadores de
contraseña configurados en Django. Si no existe una entrada oculta disponible,
el comando se detiene antes de crear datos, sin recurrir a entrada visible.

`create_initial_users` conserva la creación del administrador y trabajador con
sus roles y permisos originales. Las cuentas existentes no se actualizan, aunque
su rol o contraseña hayan cambiado. No se crea una cuenta de caja adicional.

`seed_initial_catalog` es una carga de demostración; no ejecutarlo en bases con
datos reales. Conserva usuarios, roles y claves existentes. Al repetirlo, las
citas existentes se mantienen: no se borran ni se reemplazan precios históricos.
La coincidencia de una cita de muestra usa profesional, fecha y hora inicial.

## Automatización

Usar `--no-input` y proporcionar secretos mediante variables del proceso desde
un gestor de secretos; no incluirlos en argumentos, archivos versionados ni logs.

- `INITIAL_ADMIN_PASSWORD`: contraseña de la cuenta administradora nueva.
- `INITIAL_WORKER_PASSWORD`: contraseña de la cuenta trabajadora nueva.
- `INITIAL_CATALOG_<USUARIO_NORMALIZADO>_PASSWORD`: una contraseña por cuenta
  profesional nueva del catálogo. El nombre de usuario se convierte a mayúsculas
  y cada carácter que no sea letra ASCII o dígito se sustituye por `_`.

Los comandos indican el nombre de la variable faltante, nunca su valor. No
requieren contraseñas para cuentas que ya existen. Todas las contraseñas
necesarias se validan antes de escribir datos; las operaciones son transaccionales.
No agregar valores a `.env` como parte de esta corrección ni imprimir el entorno.

## Pruebas

Las credenciales de pruebas se generan en ejecución con `secrets.token_urlsafe`.
La suite usa `config.settings_test`, SQLite en memoria y datos sintéticos.
Se verifica la autenticación, los roles, la ausencia de contraseñas en la salida,
el rechazo de entradas inseguras y la conservación de cuentas y citas existentes.

## Cuentas existentes y rotación

La coincidencia con los identificadores de los comandos solo permite identificar
candidatos; no prueba su origen ni qué contraseña conservan. Tampoco la ausencia
de coincidencias descarta cuentas renombradas o credenciales reutilizadas.
La auditoría no debe intentar iniciar sesión con claves publicadas ni mostrar
hashes, contraseñas o datos personales.

Antes de rotar cuentas reales, obtener autorización específica y confirmar sus
identificadores localmente. Un operador autorizado puede utilizar
`python manage.py changepassword <identificador_local>` con entrada oculta y una
contraseña nueva, única y almacenada en su gestor de contraseñas. Mantener los
roles y permisos, revisar las sesiones afectadas y comprobar el acceso de forma
controlada. No ejecutar cargas de demostración para rotar contraseñas.

## Hallazgo histórico de GitGuardian

El incidente `40123229` requiere revisión manual después de corregir el código
y rotar las credenciales que puedan seguir utilizándose. Retirar las cadenas del
árbol actual no las elimina del historial. Registrar la corrección, la revisión
de cuentas y la rotación sin incluir valores secretos. No clasificar el incidente
como falso positivo mientras no se descarte su uso fuera de pruebas.

Un responsable debe revisar las ocurrencias y el resultado del nuevo análisis en
GitGuardian y aplicar el estado de resolución que corresponda a la evidencia.
No desactivar el detector, añadir exclusiones globales ni reescribir el historial
compartido como sustituto de la rotación. No publicar cambios ni cerrar el
incidente sin autorización.
