from django.test import TestCase

from home.views import seed_token
from profile_user.models import Specialist


class SeedDemoDataTests(TestCase):
    def test_wrong_token_is_not_found(self):
        self.assertEqual(self.client.get('/internal/seed/wrong-token/').status_code, 404)
        self.assertEqual(Specialist.objects.filter(is_published=True).count(), 0)

    def test_valid_token_seeds_specialists(self):
        response = self.client.get(f'/internal/seed/{seed_token()}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['specialists'], 10)
