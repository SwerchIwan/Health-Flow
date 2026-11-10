import os
import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from profile_user.models import Rating, Review, Specialist

DEMO_SPECIALISTS = [
    {
        'username': 'anna.petrova',
        'name': 'Анна Петрова',
        'specialty': 'cardiology',
        'city': 'Минск',
        'experience_years': 12,
        'price': 60,
        'languages': 'Русский, английский',
        'about': 'Кардиолог высшей категории. Занимаюсь диагностикой и профилактикой '
                 'сердечно-сосудистых заболеваний, реабилитацией после инфаркта.',
        'avatar': 'doc_anna_petrova',
        'ratings': [5, 5, 5, 4],
        'reviews': [
            ('Елена К.', 5, 'Анна помогла разобраться с давлением, которое скакало несколько месяцев. '
                            'Объяснила всё по анализам и составила понятный план. Очень внимательная.'),
            ('Виктор П.', 5, 'Отличный кардиолог. После консультации чувствую себя спокойнее, '
                             'все рекомендации работают.'),
            ('Ирина М.', 4, 'Ответила быстро, задавала правильные вопросы. Спасибо за разбор ЭКГ!'),
        ],
    },
    {
        'username': 'igor.sokolov',
        'name': 'Игорь Соколов',
        'specialty': 'therapist',
        'city': 'Минск',
        'experience_years': 9,
        'price': 40,
        'languages': 'Русский',
        'about': 'Терапевт. Помогу разобраться в симптомах, подберу обследования '
                 'и объясню результаты анализов простым языком.',
        'avatar': 'doc_igor_sokolov',
        'ratings': [5, 4, 4],
        'reviews': [
            ('Андрей С.', 5, 'Наконец-то врач, который объясняет простыми словами, а не терминами.'),
            ('Марина Л.', 4, 'Помог понять, какие анализы действительно нужны. Сэкономил мне время и деньги.'),
        ],
    },
    {
        'username': 'maria.lebedeva',
        'name': 'Мария Лебедева',
        'specialty': 'endocrinology',
        'city': 'Гомель',
        'experience_years': 15,
        'price': 55,
        'languages': 'Русский, белорусский',
        'about': 'Эндокринолог. Работаю с щитовидной железой, диабетом и гормональными нарушениями.',
        'avatar': 'doc_maria_lebedeva',
        'ratings': [5, 5, 5, 5],
        'reviews': [
            ('Ольга Д.', 5, 'С щитовидкой мучилась два года, Мария наконец нашла причину. Очень благодарна.'),
            ('Павел Р.', 5, 'Грамотный подход, объяснила схему лечения по шагам.'),
        ],
    },
    {
        'username': 'sergey.orlov',
        'name': 'Сергей Орлов',
        'specialty': 'neurology',
        'city': 'Брест',
        'experience_years': 7,
        'price': 50,
        'languages': 'Русский',
        'about': 'Невролог. Мигрени, боли в спине, нарушения сна и тревожные расстройства.',
        'avatar': 'doc_sergey_orlov',
        'ratings': [4, 5, 4],
        'reviews': [
            ('Наталья В.', 4, 'Мигрени стали реже уже через месяц. Очень довольна консультацией.'),
            ('Дмитрий Ш.', 5, 'Внимательно всё расспросил, не торопил. Понятные рекомендации.'),
        ],
    },
    {
        'username': 'olga.kuznetsova',
        'name': 'Ольга Кузнецова',
        'specialty': 'psychology',
        'city': 'Минск',
        'experience_years': 10,
        'price': 45,
        'languages': 'Русский, английский',
        'about': 'Клинический психолог. Помогаю справляться со стрессом, выгоранием '
                 'и тревогой в формате онлайн-консультаций.',
        'avatar': 'doc_olga_kuznetsova',
        'ratings': [5, 5, 5],
        'reviews': [
            ('Алина Т.', 5, 'С Ольгой легко, без осуждения. Помогла пережить сложный период на работе.'),
            ('Ксения Б.', 5, 'Очень чуткий специалист. Уже чувствую прогресс.'),
            ('Марк Ю.', 5, 'Спасибо за инструменты против тревоги — реально работают.'),
        ],
    },
    {
        'username': 'pavel.morozov',
        'name': 'Павел Морозов',
        'specialty': 'gastroenterology',
        'city': 'Витебск',
        'experience_years': 11,
        'price': 52,
        'languages': 'Русский',
        'about': 'Гастроэнтеролог. Диагностика и лечение заболеваний ЖКТ, подбор диеты при '
                 'хронических состояниях.',
        'avatar': 'doc_pavel_morozov',
        'ratings': [4, 4, 5],
        'reviews': [
            ('Сергей Н.', 4, 'Подобрал диету, живот перестал беспокоить. Всё понятно объясняет.'),
            ('Ирина Ф.', 5, 'Помог расшифровать гастроскопию и успокоил.'),
        ],
    },
    {
        'username': 'ekaterina.volkova',
        'name': 'Екатерина Волкова',
        'specialty': 'pediatrics',
        'city': 'Минск',
        'experience_years': 8,
        'price': 45,
        'languages': 'Русский',
        'about': 'Педиатр. Помогаю родителям с питанием, вакцинацией и развитием ребёнка с первых месяцев.',
        'avatar': 'doc_ekaterina_volkova',
        'ratings': [5, 5, 5, 5],
        'reviews': [
            ('Анастасия Г.', 5, 'С ребёнком высыпало, Екатерина быстро подсказала, что делать. Очень спокойная.'),
            ('Олег А.', 5, 'Помогла с прикормом, всё по делу, без лишних процедур.'),
        ],
    },
    {
        'username': 'alexey.grigoriev',
        'name': 'Алексей Григорьев',
        'specialty': 'dermatology',
        'city': 'Гродно',
        'experience_years': 6,
        'price': 48,
        'languages': 'Русский',
        'about': 'Дерматолог. Акне, экзема, аллергические реакции кожи. Разбираю фото в чате '
                 'и подскажу, какие анализы сдать.',
        'avatar': 'doc_alexey_grigoriev',
        'ratings': [4, 4, 5],
        'reviews': [
            ('Валентина К.', 4, 'Кожа заметно улучшилась за полтора месяца. Спасибо за корректную схему.'),
            ('Тимур Ж.', 5, 'Удобно, что можно отправить фото и получить ответ в чате.'),
        ],
    },
    {
        'username': 'natalia.fedorova',
        'name': 'Наталья Фёдорова',
        'specialty': 'dietology',
        'city': 'Минск',
        'experience_years': 5,
        'price': 35,
        'languages': 'Русский, английский',
        'about': 'Диетолог-нутрициолог. Составляю рационы с учётом анализов и образа жизни, '
                 'помогаю корректировать вес без жёстких диет.',
        'avatar': 'doc_natalia_fedorova',
        'ratings': [4, 5],
        'reviews': [
            ('Юлия С.', 4, 'Наконец-то рацион, который мне подходит по вкусу и расписанию.'),
            ('Артём Л.', 5, 'Минус 6 кг без голода. Понятный план и поддержка.'),
        ],
    },
    {
        'username': 'roman.andreev',
        'name': 'Роман Андреев',
        'specialty': 'orthopedics',
        'city': 'Могилёв',
        'experience_years': 14,
        'price': 58,
        'languages': 'Русский',
        'about': 'Ортопед-травматолог. Боли в суставах и спине, восстановление после травм.',
        'avatar': 'doc_roman_andreev',
        'ratings': [5, 4, 5],
        'reviews': [
            ('Максим Д.', 5, 'После растяжения связок Роман составил восстановительную программу. Спасибо!'),
            ('Светлана Р.', 4, 'Помог с болью в колене, назначил нужные обследования без лишнего.'),
        ],
    },
]

DEMO_FIRST_NAMES = [
    'Елена', 'Марина', 'Ольга', 'Наталья', 'Ирина', 'Анастасия', 'Юлия', 'Светлана', 'Алина', 'Валентина',
    'Виктор', 'Андрей', 'Павел', 'Дмитрий', 'Сергей', 'Олег', 'Марк', 'Тимур', 'Артём', 'Максим',
]


class Command(BaseCommand):
    help = 'Наполняет демо-специалистов аватарками, отзывами и оценками (идемпотентно)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--images-dir', default=str(settings.BASE_DIR.parent / 'vibe_images'),
            help='Папка с исходными портретами doc_<username>_*.png',
        )

    def find_avatar(self, images_dir, prefix):
        directory = Path(images_dir)
        if not directory.is_dir():
            return None
        matches = sorted(directory.glob(f'{prefix}_*.png'), key=os.path.getmtime)
        return matches[-1] if matches else None

    def get_reviewer(self, User, index):
        username = f'reviewer_{index}'
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': DEMO_FIRST_NAMES[(index - 1) % len(DEMO_FIRST_NAMES)],
            },
        )
        if user.password == '':
            user.set_unusable_password()
            user.save(update_fields=['password'])
        return user

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        images_dir = options['images_dir']
        avatar_root = Path(settings.MEDIA_ROOT) / 'users' / 'specialists'

        created = updated = reviewer_index = 0

        for item in DEMO_SPECIALISTS:
            user, user_created = User.objects.get_or_create(
                username=item['username'],
                defaults={'email': f"{item['username']}@healthflow.pro"},
            )
            user.first_name = item['name'].split()[0]
            user.last_name = item['name'].split()[-1]
            user.email = user.email or f"{item['username']}@healthflow.pro"
            if user_created:
                user.set_unusable_password()

            if not user.photo:
                source = self.find_avatar(images_dir, item['avatar'])
                if source:
                    target_dir = avatar_root / item['username']
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target = target_dir / 'avatar.png'
                    if not target.exists():
                        shutil.copyfile(source, target)
                    user.photo = f'users/specialists/{item["username"]}/avatar.png'
            user.save()

            specialist, was_created = Specialist.objects.update_or_create(
                user=user,
                defaults={
                    'name': item['name'],
                    'specialty': item['specialty'],
                    'about': item['about'],
                    'experience_years': item['experience_years'],
                    'price': item['price'],
                    'city': item['city'],
                    'languages': item['languages'],
                    'is_published': True,
                    'is_catalog_demo': True,
                },
            )
            created += was_created
            updated += not was_created

            if Review.objects.filter(specialist=specialist).exists():
                continue

            for display_name, stars, text in item['reviews']:
                reviewer_index += 1
                reviewer = self.get_reviewer(User, reviewer_index)
                Review.objects.create(specialist=specialist, author=reviewer, text=text)
                Rating.objects.update_or_create(
                    specialist=specialist, user=reviewer, defaults={'rating': stars})
            for stars in item['ratings']:
                reviewer_index += 1
                reviewer = self.get_reviewer(User, reviewer_index)
                Rating.objects.update_or_create(
                    specialist=specialist, user=reviewer, defaults={'rating': stars})

        self.stdout.write(self.style.SUCCESS(
            f'Специалистов: создано {created}, обновлено {updated}. '
            f'Отзывы и оценки проставлены (авторов: {reviewer_index}).'
        ))
