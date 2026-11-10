# Публичный адрес: Serveo-туннель

Открывать туннель можно только по вашему решению: он делает локальный сайт доступным
всем в интернете. Ниже — куда именно вводить команды.

## Куда вводить

Всё выполняется в этой же сессии Qoder CLI — в поле ввода наберите команду с `!`
в начале и Enter:

```
! <команда>
```

Либо в обычном терминале: Git Bash или PowerShell в папке проекта.

## Шаги

1. Сайт уже работает в Docker: `http://127.0.0.1:8000`.

2. Поднимите туннель (на один шаг, не нужен `PUBLIC_URL` — Serveo сам выдаст адрес):

```
! ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:8000 serveo.net
```

В выводе появится строка вида `Forwarding HTTP traffic from https://xxxx.serveo.net` —
это и есть публичный адрес. Окно с ssh должно оставаться открытым, пока сайт нужен снаружи.

3. Впишите этот адрес в окружение:

Git Bash:
```
! PUBLIC_URL=https://xxxx.serveo.net docker compose up -d --force-recreate web bot
```
PowerShell:
```
! $env:PUBLIC_URL="https://xxxx.serveo.net"; docker compose up -d --force-recreate web bot
```

settings сам добавит домен в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.
Опционально: `SITE_URL=https://xxxx.serveo.net` — чтобы кнопка в Telegram-боте вела на публичный адрес.

4. Откройте `https://xxxx.serveo.net` в браузере. Чтобы остановить доступ — Ctrl+C в окне с ssh.

## Фиксированный поддомен

Случайный адрес меняется при каждом старте. Постоянный `https://healthflow.serveo.net`:

```
! ssh-keygen -t ed25519 -f ~/.ssh/serveo -N ""
! serveo.net   # регистрация ключа — см. инструкцию на сайте, или:
! ssh -i ~/.ssh/serveo -R healthflow:80:127.0.0.1:8000 serveo.net
```
поддомен указывается в `-R <имя>:80:...`.

## Важно
- Пока туннель открыт, сайт (и всё, что он отдаёт) доступен из интернета. В `DJANGO_DEBUG=True`
  страницы ошибок показывают внутренности — перед публичным показом поставьте `DJANGO_DEBUG=False`.
- Секреты из `.env` остаются на вашем ПК, но любой, кто получит ссылку, ходит по живому сайту
  и его базе данных.
- Windows firewall ничего не меняет — ssh соединяется исходящим.
- Если Serveo недоступен: запасной вариант — `npx localtunnel --port 8000` (нужен Node.js) или
  `cloudflared tunnel --url http://127.0.0.1:8000` (если сеть пускает Cloudflare).

## LAN (без интернета)
В рамках домашней Wi-Fi: `http://192.168.0.111:8000` (QR: `lan_qr.png`), но Windows firewall
должен пропускать входящие на 8000 — это меняется только с вашего явного согласия.
