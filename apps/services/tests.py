from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from services.models import Professional, Service

User = get_user_model()


class ProfessionalCRUDTests(TestCase):
    def setUp(self):
        # 1. Admin user
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpassword123',
            first_name='Admin',
            last_name='Sistema',
            role=User.Role.ADMIN,
        )

        # 2. Worker user
        self.worker_user = User.objects.create_user(
            username='worker_test',
            email='worker@test.com',
            password='testpassword123',
            first_name='Juan',
            last_name='Barbero',
            role=User.Role.WORKER,
        )
        self.prof1 = Professional.objects.create(
            user=self.worker_user,
            specialty='Cortes Clásicos',
            color_tag='#0D9488',
            is_active=True,
        )

        # 3. Another professional (inactive)
        self.inactive_user = User.objects.create_user(
            username='inactive_test',
            email='inactive@test.com',
            password='testpassword123',
            first_name='Pedro',
            last_name='Pérez',
            role=User.Role.WORKER,
        )
        self.prof_inactive = Professional.objects.create(
            user=self.inactive_user,
            specialty='Barba y Afeitado',
            color_tag='#2563EB',
            is_active=False,
        )

        self.list_url = reverse('services:professionals_list')
        self.create_url = reverse('services:professional_create')

    def test_professionals_list_requires_login(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_professionals_list_view_as_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services/professionals_list.html')
        self.assertContains(response, 'Juan Barbero')
        self.assertContains(response, 'Pedro Pérez')
        self.assertContains(response, 'Cortes Clásicos')

    def test_professionals_list_search_by_name_and_specialty(self):
        self.client.force_login(self.admin)
        # Search by first name
        response = self.client.get(self.list_url, {'q': 'Juan'})
        self.assertContains(response, 'Juan Barbero')
        self.assertNotContains(response, 'Pedro Pérez')

        # Search by specialty
        response = self.client.get(self.list_url, {'q': 'Barba'})
        self.assertContains(response, 'Pedro Pérez')
        self.assertNotContains(response, 'Juan Barbero')

    def test_professionals_list_filter_by_status(self):
        self.client.force_login(self.admin)
        # Only active
        res_active = self.client.get(self.list_url, {'estado': 'activos'})
        self.assertContains(res_active, 'Juan Barbero')
        self.assertNotContains(res_active, 'Pedro Pérez')

        # Only inactive
        res_inactive = self.client.get(self.list_url, {'estado': 'inactivos'})
        self.assertContains(res_inactive, 'Pedro Pérez')
        self.assertNotContains(res_inactive, 'Juan Barbero')

    def test_worker_cannot_access_create_form(self):
        self.client.force_login(self.worker_user)
        response = self.client.get(self.create_url)
        self.assertRedirects(response, self.list_url)

    def test_admin_can_create_new_professional_success(self):
        self.client.force_login(self.admin)
        payload = {
            'first_name': 'Mateo',
            'last_name': 'Ramírez',
            'email': 'mateo@studiogest.co',
            'phone': '3001234567',
            'specialty': 'Colorimetría y Diseños',
            'color_tag': '#7C3AED',
            'password': 'custompassword123',
            'is_active': 'on',
        }
        response = self.client.post(self.create_url, payload)
        self.assertRedirects(response, self.list_url)

        # Verify created User and Professional in DB
        user = User.objects.get(email='mateo@studiogest.co')
        self.assertEqual(user.first_name, 'Mateo')
        self.assertEqual(user.last_name, 'Ramírez')
        self.assertEqual(user.role, User.Role.WORKER)
        self.assertTrue(user.check_password('custompassword123'))

        prof = Professional.objects.get(user=user)
        self.assertEqual(prof.specialty, 'Colorimetría y Diseños')
        self.assertEqual(prof.color_tag, '#7C3AED')
        self.assertTrue(prof.is_active)

    def test_create_professional_duplicate_email_fails(self):
        self.client.force_login(self.admin)
        payload = {
            'first_name': 'Duplicado',
            'last_name': 'Prueba',
            'email': 'worker@test.com',  # already exists!
            'specialty': 'Barbero',
            'color_tag': '#0D9488',
        }
        response = self.client.post(self.create_url, payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFormError(form, 'email', 'Ya existe un usuario con este correo electrónico.')

    def test_create_professional_invalid_phone_fails(self):
        self.client.force_login(self.admin)
        payload = {
            'first_name': 'Carlos',
            'last_name': 'Gómez',
            'email': 'carlos.g@studiogest.co',
            'phone': '123',  # too short
            'specialty': 'Barbero',
            'color_tag': '#0D9488',
        }
        response = self.client.post(self.create_url, payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFormError(form, 'phone', 'Escribe un teléfono válido (entre 7 y 15 dígitos).')

    def test_admin_can_update_professional(self):
        self.client.force_login(self.admin)
        update_url = reverse('services:professional_update', args=[self.prof1.pk])

        # GET form preloaded
        get_res = self.client.get(update_url)
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, 'Juan')
        self.assertContains(get_res, 'Cortes Clásicos')

        # POST update
        payload = {
            'first_name': 'Juan Camilo',
            'last_name': 'Barbero Restrepo',
            'email': 'juancamilo@test.com',
            'phone': '3129876543',
            'specialty': 'Master Barber & Spa',
            'color_tag': '#D97706',
            'is_active': 'on',
            'password': '',  # Leave empty to keep previous
        }
        post_res = self.client.post(update_url, payload)
        self.assertRedirects(post_res, self.list_url)

        self.prof1.refresh_from_db()
        self.prof1.user.refresh_from_db()
        self.assertEqual(self.prof1.user.first_name, 'Juan Camilo')
        self.assertEqual(self.prof1.user.last_name, 'Barbero Restrepo')
        self.assertEqual(self.prof1.user.email, 'juancamilo@test.com')
        self.assertEqual(self.prof1.specialty, 'Master Barber & Spa')
        self.assertEqual(self.prof1.color_tag, '#D97706')
        self.assertTrue(self.prof1.user.check_password('testpassword123'))

    def test_delete_professional_without_appointments_deletes_permanently(self):
        self.client.force_login(self.admin)
        delete_url = reverse('services:professional_delete', args=[self.prof_inactive.pk])

        # GET confirm view
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¿Eliminar definitivamente')

        # POST delete
        post_res = self.client.post(delete_url, {'accion': 'eliminar'})
        self.assertRedirects(post_res, self.list_url)

        self.assertFalse(Professional.objects.filter(pk=self.prof_inactive.pk).exists())
        self.assertFalse(User.objects.filter(pk=self.inactive_user.pk).exists())

    def test_delete_professional_with_appointments_blocks_permanent_deletion_and_offers_deactivation(self):
        from customers.models import Customer
        from datetime import date, time

        customer = Customer.objects.create(name='Cliente Cita', phone='3001112233')
        service = Service.objects.create(name='Corte', price_cop=30000, duration_minutes=30)
        Appointment.objects.create(
            customer=customer,
            service=service,
            professional=self.prof1,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            price_cop=30000,
        )

        self.client.force_login(self.admin)
        delete_url = reverse('services:professional_delete', args=[self.prof1.pk])

        # GET shows warning that appointments exist
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Protección de Historial')
        self.assertContains(response, 'Desactivar profesional')

        # Direct POST to permanently delete should be rejected
        post_del = self.client.post(delete_url, {'accion': 'eliminar'})
        self.assertRedirects(post_del, self.list_url)
        self.assertTrue(Professional.objects.filter(pk=self.prof1.pk).exists())

        # POST with accion=desactivar should successfully deactivate
        post_deact = self.client.post(delete_url, {'accion': 'desactivar'})
        self.assertRedirects(post_deact, self.list_url)

        self.prof1.refresh_from_db()
        self.assertFalse(self.prof1.is_active)

    def test_toggle_professional_status(self):
        self.client.force_login(self.admin)
        toggle_url = reverse('services:professional_toggle_status', args=[self.prof1.pk])

        self.assertTrue(self.prof1.is_active)
        # GET should be rejected (require_POST)
        res_get = self.client.get(toggle_url)
        self.assertEqual(res_get.status_code, 405)

        # POST toggles to inactive
        res_post = self.client.post(toggle_url)
        self.assertRedirects(res_post, self.list_url)
        self.prof1.refresh_from_db()
        self.assertFalse(self.prof1.is_active)

        # POST again toggles back to active
        res_post2 = self.client.post(toggle_url)
        self.assertRedirects(res_post2, self.list_url)
        self.prof1.refresh_from_db()
        self.assertTrue(self.prof1.is_active)
