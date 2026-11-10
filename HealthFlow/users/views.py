import json
import random

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .notifications import normalize_phone, send_verification_code

User = get_user_model()

CODE_ATTEMPTS_LIMIT = 5


# ---------- Регистрация ----------

def reg_page(request):
    """GET-форма регистрации (POST обрабатывается в register_user)."""
    return render(request, 'additionally/reg.html')


def _pending_registration_key(choice, contact):
    return f'registration:{choice}:{contact}'


def _redirect_to_code_step(request, mode, choice, contact, code_shown=None, notice=None, error=None):
    payload = {'mode': mode, 'choice': choice, 'contact': contact}
    if code_shown:
        payload['code_shown'] = code_shown
    if notice:
        payload['notice'] = notice
    if error:
        payload['error_message'] = error
    return render(request, 'additionally/enter_confirmation_code.html', payload)


def register_user(request):
    if request.method != 'POST':
        return render(request, 'additionally/reg.html')

    auth_choice = request.POST.get('choice')
    auth_input = (request.POST.get('inputField') or '').strip()
    password = request.POST.get('password') or ''
    password_confirm = request.POST.get('password_confirm')

    if not auth_input or not password:
        return render(request, 'additionally/reg.html',
                      {'error_message': 'Заполните все поля.'})

    if password_confirm is not None and password != password_confirm:
        return render(request, 'additionally/reg.html',
                      {'error_message': 'Пароли не совпадают.'})

    if len(password) < 8:
        return render(request, 'additionally/reg.html',
                      {'error_message': 'Пароль должен содержать минимум 8 символов.'})

    if auth_choice == 'email':
        email = auth_input.lower()
        if User.objects.filter(email__iexact=email).exists():
            return render(request, 'additionally/reg.html',
                          {'error_message': 'Пользователь с такой почтой уже зарегистрирован.'})
        contact = email
        username = email.split('@')[0]
    elif auth_choice == 'phone':
        phone = normalize_phone(auth_input)
        if not phone:
            return render(request, 'additionally/reg.html',
                          {'error_message': 'Введите корректный номер телефона.'})
        if User.objects.filter(phone=phone).exists():
            return render(request, 'additionally/reg.html',
                          {'error_message': 'Пользователь с таким номером уже зарегистрирован.'})
        contact = phone
        username = phone
    else:
        return redirect('auth_page')

    if User.objects.filter(username=username).exists():
        username = f'{username}_{random.randint(1000, 9999)}'

    code = f'{random.randint(100000, 999999)}'
    cache.set(
        _pending_registration_key(auth_choice, contact),
        json.dumps({'username': username, 'password': password, 'code': code, 'attempts': 0}),
        timeout=settings.VERIFICATION_CODE_TTL,
    )

    sent, error = send_verification_code(
        auth_choice, email if auth_choice == 'email' else None,
        contact if auth_choice == 'phone' else None, code,
    )
    code_shown = None
    if not sent:
        if auth_choice == 'email':
            return render(request, 'additionally/reg.html',
                          {'error_message': 'Не удалось отправить письмо с кодом. Попробуйте позже.'})
        code_shown = code if settings.SMS_SHOW_CODE_ON_FAILURE else None

    return _redirect_to_code_step(request, 'register', auth_choice, contact, code_shown=code_shown,
                                  notice='Код отправлен' if sent else 'SMS не удалось отправить')


def confirm_registration_code(request):
    if request.method != 'POST':
        return redirect('reg_page')

    auth_choice = request.POST.get('choice')
    contact = (request.POST.get('contact') or request.POST.get('phone') or '').strip()
    entered = (request.POST.get('confirmation_code') or '').strip()

    if auth_choice == 'phone':
        contact = normalize_phone(contact) or contact
    elif auth_choice == 'email':
        contact = contact.lower()

    cache_key = _pending_registration_key(auth_choice, contact)
    user_data_json = cache.get(cache_key)
    if not user_data_json:
        return _redirect_to_code_step(request, 'register', auth_choice, contact,
                                      error='Код истёк. Пройдите регистрацию заново.')

    user_data = json.loads(user_data_json)
    if entered != user_data['code']:
        user_data['attempts'] += 1
        if user_data['attempts'] >= CODE_ATTEMPTS_LIMIT:
            cache.delete(cache_key)
            return _redirect_to_code_step(request, 'register', auth_choice, contact,
                                          error='Слишком много неверных попыток. Зарегистрируйтесь заново.')
        cache.set(cache_key, json.dumps(user_data), timeout=settings.VERIFICATION_CODE_TTL)
        return _redirect_to_code_step(request, 'register', auth_choice, contact, error='Неверный код.')

    if User.objects.filter(username=user_data['username']).exists():
        cache.delete(cache_key)
        return _redirect_to_code_step(request, 'register', auth_choice, contact,
                                      error='Пользователь уже создан. Войдите в аккаунт.')

    create_kwargs = {'password': user_data['password']}
    if auth_choice == 'email':
        create_kwargs['email'] = contact
    else:
        create_kwargs['phone'] = contact
    User.objects.create_user(username=user_data['username'], **create_kwargs)
    cache.delete(cache_key)

    return render(request, 'registration_confirmed.html')


def confirm_registration(request, token):
    return HttpResponseRedirect(reverse('auth_page'))


# ---------- Вход ----------

def auth_page(request):
    return render(request, 'additionally/aut-step-one.html')


def auth_page_two(request):
    if request.method != 'POST':
        return redirect('auth_page')

    choice = request.POST.get('choice')
    raw_input = (request.POST.get('inputField') or '').strip()

    if choice == 'email':
        contact = raw_input.lower()
        user = User.objects.filter(email__iexact=contact).first()
    elif choice == 'phone':
        contact = normalize_phone(raw_input)
        user = User.objects.filter(phone=contact).first() if contact else None
    else:
        user = None

    if not user:
        return render(request, 'additionally/aut-step-one.html',
                      {'error_message': 'Пользователь не найден.'})

    request.session['auth_choice'] = choice
    request.session['auth_input'] = contact
    return render(request, 'additionally/aut-step-two.html')


def login_user(request):
    if request.method != 'POST':
        return redirect('auth_page')

    auth_input = request.session.get('auth_input')
    auth_choice = request.session.get('auth_choice')
    password = request.POST.get('inputField')
    action = request.POST.get('action', 'password')

    if not auth_input or auth_choice not in ('email', 'phone'):
        return redirect('auth_page')

    if auth_choice == 'email':
        user = User.objects.filter(email__iexact=auth_input).first()
    else:
        user = User.objects.filter(phone=auth_input).first()

    if action == 'send_code':
        if not user:
            return render(request, 'additionally/aut-step-two.html',
                          {'code_sent': True, 'error_message': 'Пользователь не найден.'})

        code = f'{random.randint(100000, 999999)}'
        cache.set(f'login_code:{user.pk}', json.dumps({'code': code, 'attempts': 0}),
                  timeout=settings.VERIFICATION_CODE_TTL)
        sent, _ = send_verification_code(
            auth_choice,
            user.email if auth_choice == 'email' else None,
            user.phone if auth_choice == 'phone' else None,
            code,
        )
        context = {'code_sent': True, 'notice': 'Код отправлен.' if sent else 'Не удалось отправить код.'}
        if not sent and auth_choice == 'phone' and settings.SMS_SHOW_CODE_ON_FAILURE:
            context['code_shown'] = code
        return render(request, 'additionally/aut-step-two.html', context)

    if action == 'code':
        cached = cache.get(f'login_code:{user.pk}') if user else None
        entered = (request.POST.get('confirmation_code') or '').strip()
        if not cached or not user:
            return render(request, 'additionally/aut-step-two.html',
                          {'code_sent': True, 'error_message': 'Отправьте код заново.'})
        data = json.loads(cached)
        if entered != data['code']:
            data['attempts'] += 1
            if data['attempts'] >= CODE_ATTEMPTS_LIMIT:
                cache.delete(f'login_code:{user.pk}')
                return render(request, 'additionally/aut-step-two.html',
                              {'code_sent': True, 'error_message': 'Слишком много попыток. Отправьте код заново.'})
            cache.set(f'login_code:{user.pk}', json.dumps(data), timeout=settings.VERIFICATION_CODE_TTL)
            return render(request, 'additionally/aut-step-two.html',
                          {'code_sent': True, 'error_message': 'Неверный код.'})
        cache.delete(f'login_code:{user.pk}')
        authenticated = user if user.is_active else None
    else:
        authenticated = authenticate(request, username=user.username, password=password) if user else None

    if authenticated and authenticated.is_active:
        login(request, authenticated)
        request.session.pop('auth_input', None)
        request.session.pop('auth_choice', None)
        if authenticated.is_superuser:
            return redirect('/admin/')
        return HttpResponseRedirect(reverse('profile_page'))

    return render(request, 'additionally/aut-step-two.html',
                  {'error_message': 'Неверный пароль.'})


def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True})
    return redirect('auth_page')


def check(request):
    return redirect('reg_page')
