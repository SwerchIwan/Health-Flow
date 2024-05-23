import secrets
import string
from random import random

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.cache import cache
from django.db import models
from django.utils import timezone
import json

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
            user = User.objects.filter(email=auth_input).first()  # Найти пользователя по электронной почте
            if user is not None:
                user = authenticate(request, username=user.username, password=password)  # Проверить пароль
        elif auth_choice == 'phone':
            user = authenticate(request, username=auth_input, password=password)  # Найти пользователя по телефону
        else:
            user = None

        if user and user.is_active:
            login(request, user)
            return HttpResponseRedirect(reverse('profile_page'))
        else:
            return HttpResponse("Invalid login details")
    else:
        return redirect('auth_page')

def logout_user(request):
    logout(request)
    return redirect('auth_page')

def reg_page(request):
    return render(request, 'additionally/reg.html')

def check(request):
    return render(request, 'confirmation_sent.html')

def register_user(request):
    if request.method == 'POST':
        email = request.POST.get('inputField')
        password = request.POST.get('password')

        # Check if user with this email already exists
        if User.objects.filter(email=email).exists():
            return HttpResponse("User with this email already exists")

        # Generate username based on email
        username = email.split('@')[0]

        # Create a temporary user object with is_active=False
        temp_user = User(username=username, email=email)
        temp_user.set_password(password)
        temp_user.is_active = False

        # Generate a unique token for registration confirmation
        confirmation_token = PasswordResetTokenGenerator().make_token(temp_user)

        # Save user data in cache
        user_data = {'username': username, 'email': email, 'password': password}
        cache.set(confirmation_token, json.dumps(user_data), timeout=3600)  # Set expiration time (e.g., 1 hour)

        # Send email with confirmation link
        confirmation_link = request.build_absolute_uri(reverse('confirm_registration', args=[confirmation_token]))
        email_subject = 'Registration Confirmation'
        email_body = render_to_string('email_confirmation.html', {'confirmation_link': confirmation_link})
        send_mail(email_subject, email_body, 'kiselslaw@yandex.ru', [email])

        return render(request, 'confirmation_sent.html')
    else:
        return redirect('auth_page')

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


