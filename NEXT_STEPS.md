# Продолжение работы после перезагрузки

## Что уже сделано
- Удаление чатов исправлено (`HealthFlow/static/js/profile.js`), CSRF через `csrfToken()`.
- Каталог специалистов с фото, рейтингами и отзывами; страница специалиста `/specialists/<id>/`.
- Подписки: тарифы, демо-оплата картой, отмена.
- Регистрация/вход по коду (email/телефон).
- Демо-данные: `seed_specialists`, `seed_patients` (пациенты `patient_demo_1..3`, пароль `PatientDemo2026!`).
- CSRF включён на всех AJAX-вьюхах профиля (было исключение `@csrf_exempt` и на `delete_chat`).
- Из индекса git убраны `db.sqlite3` и сессия бота `HealthFlow/account.session` (файлы на диске остались).
- Тесты: 33 шт. (users, profile_user) — проходят.
- Коммиты: 0399f98, 110aa19, 2228092, eba008d. **Push на GitHub не выполнен** — `git push` требует логин (HTTPS без сохранённых учётных данных).

## После перезагрузки — запуск
```
cd C:/Users/12059/PycharmProjects/Health-Flow/HealthFlow
../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
../.venv/Scripts/python.exe tg.py          # бот, .env загружается сам
```

## Docker/хостинг — блокер
Docker Desktop не стартует: виртуализация выключена в BIOS (`Виртуализация включена во встроенном ПО: Нет`).
1. Включить Intel VT-x / AMD SVM в BIOS.
2. `wsl --install -d Ubuntu-24.04`, запустить Docker Desktop.
3. `docker compose up -d --build` (web + nginx + bot).

## Перед продакшеном
- `.env`: `DJANGO_DEBUG=False`, домен в `DJANGO_ALLOWED_HOSTS` и `SITE_URL`.
- In-memory cache для кодов подтверждения заменить на Redis (много воркеров).
- Сменить пароль суперпользователя и ротировать секреты из `.env`.
