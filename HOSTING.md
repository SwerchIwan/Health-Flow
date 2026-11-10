# Hosting: local PC + public tunnel

Публичный адрес даётся SSH reverse-tunnel на сервис **Serveo** (`serveo.net`) —
он не требует регистрации и карты. Открывайте его только по вашему запросу:
команда ниже делает локальный сайт доступным из интернета.

## Запуск (нужны уже запущенный сайт на 127.0.0.1:8000 и интернет)

```
cd C:/Users/12059/PycharmProjects/Health-Flow

# 1. стек
docker compose up -d

# 2. туннель (открывает сайт в интернет)
set PUBLIC_URL=https://healthflow.serveo.net
ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:8000 serveo.net
```

При первом подключении Serveo выдаст случайный поддомен — он будет в выводе ssh.
Если нужен фиксированный `healthflow.serveo.net`, регистрация ключа описана на serveo.net.

3. Задайте `PUBLIC_URL` в окружении Django (settings сам добавит домен в `ALLOWED_HOSTS` и
   `CSRF_TRUSTED_ORIGINS`). В Docker:
```
set PUBLIC_URL=https://<этот-адрес>
docker compose up -d --force-recreate web bot
```

## Важно
- Туннель живёт, пока открыты ssh и сам ПК; всё, что закрыто в `.env` (секреты, TELEGRAM_BOT_TOKEN), попадает в интернет через сайт.
- Сайт в режиме разработки (`DJANGO_DEBUG=True`) — перед публикацией включите `DJANGO_DEBUG=False`.
- Ссылка в Telegram-боте берётся из `SITE_URL` — для публичного адреса задайте `SITE_URL=https://<этот-адрес>`.

## LAN (без интернета)
В рамках домашней Wi-Fi: `http://192.168.0.111:8000` (QR: `lan_qr.png`), но Windows firewall
должен пропускать входящие на 8000 — это меняется только с вашего явного согласия.
