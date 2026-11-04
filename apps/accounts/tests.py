from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .forms import LoginForm, ProfileForm

User = get_user_model()


class ProfileSettingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.worker = User.objects.create_user(
            username='perfil-worker', email='worker@profile.test', password='Clave#12345',
            first_name='Luisa', last_name='Gomez', phone='3001112233', role=User.Role.WORKER)
        cls.admin = User.objects.create_user(
            username='perfil-admin', email='admin@profile.test', password='Clave#12345',
            first_name='Admin', role=User.Role.ADMIN)

    def setUp(self):
        self.url = reverse('accounts:settings')
        self.client.force_login(self.worker)
        self.data = {'first_name': 'Luisa Fernanda', 'last_name': 'Gomez Andrade',
                     'email': 'nuevo@profile.test', 'phone': '+57 310 123 4567'}

    def test_anonymous_get_and_post_require_login(self):
        self.client.logout()
        for method in [self.client.get, self.client.post]:
            response = method(self.url)
            self.assertRedirects(response, reverse('accounts:login') + '?next=' + self.url)
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.email, 'worker@profile.test')

    def test_worker_sees_own_profile_and_active_menu(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
        self.assertEqual(response.context['form'].instance.pk, self.worker.pk)
        for value in ['Luisa', 'Gomez', 'worker@profile.test', '3001112233']:
            self.assertContains(response, value)
        self.assertContains(response, 'href="' + self.url + '" aria-current="page"')

    def test_admin_can_edit_own_profile(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, self.data)
        self.assertRedirects(response, self.url)
        self.admin.refresh_from_db()
        self.worker.refresh_from_db()
        self.assertEqual(self.admin.email, self.data['email'])
        self.assertEqual(self.worker.email, 'worker@profile.test')

    def test_success_normalizes_data_and_keeps_session(self):
        self.data.update(first_name='  Luisa   Fernanda  ', last_name='  Gomez   Andrade ',
                         email='  NUEVO@PROFILE.TEST  ')
        response = self.client.post(self.url, self.data, follow=True)
        self.assertContains(response, 'Tus datos personales se actualizaron correctamente.')
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.first_name, 'Luisa Fernanda')
        self.assertEqual(self.worker.last_name, 'Gomez Andrade')
        self.assertEqual(self.worker.email, 'nuevo@profile.test')
        self.assertEqual(self.worker.phone, self.data['phone'])
        self.assertEqual(int(self.client.session['_auth_user_id']), self.worker.pk)
        login = LoginForm({'login': 'nuevo@profile.test', 'password': 'Clave#12345'})
        self.assertTrue(login.is_valid(), login.errors)
        self.assertEqual(login.get_user().pk, self.worker.pk)

    def test_only_personal_fields_are_exposed(self):
        self.assertEqual(set(ProfileForm().fields), {'first_name', 'last_name', 'email', 'phone'})

    def test_crafted_post_cannot_target_other_user_or_change_privileges(self):
        original_password = self.worker.password
        data = dict(self.data, id=self.admin.pk, pk=self.admin.pk, user_id=self.admin.pk,
                    username='changed', role=User.Role.ADMIN, is_staff='1', is_superuser='1',
                    is_active='', password='replacement', groups='1', user_permissions='1')
        response = self.client.post(self.url + '?user_id=' + str(self.admin.pk), data)
        self.assertRedirects(response, self.url)
        self.worker.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.worker.email, self.data['email'])
        self.assertEqual(self.worker.username, 'perfil-worker')
        self.assertEqual(self.worker.role, User.Role.WORKER)
        self.assertFalse(self.worker.is_staff)
        self.assertFalse(self.worker.is_superuser)
        self.assertTrue(self.worker.is_active)
        self.assertEqual(self.worker.password, original_password)
        self.assertFalse(self.worker.groups.exists())
        self.assertFalse(self.worker.user_permissions.exists())
        self.assertEqual(self.admin.email, 'admin@profile.test')
        self.assertEqual(self.admin.first_name, 'Admin')

    def test_duplicate_email_case_insensitive_does_not_save_other_fields(self):
        self.data['email'] = 'ADMIN@PROFILE.TEST'
        response = self.client.post(self.url, self.data)
        self.assertContains(response, 'Este correo electrónico ya está registrado por otro usuario.')
        self.assertContains(response, 'No se pudieron guardar los cambios.')
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.first_name, 'Luisa')
        self.assertEqual(self.worker.email, 'worker@profile.test')

    def test_own_email_is_allowed(self):
        self.data['email'] = 'WORKER@PROFILE.TEST'
        self.assertRedirects(self.client.post(self.url, self.data), self.url)

    def test_invalid_fields_do_not_save(self):
        for field, value in [('email', 'invalido'), ('email', ''), ('first_name', '  '),
                             ('first_name', 'a' * 151), ('last_name', 'a' * 151),
                             ('phone', 'abc1234567'), ('phone', '123'),
                             ('phone', '1' * 16)]:
            with self.subTest(field=field, value=value):
                data = dict(self.data, **{field: value})
                response = self.client.post(self.url, data)
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context['form'].errors)
                self.worker.refresh_from_db()
                self.assertEqual(self.worker.first_name, 'Luisa')
                self.assertEqual(self.worker.email, 'worker@profile.test')
                self.assertEqual(self.worker.phone, '3001112233')

    def test_optional_fields_can_be_cleared(self):
        self.data.update(last_name='', phone='')
        self.assertRedirects(self.client.post(self.url, self.data), self.url)
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.last_name, '')
        self.assertIsNone(self.worker.phone)

    def test_post_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.worker)
        client.get(self.url)
        self.assertEqual(client.post(self.url, self.data).status_code, 403)
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.email, 'worker@profile.test')
        token = client.cookies['csrftoken'].value
        self.assertRedirects(client.post(self.url, dict(self.data, csrfmiddlewaretoken=token)), self.url)

    def test_unsupported_method_is_rejected(self):
        self.assertEqual(self.client.delete(self.url).status_code, 405)
