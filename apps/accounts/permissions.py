"""
Helpers centralizados de permisos por rol (RBAC).

Política aplicada (mínimo privilegio, ver documentación de entrega):
- ADMIN (is_admin, incluye superuser): acceso completo.
- CAJA_RECEPCION (is_cashier): Ventas/Caja y Reportes (lectura); Clientes
  listar/ver/crear/editar; Dashboard/Agenda/Inventario/Catálogo/Profesionales
  en lectura. Sin escritura en servicios/profesionales/inventario ni /admin/.
- TRABAJADOR (is_worker): Dashboard y Agenda (ver/crear; completar/cancelar
  propias o reglas existentes); Clientes listar/ver/crear/editar; Inventario,
  Servicios y Profesionales en lectura. Sin Ventas/Caja, sin Reportes, sin
  /admin/. Sin eliminación de clientes.
- Todas las vistas de negocio requieren autenticación (se aplica en vistas).
"""

from django.core.exceptions import PermissionDenied


def _is(user, attr):
    return bool(user and user.is_authenticated and getattr(user, attr, False))


def is_admin(user):
    return _is(user, 'is_admin')


def is_cashier(user):
    return _is(user, 'is_cashier')


def is_worker(user):
    return _is(user, 'is_worker')


# --- Ventas y caja ---------------------------------------------------------

def can_manage_sales(user):
    """Acceso operativo a Ventas y Caja: ADMIN y CAJA_RECEPCION."""
    return is_admin(user) or is_cashier(user)


# --- Reportes --------------------------------------------------------------

def can_view_reports(user):
    """Acceso de lectura a Reportes: ADMIN y CAJA_RECEPCION."""
    return is_admin(user) or is_cashier(user)


# --- Clientes --------------------------------------------------------------

def can_access_customers(user):
    """Listar/ver/crear/editar clientes: todos los roles de negocio."""
    return is_admin(user) or is_cashier(user) or is_worker(user)


def can_delete_customers(user):
    """Eliminar clientes: solo ADMIN (regla preexistente)."""
    return is_admin(user)


def can_view_customer_sales_history(user):
    """Historial de ventas/compras en detalle de cliente: ADMIN y CAJA_RECEPCION.

    Supuesto: se oculta a TRABAJADOR por mínimo privilegio; el historial de
    citas permanece visible para atención.
    """
    return is_admin(user) or is_cashier(user)


# --- Agenda / citas --------------------------------------------------------

def can_view_agenda(user):
    """Ver agenda/calendario: todos los roles de negocio."""
    return is_admin(user) or is_cashier(user) or is_worker(user)


def can_create_appointments(user):
    """Crear citas: ADMIN y TRABAJADOR (CAJA_RECEPCION es lectura en Agenda)."""
    return is_admin(user) or is_worker(user)


def can_change_appointment_status(user, appointment):
    """Completar/cancelar: ADMIN o el profesional dueño de la cita (trabajador)."""
    if is_admin(user):
        return True
    return is_worker(user) and appointment.professional.user_id == user.id


# --- Inventario ------------------------------------------------------------

def can_view_inventory(user):
    """Lectura de inventario: todos los roles de negocio."""
    return is_admin(user) or is_cashier(user) or is_worker(user)


def can_manage_inventory(user):
    """Escritura en inventario (altas/ediciones/ajustes): solo ADMIN."""
    return is_admin(user)


def can_view_inventory_history(user):
    """Historial de entradas de inventario (lectura): todos los roles."""
    return is_admin(user) or is_cashier(user) or is_worker(user)


def can_view_inventory_costs(user):
    """Ver costos de adquisición/totales de inventario.

    Supuesto razonable: visible para ADMIN y CAJA_RECEPCION (operación/caja);
    oculto a TRABAJADOR por mínimo privilegio.
    """
    return is_admin(user) or is_cashier(user)


# --- Servicios y profesionales --------------------------------------------

def can_manage_services(user):
    """Crear/editar/eliminar servicios: solo ADMIN."""
    return is_admin(user)


def can_manage_professionals(user):
    """Gestionar profesionales: solo ADMIN (regla preexistente)."""
    return is_admin(user)


# --- Dashboard -------------------------------------------------------------

def can_view_financial_dashboard(user):
    """Métricas financieras/ventas en dashboard.

    Supuesto razonable: visibles para ADMIN y CAJA_RECEPCION; ocultas a
    TRABAJADOR, que no accede a Ventas/Caja ni Reportes.
    """
    return is_admin(user) or is_cashier(user)


def require_permission(check, message='No tienes permisos para acceder a esta sección.'):
    """Decorador simple para vistas basadas en función."""
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if not check(request.user):
                raise PermissionDenied(message)
            return view_func(request, *args, **kwargs)
        _wrapped.__name__ = getattr(view_func, '__name__', 'wrapped')
        _wrapped.__doc__ = view_func.__doc__
        return _wrapped
    return decorator
