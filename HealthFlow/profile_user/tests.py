from datetime import date, timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from profile_user.models import (BMI, Blood, Chat, Message, Note, Pressure, Rating,
                                 Specialist, SpecialistApplication, Review)
from users.models import User


class SiteFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.patient = User.objects.create_user(
            username='t_patient', email='t_patient@example.com', password='Passw0rd!2026',
            first_name='Тест', last_name='Пациент', phone='+375291112233',
        )
        cls.spec_user = User.objects.create_user(
            username='t_spec', email='t_spec@example.com', password='Passw0rd!2026',
            first_name='Врач', last_name='Тестов',
        )
        cls.specialist = Specialist.objects.create(
            user=cls.spec_user, name='Врач Тестов', specialty='therapist',
            is_published=True, price=Decimal('50'),
        )
        cls.unpublished = Specialist.objects.create(
            user=User.objects.create_user(username='t_hidden', password='Passw0rd!2026'),
            name='Скрытый', specialty='other', is_published=False,
        )

    # --- публичные страницы ---
    def test_public_pages(self):
        for url in ['/', '/accounts/', '/specialists/',
                    f'/specialists/{self.specialist.id}/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        pay = self.client.get(reverse('pay'))
        self.assertEqual(pay.status_code, 302)
        self.assertIn('/accounts/', pay['Location'])

    def test_hidden_specialist_not_in_catalog(self):
        self.assertContains(self.client.get('/specialists/'), 'Врач Тестов')
        self.assertNotContains(self.client.get('/specialists/'), 'Скрытый')
        self.assertEqual(self.client.get(f'/specialists/{self.unpublished.id}/').status_code, 404)

    def test_anonymous_profile_redirect(self):
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/', response['Location'])

    # --- профиль и заметки ---
    def test_profile_with_notes_and_chart(self):
        self.client.login(username='t_patient', password='Passw0rd!2026')
        note = Note.objects.create(user=self.patient, date=date.today(), additional_notes='Тест')
        Blood.objects.create(note=note, hemoglobin=140, leukocytes=6, lymphocytes=30)
        Pressure.objects.create(note=note, systolic=120, diastolic=80, pulse_rate=70)
        BMI.objects.create(note=note, height=170, weight=70)

        self.assertContains(self.client.get('/profile/'), 'Тест')
        chart = self.client.get('/profile/get_bmi_data/').json()
        self.assertEqual(chart['weights'], [70.0])
        self.assertEqual(chart['systolic'], [120.0])
        notes = self.client.get('/profile/notes/').json()['notes']
        self.assertEqual(len(notes), 1)

    def test_add_note_creates_metrics(self):
        self.client.login(username='t_patient', password='Passw0rd!2026')
        response = self.client.post('/profile/add_note/', {
            'date': date.today().isoformat(),
            'additional_notes': 'Хорошо себя чувствую',
            'blood[]': ['138', '6.5', '31'],
            'pressure[]': ['125', '82', '68'],
            'bmi[]': ['170', '71'],
        })
        self.assertIn(response.status_code, (200, 302))
        note = Note.objects.get(user=self.patient)
        self.assertEqual(float(note.blood_data.first().hemoglobin), 138)
        self.assertEqual(note.pressure_data.first().systolic, 125)
        self.assertEqual(float(note.bmi_data.first().weight), 71)

    def test_update_profile(self):
        self.client.login(username='t_patient', password='Passw0rd!2026')
        response = self.client.post('/profile/update_profile/', {
            'name': 'Новое', 'last_name': 'Имя',
        })
        self.assertIn(response.status_code, (200, 302))
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.first_name, 'Новое')

    # --- чаты ---
    def _make_chat(self):
        chat = Chat.objects.create(user=self.patient, specialist=self.specialist)
        Message.objects.create(chat=chat, sender=self.patient, content='Привет')
        return chat

    def test_start_chat(self):
        self.client.login(username='t_patient', password='Passw0rd!2026')
        data = self.client.post('/profile/start_chat/', {'specialist_id': self.specialist.id}).json()
        self.assertEqual(data['status'], 'success')
        again = self.client.post('/profile/start_chat/', {'specialist_id': self.specialist.id}).json()
        self.assertEqual(again['chatId'], data['chatId'])
        self.assertEqual(Chat.objects.count(), 1)

    def test_send_message_and_detail(self):
        chat = self._make_chat()
        self.client.login(username='t_patient', password='Passw0rd!2026')
        response = self.client.post('/profile/send_message/', {'chat_id': chat.id, 'message': 'Как дела?'})
        self.assertEqual(response.json()['status'], 'success')
        detail = self.client.get(f'/profile/chat_detail/{chat.id}/').json()
        self.assertEqual(len(detail['messages']), 2)

    def test_delete_chat_by_participants(self):
        chat = self._make_chat()
        self.client.login(username='t_patient', password='Passw0rd!2026')
        self.assertEqual(self.client.post(f'/profile/delete_chat/{chat.id}/').json()['status'], 'success')
        self.assertFalse(Chat.objects.filter(id=chat.id).exists())

        chat = self._make_chat()
        self.client.login(username='t_spec', password='Passw0rd!2026')
        self.assertEqual(self.client.post(f'/profile/delete_chat/{chat.id}/').json()['status'], 'success')

    def test_delete_chat_forbidden_for_stranger(self):
        chat = self._make_chat()
        stranger = User.objects.create_user(username='t_stranger', password='Passw0rd!2026')
        self.client.login(username='t_stranger', password='Passw0rd!2026')
        response = self.client.post(f'/profile/delete_chat/{chat.id}/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Chat.objects.filter(id=chat.id).exists())

    def test_send_notes_to_chat(self):
        chat = self._make_chat()
        note = Note.objects.create(user=self.patient, date=date.today(), additional_notes='Давление 130/85')
        self.client.login(username='t_patient', password='Passw0rd!2026')
        response = self.client.post(f'/profile/send_notes/{chat.id}/', {
            'note_ids': [note.id], 'comment': 'Посмотрите, пожалуйста',
        })
        self.assertEqual(response.json()['status'], 'success')
        self.assertTrue(chat.messages.filter(content__contains='Давление').exists())

    def test_send_notes_foreign_note_rejected(self):
        chat = self._make_chat()
        other = User.objects.create_user(username='t_other', password='Passw0rd!2026')
        foreign = Note.objects.create(user=other, date=date.today(), additional_notes='Чужая')
        self.client.login(username='t_patient', password='Passw0rd!2026')
        response = self.client.post(f'/profile/send_notes/{chat.id}/', {'note_ids': [foreign.id]})
        self.assertNotEqual(response.json().get('status'), 'success')
        self.assertFalse(chat.messages.filter(content__contains='Чужая').exists())

    def test_non_participant_cannot_read_chat(self):
        chat = self._make_chat()
        User.objects.create_user(username='t_stranger2', password='Passw0rd!2026')
        self.client.login(username='t_stranger2', password='Passw0rd!2026')
        self.assertEqual(self.client.get(f'/profile/chat_detail/{chat.id}/').status_code, 403)

    # --- рейтинги и отзывы ---
    def test_set_rating_recalculates_average(self):
        Rating.objects.create(specialist=self.specialist, user=User.objects.create_user(
            username='t_r1', password='Passw0rd!2026'), rating=4)
        self.client.login(username='t_patient', password='Passw0rd!2026')
        data = self.client.post('/profile/set_rating/', {
            'specialist_contact': self.spec_user.email, 'rating': 2,
        }).json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(Rating.objects.get(specialist=self.specialist, user=self.patient).rating, 2)

    def test_reviews_on_catalog_and_detail(self):
        Review.objects.create(specialist=self.specialist, author=self.patient, text='Отличный врач')
        self.assertContains(self.client.get('/specialists/'), 'Отличный врач')
        self.assertContains(self.client.get(f'/specialists/{self.specialist.id}/'), 'Отличный врач')

    def test_search_specialist(self):
        self.client.login(username='t_patient', password='Passw0rd!2026')
        data = self.client.get('/search_specialist/', {'q': 'Тестов'}).json()
        self.assertEqual(data['specialists'][0]['name'], 'Врач Тестов')
        hidden = self.client.get('/search_specialist/', {'q': 'Скрытый'}).json()
        self.assertEqual(hidden['specialists'], [])

    # --- подписка ---
    def test_pay_page_and_invalid_card(self):
        self.client.login(username='t_patient', password='Passw0rd!2026')
        self.assertEqual(self.client.get(reverse('pay')).status_code, 200)
        from subscription.models import Plan
        plan = Plan.objects.create(code='TEST', name='Тест', price=Decimal('10'), duration_days=30)
        response = self.client.post(reverse('process_payment'), {
            'subscription': plan.code, 'card_number': '1234 5678 9012 3456',
            'card_name': 'TEST USER', 'validity': '12/30', 'cvv': '123',
        })
        self.assertNotEqual(response.status_code, 302)

    # --- доступ к кабинету специалиста ---
    def test_specialist_sees_incoming_chats(self):
        self._make_chat()
        self.client.login(username='t_spec', password='Passw0rd!2026')
        self.assertContains(self.client.get('/profile/'), 'Тест')

    def test_create_specialist_application(self):
        User.objects.create_user(username='t_applicant', password='Passw0rd!2026', email='app@example.com')
        self.client.login(username='t_applicant', password='Passw0rd!2026')
        self.assertEqual(self.client.get('/profile/create_specialist/').status_code, 200)
        self.client.post('/profile/create_specialist/', {
            'first_name': 'Иван', 'last_name': 'Петров', 'contact': 'test@example.com',
            'specialization': 'therapist', 'additional_info': 'Опыт 8 лет',
        })
        self.assertTrue(SpecialistApplication.objects.filter(user__username='t_applicant').exists())
