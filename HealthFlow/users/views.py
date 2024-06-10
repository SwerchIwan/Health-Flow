import secrets
import string
import random
from twilio.rest import Client
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.cache import cache
from django.db import models
from django.utils import timezone
import json
from twilio.rest import Client
import os

User = get_user_model()

def auth_page(request):
    return render(request, 'aut-step-one.html')

def auth_page_two(request):
    if request.method == 'POST':
        choice = request.POST.get('choice')
        input_field = request.POST.get('inputField')

        # Проверяем, существует ли пользователь с таким email или телефоном
        if choice == 'email':
            user_exists = User.objects.filter(email=input_field).exists()  # Поиск пользователя по электронной почте
        elif choice == 'phone':
            user_exists = User.objects.filter(phone=input_field).exists()  # Поиск пользователя по телефону
        else:
            user_exists = False

        if user_exists:
            # Сохраняем данные в сессии и перенаправляем на вторую форму
            request.session['auth_choice'] = choice
            request.session['auth_input'] = input_field
            return render(request, 'additionally/aut-step-two.html')
        else:
            # Если пользователь не найден, возвращаем ошибку
            return redirect('auth_page')
    else:
        return redirect('auth_page')

def login_user(request):
    if request.method == 'POST':
        password = request.POST.get('inputField')
        auth_input = request.session.get('auth_input')
        auth_choice = request.session.get('auth_choice')

        if auth_choice == 'email':
            user = User.objects.filter(email=auth_input).first()
            if user is not None:
                user = authenticate(request, username=user.username, password=password)
        elif auth_choice == 'phone':
            user = User.objects.filter(phone=auth_input).first()
            if user is not None:
                user = authenticate(request, username=user.username, password=password)
        else:
            user = None

        if user and user.is_active:
            login(request, user)
            if user.is_superuser:
                return redirect('/admin/')
            else:
                return HttpResponseRedirect(reverse('profile_page'))
        else:
            error_message = "Неверный пароль"
            return render(request, 'additionally/aut-step-two.html', {'error_message': error_message})
    else:
        return redirect('auth_page')

def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True})
    return redirect('auth_page')

def reg_page(request):
    return render(request, 'additionally/reg.html')

def check(request):
    return render(request, 'confirmation_sent.html')





def register_user(request):
    if request.method == 'POST':
        auth_input = request.POST.get('inputField')
        password = request.POST.get('password')
        auth_choice = request.POST.get('choice')  # 'email' or 'phone'

        if not auth_input or not password:
            return HttpResponse("All fields must be filled.")

        if auth_choice == 'email':
            email = auth_input

            if User.objects.filter(email=email).exists():
                return HttpResponse("User with this email already exists")

            username = email.split('@')[0]

            temp_user = User(username=username, email=email)
            temp_user.set_password(password)
            temp_user.is_active = False

            confirmation_token = PasswordResetTokenGenerator().make_token(temp_user)

            user_data = {'username': username, 'email': email, 'password': password}
            cache.set(confirmation_token, json.dumps(user_data), timeout=3600)

            confirmation_link = request.build_absolute_uri(reverse('confirm_registration', args=[confirmation_token]))
            email_subject = 'Registration Confirmation'
            confirmation_code = confirmation_link  # Example of a confirmation code
            logo_path = 'static/css/img/logo.png'

            context = {'confirmation_link': confirmation_link, 'confirmation_code': confirmation_code, 'logo_path': logo_path}
            html_message = render_to_string('email_confirmation.html', context)

            email_message = EmailMultiAlternatives(
                email_subject,
                '',
                'kiselslaw@yandex.ru',
                [email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()

            return render(request, 'confirmation_sent.html')

        elif auth_choice == 'phone':
            phone = auth_input

            if User.objects.filter(username=phone).exists():  # Assuming phone number is used as username
                return HttpResponse("User with this phone already exists")

            username = phone
            confirmation_code = random.randint(100000, 999999)

            user_data = {'username': username, 'phone': phone, 'password': password, 'confirmation_code': str(confirmation_code)}
            cache.set(f'{phone}_confirmation_code', json.dumps(user_data), timeout=3600)

            sms_status = sending_sms(text=f'Ваш код подтверждения {confirmation_code}', receiver=phone)

            return render(request, 'confirmation_sent.html', {'phone': phone})

    else:
        return redirect('auth_page')

def sending_sms(text='Wake up Neo...', receiver='+89876540000'):
    try:
        account_sid = 'AC10a061a838658a53db4f0272d4f2a89d'
        auth_token = '8d42453b72ad19b03fed92764db7b264'

        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=text,
            from_='+12077695734',  # Replace with your Twilio number
            to=receiver
        )

        return 'The message was successfully sent!'
    except Exception as ex:
        return f'Something went wrong... :({ex})'

def confirm_phone_registration(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        confirmation_code = request.POST.get('confirmation_code')
        user_data_json = cache.get(f'{phone}_confirmation_code')

        if user_data_json:
            user_data = json.loads(user_data_json)
            cached_code = user_data['confirmation_code']

            if str(cached_code) == str(confirmation_code):
                user = User.objects.create_user(username=user_data['username'], password=user_data['password'])
                user.is_active = True
                user.save()

                cache.delete(f'{phone}_confirmation_code')

                return render(request, 'registration_confirmed.html')
            else:
                error_message = "Invalid confirmation code."
                return render(request, 'enter_confirmation_code.html', {'phone': phone, 'error_message': error_message})
        else:
            return HttpResponse("Invalid or expired confirmation code.")
    else:
        return render(request, 'enter_confirmation_code.html')

def confirm_registration(request, token):
    user_data_json = cache.get(token)

    if user_data_json:
        user_data = json.loads(user_data_json)
        username = user_data['username']
        email = user_data['email']
        password = user_data['password']

        # Check if user with this email already exists (just in case)
        if not User.objects.filter(email=email).exists():
            # Create a new user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_active = True
            user.save()

            # Remove the token from cache after successful confirmation
            cache.delete(token)

            return render(request, 'registration_confirmed.html')

    return HttpResponse("Invalid link or link expired")


# def confirmation_page(request):
#     if request.method == 'POST':
#         choice = request.POST.get('choice')
#         if choice == 'phone':
#             confirmation_message = "Для продолжения введите код, отправленный на ваш номер телефона"
#         elif choice == 'email':
#             confirmation_message = "Для продолжения введите код, отправленный на вашу почту"
#         else:
#             confirmation_message = "Неизвестный выбор"
#         return render(request, 'additionally/confirmation.html', {'confirmation_message': confirmation_message})
#     else:
#         return redirect('reg_page')


