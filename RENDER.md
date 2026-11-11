# Деплой на Render.com

Пробный бесплатный план (30 дней). Сайт работает на серверах Render — ваш ПК не нужен.

## Что нужно
1. Аккаунт Render (регистрация через GitHub), карта не нужна.
2. GitHub-репозиторий с последним `master` (см. ниже).

## Шаги
1. Push в GitHub (из папки проекта):
   ```
   git push origin master
   ```
2. На https://dashboard.render.com → **New** → **Blueprint** → выберите репозиторий
   `SwerchIwan/Health-Flow` (ветка `master`). Render прочитает `render.yaml` и создаст:
   - `healthflow` — веб-сервис (миграции + gunicorn);
   - `healthflow-bot` — Telegram-бот;
   - `healthflow-db` — Postgres.
3. В диалоге Blueprint у сервисов с `sync: false` введите значения:

   | Переменная | Куда | Значение |
   |---|---|---|
   | `TELEGRAM_BOT_TOKEN` | healthflow-bot | токен из `.env` |
   | `SITE_URL` | healthflow-bot | `https://<имя>.onrender.com` (появится после первого деплоя) |
   | `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_SSL` | healthflow | SMTP Яндекса из `.env` |
   | `TWILIO_*` | healthflow | если нужны SMS |
   | S3 (см. ниже) | healthflow | медиа-файлы |

   `DJANGO_SECRET_KEY` Render сгенерирует сам; `DATABASE_URL` подставится из базы.
4. Первый деплой — адрес появится в панели (`https://<имя>.onrender.com`).
5. Демо-данные: в панели → healthflow → **Shell**:
   ```
   cd HealthFlow && python manage.py seed_specialists && python manage.py seed_patients
   python manage.py createsuperuser
   ```

## Медиа-файлы (аватары, документы)

У контейнера Render нет постоянного диска: загруженные в админке файлы пропадут при деплое.
Варианты:
- **S3-совместимое хранилище** (Cloudflare R2 — бесплатно 10 ГБ): задайте в healthflow
  ```
  AWS_STORAGE_BUCKET_NAME=<bucket>
  AWS_ACCESS_KEY_ID=<ключ>
  AWS_SECRET_ACCESS_KEY=<секрет>
  AWS_S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com   # для R2
  AWS_S3_REGION_NAME=auto
  AWS_S3_CUSTOM_DOMAIN=pub-<hash>.r2.dev                            # публичный домен бакета
  ```
  При их наличии media отдаётся из бакета, всё остальное работает как раньше.
- Без S3 сайт работает, но картинки, загруженные после деплоя, будут теряться.

## Ограничения плана
- Пробный план действует 30 дней, затем сервисы удаляются (данные базы тоже).
- Postgres free-план на Render удаляется после истечения срока.
- Нейросеть-чат (`g4f`) на серверах Render может не работать — провайдеры часто блокируют
  дата-центры; сайт от этого не падает, просто ответ AI будет `None`.
- Это деплой тестовый: пароль администратора и секреты из `.env` были в истории git —
  для реального продакшена их надо сменить/ротировать.

## Проверка после деплоя
- `https://<имя>.onrender.com/` — главная;
- `/specialists/` — каталог (после seed);
- `/accounts/` — вход;
- `/admin/` — админка;
- в Telegram напишите боту `/start`.

## Локальная проверка прод-настроек (без Render)
```
cd HealthFlow
DJANGO_DEBUG=False ../.venv/Scripts/python.exe manage.py collectstatic --noinput
DJANGO_DEBUG=False ../.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000 --insecure
```
