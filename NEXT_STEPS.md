# Продолжение работы: деплой на Render

## Где остановились (11.11.2026)

- База Render: `healthflow-db` (`dpg-dbprh8jl550s738n0k1g-a`, free, frankfurt, status available).
- Web-сервис: `healthflow-web` (`srv-dbprkne7bikc73b6oa8g`), https://healthflow-web.onrender.com,
  репозиторий `https://github.com/SwerchIwan/Health-Flow`, ветка `master`, автодеплой по коммиту.
- Переменные окружения web заданы: `PYTHON_VERSION=3.12.3`, `DJANGO_DEBUG=False`,
  `DJANGO_SECRET_KEY` (сгенерирован), `DJANGO_ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1`,
  `DATABASE_URL=<internal, с :5432>`, `SITE_URL`/`PUBLIC_URL=https://healthflow-web.onrender.com`,
  `EMAIL_BACKEND/HOST/PORT/USER/PASSWORD/USE_SSL/DEFAULT_FROM_EMAIL` (из .env), `TELEGRAM_BOT_TOKEN`.
- Воркер бота на Render **не создан**: на плане free API отвечает
  `only web services allowed for plan`. Создавать вручную в панели
  (New → Background Worker → репозиторий Health-Flow, `pip install -r requirements-prod.txt`,
  start: `python tg_worker.py`, те же env, что у web, кроме `DATABASE_*` = internal URL).
- Последний коммит: `c088073` — start-команды обёрнуты в `bash -c '...'`
  (Render не запускает startCommand через shell → `migrate && gunicorn` падал с exit 1),
  добавлен `tg_worker.py` (запуск `tg.py` из корня репозитория).

## Что проверено

- Сборка (build) на Render проходит успешно: `pip install`, `collectstatic` — OK.
- Локально SQLite-сайт и Docker-стек работают; 35 тестов проходят.
- Подключение к Postgres Render с этого ПК (`psycopg`, любой sslmode) не удаётся:
  `SSL connection has been closed unexpectedly` — скорее всего сеть/провайдер режет,
  проверить из Render-контейнера.
- Deploy `c088073` падал в runtime с `ModuleNotFoundError: No module named 'g4f'`
  (`profile_user/AI.py` ← `urls.py`): `g4f` был только в `requirements.txt`, не в prod.
  Исправлено: `g4f==0.3.1.0` добавлен в `requirements-prod.txt`; проверено в чистом venv —
  `pip install -r requirements-prod.txt`, `manage.py check` (DEBUG=False), страницы `/`,
  `/specialists/`, `/accounts/` → 200, все 7 AI-провайдеров на месте, 35 тестов OK.
  Коммит `245d381` запушен, Render пересобрал:
  `/` → 200, `/specialists/` → 200, `/accounts/` → 200, `/admin/` → 302 (login),
  статика whitenoise (css `base.*.css`, шрифт `.ttf`) отдаётся 200.
- На сервисе пока нет пользователей: каталог `/specialists/` пишет
  «0 проверенных специалистов» — нужен шаг 3 ниже (seed).

## Что делать дальше (по порядку)

1. Открыть https://dashboard.render.com/web/srv-dbprkne7bikc73b6oa8g → вкладка **Logs**
   (Build / Deploy / App). Посмотреть последнюю причину `update_failed` (exit 1).
   Если снова падает на `migrate` — это подключение к internal-DB:
   env `DATABASE_URL` должен быть ровно internal URL вида
   `postgresql://<user>:<pass>@dpg-dbprh8jl550s738n0k1g-a:5432/<db>` (порт обязателен).
2. После статуса **Live**: открыть https://healthflow-web.onrender.com
   (`/`, `/specialists/`, `/accounts/`, `/admin/`).
3. Демо-данные — через панель Render: Shell у web-сервиса →
   `cd HealthFlow && python manage.py seed_specialists && python manage.py seed_patients`.
   Пациенты: `patient_demo_1..3`, пароль `PatientDemo2026!`.
4. Суперпользователь — в том же Shell: `cd HealthFlow && python manage.py createsuperuser`
   (нужен свой пароль; можно `DJANGO_SUPERUSER_PASSWORD=... python manage.py createsuperuser --noinput
   --username admin --email ...`).
5. Воркер бота `healthflow-bot` — создать в панели (см. выше).
6. После деплоя **отозвать API-ключ Render**: Account Settings → API Keys → Revoke
   (ключи передавались в чате — ротировать обязательно).
7. Медиа (фото) — контейнер free без диска: настроить S3 (Cloudflare R2 / B2) через
   `AWS_STORAGE_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
   `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN`, `AWS_S3_REGION_NAME`. См. `RENDER.md`.
8. Free-план засыпает после ~15 минут без запросов (первый запрос 30-60 с) и действует пробный период.

## Локальный запуск (как раньше)

```
cd C:/Users/12059/PycharmProjects/Health-Flow/HealthFlow
../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
../.venv/Scripts/python.exe tg.py
```
Docker: `docker compose up -d --build` (сайт на http://127.0.0.1:8000).

## Вспомогательные скрипты (каталог `.local/`, в git не попадает)

- `render_create.py` / `render_env.py` / `render_fixdb.py` / `render_start.py` — работа через
  Render API; ключ берётся из переменной окружения `RENDER_API_KEY` (в файл не сохранять).
- `render_find.py`, `render_deploy.py`, `render_events.py`, `render_logs.py` — поиск сервисов,
  деплой и события. Логи сборки через API v1 отдают 404 — смотреть в панели.
- `render_state.json` — id базы и внутренний `DATABASE_URL` (содержит пароль, не коммитить).
- `HOSTING.md` — туннель Serveo / LAN.
