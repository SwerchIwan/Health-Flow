import logging
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def normalize_phone(raw):
    """Приводит номер к виду +375XXXXXXXXX / +7XXXXXXXXXX, возвращает None если номер некорректен."""
    if not raw:
        return None
    digits = re.sub(r'\D', '', str(raw))
    if len(digits) < 10 or len(digits) > 15:
        return None
    if digits.startswith('80') and len(digits) == 12:
        digits = '375' + digits[2:]
    elif len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '375' + digits
    return '+' + digits


def send_email(to, subject, template, context, text_body=''):
    try:
        html_message = render_to_string(template, context)
        message = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [to])
        message.attach_alternative(html_message, 'text/html')
        message.send()
        return True
    except Exception:
        logger.exception('Не удалось отправить письмо на %s', to)
        return False


def send_email_code(to, code):
    return send_email(
        to,
        'Код подтверждения Health Flow AI',
        'email_code.html',
        {'code': code, 'ttl_minutes': settings.VERIFICATION_CODE_TTL // 60},
        text_body=f'Ваш код подтверждения: {code}. Код действует {settings.VERIFICATION_CODE_TTL // 60} минут.',
    )


def send_sms(to, text):
    """Возвращает (ok, error). Без настроенного Twilio — (False, причина)."""
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
        return False, 'Twilio не настроен'
    if not to:
        return False, 'Нет номера телефона'
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(body=text, from_=settings.TWILIO_FROM_NUMBER, to=to)
        return True, ''
    except Exception as ex:
        logger.warning('Не удалось отправить SMS на %s: %s', to, ex)
        return False, str(ex)


def send_verification_code(choice, email, phone, code):
    """Отправляет код на почту или SMS. Возвращает (ok, error)."""
    if choice == 'email':
        ok = send_email_code(email, code)
        return ok, '' if ok else 'Не удалось отправить письмо'
    ok, error = send_sms(phone, f'Ваш код подтверждения Health Flow AI: {code}')
    if not ok:
        logger.error('SMS для %s не отправлено: %s', phone, error)
    return ok, error


def notify_about_message(recipient, chat_url, preview):
    """Уведомляет получателя нового сообщения в чате письмом и SMS."""
    if recipient.email:
        send_email(
            recipient.email,
            'Новое сообщение в Health Flow AI',
            'email_new_message.html',
            {'preview': preview, 'chat_url': chat_url},
            text_body=f'Новое сообщение: {preview}\n{chat_url}',
        )
    if recipient.phone and recipient.phone_notifications:
        send_sms(recipient.phone, f'Health Flow AI: новое сообщение — {preview[:100]}. {chat_url}')
