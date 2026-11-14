# Contrato económico entre Agenda y los futuros cobros de Ventas

## Importe que debe consumir Ventas

`Appointment.price_cop` es el **total final de la cita después del descuento**,
expresado en pesos colombianos enteros. Los consumidores deben utilizar ese
importe directamente. Nunca deben volver a restarle `discount_amount_cop`
ni aplicar `discount_value` a ese total.

Ejemplo: catálogo 250000, precio personalizado 320000, descuento 10 %, importe
descontado 32000, `price_cop=288000`. El cobro previsto es 288000, no 259200.

El precio del catálogo y los demás campos son información histórica y de
desglose. No se recalculan desde `Service.price_cop` al completar una cita,
al consultar reportes ni al crear un futuro cobro.

## Campos y estados históricos

| Campo | Significado |
| --- | --- |
| `catalog_price_cop` | Precio del catálogo observado al registrar la cita |
| `adjusted_price_cop` | Base acordada para esa cita, antes del descuento |
| `discount_type` | `NONE`, `PERCENT` o `FIXED` |
| `discount_value` | Porcentaje solicitado o importe fijo |
| `discount_amount_cop` | Importe efectivo descontado, ya calculado |
| `price_cop` | Total final, incluido cero como importe válido |
| `pricing_reason` | Motivo opcional del acuerdo |

Los cinco campos nuevos numéricos/de tipo aceptan `NULL`: significa detalle
desconocido. El motivo puede estar vacío. La migración no reconstruye valores
del pasado con el catálogo actual. Las citas antiguas conservan `price_cop`
sin modificación; un consumidor no debe deducir descuentos que no se guardaron.

## Cálculo autorizado

Los importes COP son enteros no negativos de hasta 12 dígitos. El porcentaje
admite dos decimales, entre 0 y 100. El descuento porcentual se calcula con
`Decimal` y `ROUND_HALF_UP` al peso más cercano. El total es la base personalizada
menos el importe descontado. Un descuento fijo no puede superar la base.
Descuentos del 100 % y totales cero están permitidos.

Solo administradores pueden enviar ajustes económicos desde Agenda. Los
trabajadores pueden seguir agendando con el precio del catálogo, pero el
servidor rechaza sus intentos de enviar campos económicos, incluidos los campos
derivados. Para administradores, los totales y el catálogo enviados manualmente
no se utilizan: se calculan o consultan en el servidor.

## Límite de la implementación actual

Ventas sigue siendo una pantalla informativa, sin modelos ni operaciones de
cobro. No se implementó una integración de cobros inexistente ni se equiparó
una cita completada a un pago recibido. Las pruebas sí verifican que los
consumidores actuales (Dashboard y Reportes) suman el importe final una sola vez
y que completar repetidamente una cita no vuelve a descontar su precio.

Al implementar Ventas habrá que probar además la vinculación cita/cobro y la
protección frente a cobros duplicados. Esa idempotencia de cobros futuros no
queda garantizada por el cálculo de descuentos de Agenda.

## Antes de migrar MySQL

La migración `appointments.0002_appointment_pricing` está generada y probada
únicamente en SQLite en memoria, incluida una actualización desde `0001` con
citas sintéticas de importe cero y positivo. No se ejecutó sobre MySQL.

Antes de aplicar en MySQL: revisar el SQL y el plan sobre una copia, preparar
una copia de seguridad y su restauración, confirmar versión del motor, permisos
DDL, espacio y posible bloqueo al añadir columnas. Coordinar el despliegue del
código con la migración: el código actualizado consulta los campos nuevos y
necesita el esquema actualizado. La aplicación a MySQL requiere autorización
separada. No se incluyen comandos de ejecución contra la base real aquí.
