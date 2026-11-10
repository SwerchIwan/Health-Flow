# Продолжение работы после перезагрузки

## Что уже сделано
- Удаление чатов исправлено (`HealthFlow/static/js/profile.js`), CSRF через `csrfToken()`.
- Каталог специалистов с фото, рейтингами и отзывами; страница специалиста `/specialists/<id>/`.
- Подписки: тарифы, демо-оплата картой, отмена.
- Регистрация/вход по коду (email/телефон).
- Демо-данные: `seed_specialists`, `seed_patients` (пациенты `patient_demo_1..3`, пароль `PatientDemo2026!`).
- CSRF включён на всех AJAX-вьюхах профиля (было исключение `@csrf_exempt` и на `delete_chat`).
- Из индекса git убраны `db.sqlite3` и сессия бота `HealthFlow/account.session` (файлы на диске остались).
- Docker-стек поднимается: web (gunicorn) + nginx + redis + bot. Исправлены `.dockerignore`, пути `/app/HealthFlow/*`, `TgCrypto`, `gunicorn`, UTF-16 в requirements, Windows-only event loop.
- Коды подтверждения хранятся в Redis (`REDIS_URL`), общие для всех воркеров; без `REDIS_URL` — LocMem (локальная разработка).
- Тесты: 35 шт. (users, profile_user) — проходят.
- Push на GitHub работает (credential.helper=manager). Последний коммит: bb24ef7.

## Запуск
Локально (без Docker):
```
cd C:/Users/12059/PycharmProjects/Health-Flow/HealthFlow
../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
../.venv/Scripts/python.exe tg.py          # бот, .env загружается сам
```
Docker (сайт на http://127.0.0.1:8000):
```
cd C:/Users/12059/PycharmProjects/Health-Flow
docker compose up -d --build
docker compose logs -f web|bot
docker compose down
```
Если Docker Desktop не стартует — проверить, что он запущен (системный трей); WSL-дистрибутив `docker-desktop` создаётся сам.

## Перед продакшеном
- `.env`: `DJANGO_DEBUG=False`, домен в `DJANGO_ALLOWED_HOSTS`, `SITE_URL`, `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Сменить пароль суперпользователя и ротировать секреты из `.env` (они уже были в истории git).
- На хосте `REDIS_URL` задавать через окружение compose, не через `.env`/`env_file` (иначе локальное значение перекроет адрес сервиса).
