from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


class RootSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='root', email='root@example.com', password='Test-only-password-42',
        )
        self.client.force_login(self.user)

    def _login_to_admin(self):
        return self.client.post(reverse('admin:login'), {
            'username': self.user.email, 'password': 'Test-only-password-42',
            'next': reverse('admin:index'),
        })

    @override_settings(ADMIN_ACCESS_ALERT_EMAIL='security@example.com',
                       EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_first_admin_entry_is_reported_once_in_the_session(self):
        self.assertRedirects(self._login_to_admin(), reverse('admin:index'), fetch_redirect_response=False)
        for _ in range(2):
            self.assertEqual(self.client.get(reverse('admin:index'), REMOTE_ADDR='192.0.2.10',
                                             HTTP_USER_AGENT='Test browser').status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('192.0.2.10', mail.outbox[0].body)
        self.assertIn('Test browser', mail.outbox[0].body)

    def test_root_can_open_enrollment(self):
        response = self.client.get(reverse('accounts:mfa_setup'))
        self.assertContains(response, 'Activar multifactor')
        self.assertIn('no-store', response['Cache-Control'])

    def test_email_login_works_in_both_panels(self):
        self.client.logout()
        response = self.client.post(reverse('admin:login'), {
            'username': 'ROOT@example.com', 'password': 'Test-only-password-42',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))
        self.client.logout()
        response = self.client.post(reverse('accounts:login'), {
            'login': 'ROOT@example.com', 'password': 'Test-only-password-42',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))

    def test_enrollment_blocks_both_panels_and_recovery_code_is_single_use(self):
        from django_otp.oath import TOTP

        setup = reverse('accounts:mfa_setup')
        verify = reverse('accounts:mfa_verify')
        self.assertNotContains(self.client.get(setup), 'Clave de configuración manual')
        self.assertRedirects(self.client.post(setup, {'password': 'Test-only-password-42'}), setup)
        self.assertContains(self.client.get(setup), 'Clave de configuración manual')
        key = bytes.fromhex(self.client.session['privileged_mfa_setup']['key'])
        token = f'{TOTP(key).token():06d}'
        enrollment = self.client.post(setup, {'token': token})
        self.assertContains(enrollment, 'Multifactor activado')
        recovery_code = enrollment.context['recovery_codes'][0]
        admin_index = reverse('admin:index')
        self.assertRedirects(
            self.client.get(admin_index), f"{reverse('admin:login')}?next={admin_index}",
        )
        self.assertRedirects(self._login_to_admin(), admin_index, fetch_redirect_response=False)
        self.assertRedirects(
            self.client.get(admin_index), f'{verify}?next={admin_index}', fetch_redirect_response=False,
        )
        admin_recovery_code = enrollment.context['recovery_codes'][1]
        self.assertRedirects(
            self.client.post(f'{verify}?next={admin_index}', {'token': admin_recovery_code}),
            admin_index,
        )

        self.client.logout()
        self.client.force_login(self.user)
        dashboard = reverse('dashboard:index')
        self.assertRedirects(
            self.client.get(dashboard), f'{verify}?next={dashboard}', fetch_redirect_response=False,
        )
        self.assertContains(self.client.post(verify, {'token': token}), 'Código incorrecto')
        from django_otp.plugins.otp_totp.models import TOTPDevice
        TOTPDevice.objects.get(user=self.user).throttle_reset()

        self.assertRedirects(self.client.post(verify, {'token': recovery_code}), reverse('dashboard:index'))
        self.client.logout()
        self.client.force_login(self.user)
        self.assertContains(self.client.post(verify, {'token': recovery_code}), 'Código incorrecto')

    def test_studiogest_session_does_not_open_django_admin(self):
        admin_index = reverse('admin:index')
        admin_login = reverse('admin:login')
        self.assertRedirects(self.client.get(admin_index), f'{admin_login}?next={admin_index}')
        self.assertEqual(self.client.post(admin_login, {
            'username': self.user.email, 'password': 'incorrect', 'next': admin_index,
        }).status_code, 200)
        self.assertRedirects(self.client.get(admin_index), f'{admin_login}?next={admin_index}')
        self.assertRedirects(self.client.post(admin_login, {
            'username': self.user.email, 'password': 'Test-only-password-42', 'next': admin_index,
        }), admin_index)
