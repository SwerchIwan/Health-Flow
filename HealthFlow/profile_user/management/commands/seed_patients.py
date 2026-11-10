import shutil
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from profile_user.models import BMI, Blood, Chat, Message, Note, Pressure, Specialist

DEMO_PASSWORD = 'PatientDemo2026!'

DEMO_PATIENTS = [
    {
        'username': 'patient_demo_1',
        'first_name': 'Елена',
        'last_name': 'Ковалёва',
        'city': 'Минск',
        'specialist': 'anna.petrova',
        'messages': [
            ('Здравствуйте! Последнюю неделю давление держится около 140/90, есть слабость.', True),
            ('Добрый день, Елена. Давление лучше измерять утром и вечером, запишите показания в дневник '
             'здоровья в профиле и прикрепите, пожалуйста, свежие анализы. По ним посмотрим динамику.', False),
            ('Хорошо, отправляю результаты последних анализов и дневник за две недели.', True),
            ('Спасибо, вижу данные. Давление постепенно снижается, гемоглобин в норме. '
             'Продолжайте текущий режим, обсудим на следующей неделе.', False),
        ],
        'notes': [
            # (days_ago, text, hemoglobin, leukocytes, lymphocytes, systolic, diastolic, pulse, height, weight, file)
            (28, 'Начала вести дневник после консультации кардиолога. Утром слабость, давление повышенное.',
             132, 6.8, 30, 142, 92, 81, 168, 74, 'lab_blood_general'),
            (21, 'Утром давление чуть ниже, чувствую себя лучше. Сдала общий анализ крови.',
             136, 6.2, 32, 136, 88, 78, 168, 73, None),
            (14, 'Самочувствие улучшилось, давление в вечерние часы нормальное.',
             138, 6.4, 31, 130, 84, 75, 168, 73, None),
            (7, 'Прошла неделя, слабость почти ушла. Вес держится.',
             140, 6.1, 33, 126, 82, 72, 168, 72, None),
            (2, 'Повторно сдала биохимию по рекомендации врача, результаты прикрепила.',
             139, 6.3, 31, 124, 80, 70, 168, 72, 'lab_biochem'),
        ],
    },
    {
        'username': 'patient_demo_2',
        'first_name': 'Дмитрий',
        'last_name': 'Савин',
        'city': 'Гомель',
        'specialist': 'maria.lebedeva',
        'messages': [
            ('Добрый день! Сдал гормоны, отправляю результаты.', True),
            ('Здравствуйте, Дмитрий. Спасибо, вижу ТТГ в норме, но кортизол высоковат. '
             'Как со сном и стрессом в последние недели?', False),
            ('Сплю плохо, много работы. Стараюсь гулять по вечерам.', True),
            ('Начнём с режима сна и лёгкой нагрузки. Ещё раз сдадим гормоны через месяц '
             'и сравним с этими значениями.', False),
        ],
        'notes': [
            (30, 'Сдал гормональный профиль по направлению эндокринолога.',
             None, None, None, 128, 82, 72, 182, 88, 'lab_hormones'),
            (23, 'Начал ложиться до 23:00, по вечерам прогулка 30 минут.',
             None, None, None, 124, 80, 70, 182, 87, None),
            (16, 'Сон стал лучше, к вечеру меньше усталости.',
             None, None, None, 122, 79, 68, 182, 86, None),
            (9, 'Сдал общий анализ крови — решил проверить на фоне изменений самочувствия.',
             146, 7.1, 29, 120, 78, 67, 182, 86, 'lab_blood_general'),
            (3, 'Вес снизился на 2 кг, давление стабильное.',
             None, None, None, 118, 76, 66, 182, 86, None),
        ],
    },
    {
        'username': 'patient_demo_3',
        'first_name': 'Анастасия',
        'last_name': 'Белова',
        'city': 'Минск',
        'specialist': 'ekaterina.volkova',
        'messages': [
            ('Здравствуйте, у ребёнка периодически красные пятна на коже после еды.', True),
            ('Здравствуйте! Пришлите, пожалуйста, фото пятен и сдайте общий анализ мочи — '
             'исключим аллергическую реакцию.', False),
            ('Фото отправила, анализ мочи прикрепила сегодня.', True),
            ('Всё в пределах нормы, скорее всего пищевая реакция. Давайте понаблюдаем две недели '
             'и посмотрим, зависит ли от продуктов.', False),
        ],
        'notes': [
            (25, 'Появились пятна после ужина. Сдала анализ мочи для исключения инфекции.',
             None, None, None, None, None, None, 162, 56, 'lab_urine'),
            (18, 'Исключили ягоды на неделю, пятна стали реже.',
             118, 5.4, 35, None, None, None, 162, 55.5, None),
            (11, 'Ходим гулять чаще, сон ребёнка нормализовался.',
             None, None, None, 112, 70, 76, 162, 55.5, None),
            (4, 'Контрольный анализ крови — всё в норме.',
             120, 5.6, 34, None, None, None, 162, 55.5, 'lab_blood_general'),
        ],
    },
]

FILE_SOURCES = {
    'lab_blood_general': 'lab_blood_general',
    'lab_biochem': 'lab_biochem',
    'lab_urine': 'lab_urine',
    'lab_hormones': 'lab_hormones',
}


class Command(BaseCommand):
    help = 'Создаёт демо-пациентов с заметками, графиками, анализами и чатами со специалистами'

    def add_arguments(self, parser):
        parser.add_argument(
            '--images-dir', default=str(settings.BASE_DIR.parent / 'vibe_images'),
            help='Папка с изображениями бланков анализов lab_*.png',
        )

    def find_file(self, images_dir, prefix):
        directory = Path(images_dir)
        if not directory.is_dir():
            return None
        matches = sorted(directory.glob(f'{prefix}_*.png'))
        return matches[-1] if matches else None

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        images_dir = options['images_dir']
        today = date.today()

        for data in DEMO_PATIENTS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={'email': f"{data['username']}@healthflow.pro"},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = user.email or f"{data['username']}@healthflow.pro"
            user.save()

            if Note.objects.filter(user=user).exists():
                self.stdout.write(f'{user.username}: заметки уже есть, пропускаю')
                continue

            for days_ago, text, hb, leuk, lymph, sys, dia, pulse, height, weight, file_key in data['notes']:
                note = Note.objects.create(
                    user=user,
                    date=today - timedelta(days=days_ago),
                    additional_notes=text,
                )
                if hb is not None:
                    Blood.objects.create(note=note, hemoglobin=hb, leukocytes=leuk, lymphocytes=lymph)
                if sys is not None:
                    Pressure.objects.create(note=note, systolic=sys, diastolic=dia, pulse_rate=pulse)
                if height is not None:
                    BMI.objects.create(note=note, height=height, weight=weight)
                if file_key:
                    source = self.find_file(images_dir, file_key)
                    if source:
                        with open(source, 'rb') as fh:
                            note.file.save(f'{file_key}.png', File(fh), save=True)
                        note.save(update_fields=['file'])

            specialist = Specialist.objects.filter(user__username=data['specialist']).first()
            if not specialist:
                self.stdout.write(self.style.WARNING(f'{user.username}: специалист не найден'))
                continue

            chat, _ = Chat.objects.get_or_create(user=user, specialist=specialist)
            if not chat.messages.exists():
                for index, (text, from_patient) in enumerate(data['messages']):
                    sender = user if from_patient else specialist.user
                    Message.objects.create(chat=chat, sender=sender, content=text)
                    chat.last_message = text
                    chat.save()

            self.stdout.write(self.style.SUCCESS(
                f'{user.username}: заметок {len(data["notes"])}, чат с {specialist.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Пароль демо-пациентов: {DEMO_PASSWORD}'))
