from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer

User = get_user_model()


class ClientesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='admin@t.co', email='admin@t.co', password='Clave#12345', role=User.Role.ADMIN)
        cls.worker = User.objects.create_user(
            username='trab@t.co', email='trab@t.co', password='Clave#12345', role=User.Role.WORKER)
        cls.ana = Customer.objects.create(name='Ana Gómez', phone='3001112233', is_vip=True)
        cls.luis = Customer.objects.create(name='Luis Pérez', phone='3109998877')

    def entrar(self, usuario):
        self.client.force_login(usuario)

    def test_requiere_iniciar_sesion(self):
        r = self.client.get(reverse('customers:list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_lista_y_busqueda(self):
        self.entrar(self.worker)
        r = self.client.get(reverse('customers:list'))
        self.assertContains(r, 'Ana Gómez')
        self.assertContains(r, 'Luis Pérez')
        r = self.client.get(reverse('customers:list'), {'q': 'Ana'})
        self.assertContains(r, 'Ana Gómez')
        self.assertNotContains(r, 'Luis Pérez')

    def test_filtro_vip(self):
        self.entrar(self.worker)
        r = self.client.get(reverse('customers:list'), {'vip': '1'})
        self.assertContains(r, 'Ana Gómez')
        self.assertNotContains(r, 'Luis Pérez')

    def test_crear_cliente_valido(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:create'), {'name': 'Mario  Ruiz', 'phone': '320 555 1212'})
        self.assertRedirects(r, reverse('customers:list'))
        self.assertTrue(Customer.objects.filter(name='Mario Ruiz').exists())

    def test_rechaza_telefono_repetido(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:create'), {'name': 'Otro Cliente', 'phone': '3001112233'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Ya existe un cliente con este teléfono')

    def test_rechaza_telefono_invalido_y_nombre_corto(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:create'), {'name': 'Al', 'phone': 'abc'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Customer.objects.count(), 2)

    def test_editar_cliente(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:update', args=[self.luis.pk]),
                             {'name': 'Luis P. Pérez', 'phone': '3109998877', 'is_vip': 'on'})
        self.assertRedirects(r, reverse('customers:list'))
        self.luis.refresh_from_db()
        self.assertEqual(self.luis.name, 'Luis P. Pérez')
        self.assertTrue(self.luis.is_vip)

    def test_trabajador_no_puede_eliminar(self):
        self.entrar(self.worker)
        r = self.client.post(reverse('customers:delete', args=[self.luis.pk]))
        self.assertRedirects(r, reverse('customers:list'))
        self.assertTrue(Customer.objects.filter(pk=self.luis.pk).exists())

    def test_admin_elimina_cliente_sin_citas(self):
        self.entrar(self.admin)
        r = self.client.post(reverse('customers:delete', args=[self.luis.pk]))
        self.assertRedirects(r, reverse('customers:list'))
        self.assertFalse(Customer.objects.filter(pk=self.luis.pk).exists())

    def test_admin_no_elimina_cliente_con_citas(self):
        call_command('seed_initial_catalog', verbosity=0)
        con_citas = Customer.objects.filter(appointments__isnull=False).first()
        self.assertIsNotNone(con_citas)
        self.entrar(self.admin)
        self.client.post(reverse('customers:delete', args=[con_citas.pk]))
        self.assertTrue(Customer.objects.filter(pk=con_citas.pk).exists())
