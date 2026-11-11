import json
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from subscription.models import Payment, Plan
from users.models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthFlowTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_registration_by_email_stores_pending(self):
        response = self.client.post('/accounts/registration/', {
            'choice': 'email', 'inputField': 'new.user@example.com',
            'password': 'Str0ngPass!', 'password_confirm': 'Str0ngPass!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="confirmation_code"')
        self.assertFalse(User.objects.filter(email='new.user@example.com').exists())
        reg_id = response.context['reg_id']
        self.assertEqual(json.loads(cache.get(f'registration:{reg_id}'))['contact'], 'new.user@example.com')

    def test_registration_password_mismatch(self):
        response = self.client.post('/accounts/registration/', {
            'choice': 'email', 'inputField': 'x@example.com',
            'password': 'Str0ngPass!', 'password_confirm': 'OtherPass1',
        })
        self.assertContains(response, 'Пароли не совпадают')

    def test_registration_invalid_phone(self):
        response = self.client.post('/accounts/registration/', {
            'choice': 'phone', 'inputField': '123', 'password': 'Str0ngPass!',
        })
        self.assertContains(response, 'корректный номер')

    def test_confirm_registration_creates_user(self):
        cache.set('registration:pending-reg', json.dumps({
            'choice': 'email', 'contact': 'reg@example.com',
            'username': 'reg', 'password': 'Str0ngPass!', 'code': '424242', 'attempts': 0,
        }), timeout=900)
        response = self.client.post('/accounts/registration/confirm/', {
            'choice': 'email', 'contact': 'reg@example.com', 'confirmation_code': '424242',
            'reg_id': 'pending-reg',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='reg@example.com').exists())

    def test_confirm_registration_wrong_code(self):
        cache.set('registration:reg2-pending', json.dumps({
            'choice': 'email', 'contact': 'reg2@example.com',
            'username': 'reg2', 'password': 'Str0ngPass!', 'code': '424242', 'attempts': 0,
        }), timeout=900)
        self.client.post('/accounts/registration/confirm/', {
            'choice': 'email', 'contact': 'reg2@example.com', 'confirmation_code': '000000',
            'reg_id': 'reg2-pending',
        })
        self.assertFalse(User.objects.filter(email='reg2@example.com').exists())

    def test_login_by_password(self):
        User.objects.create_user(username='loginuser', email='login@example.com',
                                 password='Str0ngPass!')
        self.client.post('/accounts/step-two/', {'choice': 'email', 'inputField': 'login@example.com'})
        response = self.client.post('/accounts/login/', {'inputField': 'Str0ngPass!'})
        self.assertRedirects(response, reverse('profile_page'))

    def test_login_wrong_password(self):
        User.objects.create_user(username='loginuser2', email='login2@example.com',
                                 password='Str0ngPass!')
        self.client.post('/accounts/step-two/', {'choice': 'email', 'inputField': 'login2@example.com'})
        response = self.client.post('/accounts/login/', {'inputField': 'WrongPass1'})
        self.assertContains(response, 'Неверный пароль')

    def test_logout(self):
        user = User.objects.create_user(username='logoutuser', password='Str0ngPass!')
        self.client.force_login(user)
        response = self.client.post('/accounts/logout/')
        self.assertEqual(response.json(), {'success': True})
        self.assertEqual(self.client.get('/profile/').status_code, 302)


class CacheConfigTests(TestCase):
    def _load_settings_cache(self, redis_url):
        import importlib
        import os
        from unittest import mock

        from django.conf import settings as django_settings
        from HealthFlow import settings as project_settings

        with mock.patch.dict(os.environ, {'REDIS_URL': redis_url}):
            module = importlib.reload(project_settings)
        try:
            return module.CACHES['default']
        finally:
            importlib.reload(project_settings)
            self.assertIn('default', django_settings.CACHES)

    def test_redis_backend_when_url_set(self):
        config = self._load_settings_cache('redis://redis:6379/0')
        self.assertEqual(config['BACKEND'], 'django.core.cache.backends.redis.RedisCache')
        self.assertEqual(config['LOCATION'], 'redis://redis:6379/0')

    def test_locmem_backend_without_url(self):
        config = self._load_settings_cache('')
        self.assertEqual(config['BACKEND'], 'django.core.cache.backends.locmem.LocMemCache')


class PaymentFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='buyer', email='buyer@example.com', password='Str0ngPass!')
        cls.plan = Plan.objects.create(
            code='GRANDPRO', name='Grand Pro', price=Decimal('29.90'), duration_days=30)

    def test_successful_payment_activates_subscription(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('process_payment'), {
            'subscription': self.plan.code,
            'card_number': '4111 1111 1111 1111',
            'card_name': 'TEST BUYER',
            'validity': '12/30',
            'cvv': '123',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription, self.plan.code)
        self.assertTrue(self.user.subscription_is_active())
        self.assertTrue(Payment.objects.filter(user=self.user).exists())
        self.assertTrue(response['Location'].endswith(reverse('payment_success')))

    def test_payment_rejected_luhn(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('process_payment'), {
            'subscription': self.plan.code,
            'card_number': '1234 5678 9012 3456',
            'card_name': 'TEST BUYER',
            'validity': '12/30',
            'cvv': '123',
        })
        self.assertNotEqual(response.status_code, 302)
        self.assertFalse(Payment.objects.exists())
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription, 'FREE')

    def test_payment_rejected_expired_card(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('process_payment'), {
            'subscription': self.plan.code,
            'card_number': '4111 1111 1111 1111',
            'card_name': 'TEST BUYER',
            'validity': '01/20',
            'cvv': '123',
        })
        self.assertNotEqual(response.status_code, 302)
        self.assertFalse(Payment.objects.exists())

    def test_cancel_subscription(self):
        self.client.force_login(self.user)
        self.client.post(reverse('process_payment'), {
            'subscription': self.plan.code, 'card_number': '4111 1111 1111 1111',
            'card_name': 'TEST BUYER', 'validity': '12/30', 'cvv': '123',
        })
        response = self.client.post(reverse('cancel_subscription'))
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.subscription_is_active())

    def test_pay_requires_login(self):
        self.assertEqual(self.client.get(reverse('pay')).status_code, 302)
