from django.shortcuts import render, get_object_or_404, redirect
from django.templatetags.static import static
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from users.notifications import notify_about_message
from .AI import new_request
from .models import Chat, Message, Specialist, Note, Blood, BMI, Pressure, Rating, SpecialistApplication
import json


def notify_chat_recipient(request, chat, content):
    recipient = chat.user if chat.user_id != request.user.pk else chat.specialist.user
    if recipient.pk == request.user.pk:
        return
    chat_url = request.build_absolute_uri(reverse('profile_page')) + f'#chat-{chat.id}'
    notify_about_message(recipient, chat_url, content[:300])


def create_specialist(request):
    user = request.user

    # Проверка на существование заявки
    if SpecialistApplication.objects.filter(user=user).exists():
        return render(request, 'profile/wait.html')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        contact = request.POST.get('contact')
        specialization = request.POST.get('specialization') or 'other'
        additional_info = request.POST.get('additional_info')
        attached_file = request.FILES.get('attached_file')

        # Сохраняем данные в базу
        SpecialistApplication.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            contact=contact,
            specialization=specialization,
            additional_info=additional_info,
            attached_file=attached_file
        )

        return redirect(
            'profile_page')  # Страница, на которую перенаправляется пользователь после успешной отправки заявки

    return render(request, 'profile/profile_specialist.html', {
        'specialties': Specialist.SPECIALTY_CHOICES,
    })


@login_required
@require_POST
def update_profile(request):
    user = request.user
    photo = request.FILES.get('photo')
    if photo:
        user.photo = photo

    user.first_name = request.POST.get('name', user.first_name)
    user.last_name = request.POST.get('last_name', user.last_name)
    user.email = request.POST.get('email', user.email)
    user.save()

    response_data = {
        'status': 'success',
        'avatar_url': user.photo.url if user.photo else '',
        'name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,

    }

    return JsonResponse(response_data)


class PressureData:
    pass


class BloodData:
    pass


class BMIData:
    pass


from django.http import JsonResponse

@login_required
def add_note(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        additional_notes = request.POST.get('additional_notes')
        blood_data = request.POST.getlist('blood[]')
        pressure_data = request.POST.getlist('pressure[]')
        bmi_data = request.POST.getlist('bmi[]')
        file = request.FILES.get('file')

        if not date:
            return JsonResponse({'status': 'error', 'message': 'Дата не указана'})

        try:
            note = Note.objects.create(
                user=request.user,
                date=date,
                additional_notes=additional_notes,
                file=file
            )

            blood_entry = None
            if blood_data:
                blood_entry = Blood.objects.create(
                    note=note,
                    hemoglobin=blood_data[0] if blood_data[0] else None,
                    leukocytes=blood_data[1] if blood_data[1] else None,
                    lymphocytes=blood_data[2] if blood_data[2] else None
                )

            pressure_entry = None
            if pressure_data:
                pressure_entry = Pressure.objects.create(
                    note=note,
                    systolic=pressure_data[0] if pressure_data[0] else None,
                    diastolic=pressure_data[1] if pressure_data[1] else None,
                    pulse_rate=pressure_data[2] if pressure_data[2] else None
                )

            bmi_entry = None
            if bmi_data:
                bmi_entry = BMI.objects.create(
                    note=note,
                    height=bmi_data[0] if bmi_data[0] else None,
                    weight=bmi_data[1] if bmi_data[1] else None
                )

            return JsonResponse({
                'status': 'success',
                'note_id': note.id,
                'date': note.date,
                'additional_notes': note.additional_notes,
                'blood_data': {
                    'hemoglobin': blood_entry.hemoglobin if blood_entry else None,
                    'leukocytes': blood_entry.leukocytes if blood_entry else None,
                    'lymphocytes': blood_entry.lymphocytes if blood_entry else None,
                } if blood_entry else None,
                'pressure_data': {
                    'systolic': pressure_entry.systolic if pressure_entry else None,
                    'diastolic': pressure_entry.diastolic if pressure_entry else None,
                    'pulse_rate': pressure_entry.pulse_rate if pressure_entry else None,
                } if pressure_entry else None,
                'bmi_data': {
                    'height': bmi_entry.height if bmi_entry else None,
                    'weight': bmi_entry.weight if bmi_entry else None,
                } if bmi_entry else None
            })
        except Exception as e:
            print("Error while adding note:", str(e))
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error'})


# Обновление существующих представлений для загрузки заметок
@login_required
def profile_page(request):
    user = request.user
    try:
        specialist = Specialist.objects.get(user=user)
        is_specialist = True
        chats = Chat.objects.filter(specialist=specialist)
    except Specialist.DoesNotExist:
        is_specialist = False
        chats = Chat.objects.filter(user=user)

    notes = Note.objects.filter(user=user)
    if user.is_superuser:
        return redirect('/admin/')

    active = user.subscription_is_active()
    return render(request, 'profile/profile.html', {
        "name": user.first_name if user.first_name else "Пользователь",
        "last_name": user.last_name,
        "additional": user.email,
        "avatar": user.photo.url if user.photo else static('css/img/default-avatar.svg'),
        "chats": chats,
        "notes": notes.order_by('-date', '-id'),
        "subscription": user.subscription if active else 'FREE',
        "subscription_until": user.subscription_until if active else None,
        "is_specialist": is_specialist  # Передаем флаг в контекст
    })



@require_POST
def process_message(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Некорректный запрос.'}, status=400)

    message = (data.get('message') or '').strip()
    if not message:
        return JsonResponse({'error': 'Сообщение не может быть пустым.'}, status=400)
    if len(message) > 2000:
        return JsonResponse({'error': 'Слишком длинное сообщение (максимум 2000 символов).'}, status=400)

    try:
        response = new_request(message, request.user.pk)
    except Exception as e:
        print("AI error:", str(e))
        return JsonResponse(
            {'error': 'Нейросеть сейчас недоступна. Попробуйте ещё раз через минуту.'},
            status=503,
        )

    if not response:
        return JsonResponse({'error': 'Нейросеть не вернула ответ. Попробуйте переформулировать запрос.'}, status=503)
    return JsonResponse({'response': response})


@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user != chat.user and request.user != chat.specialist.user:
        return JsonResponse({'error': 'You do not have permission to view this chat.'}, status=403)

    messages = chat.messages.all()
    messages_data = [{
        'sender': message.sender.username,
        'content': message.content,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for message in messages]

    if request.user == chat.user:
        other_user = chat.specialist.user
    else:
        other_user = chat.user

    other_user_photo = other_user.photo.url if other_user.photo else static('css/img/default-avatar.svg')
    other_user_contact = other_user.email if other_user.email else ''

    # Получаем текущий рейтинг пользователя для этого специалиста
    try:
        user_rating = Rating.objects.get(specialist=chat.specialist, user=request.user).rating
    except Rating.DoesNotExist:
        user_rating = None

    average_rating = chat.specialist.average_rating()

    return JsonResponse({
        'chat_id': chat.id,
        'specialist': chat.specialist.user.first_name if request.user == chat.user else chat.user.first_name,
        'specialist_photo': other_user_photo,
        'specialist_contact': other_user_contact,
        'messages': messages_data,
        'user_rating': user_rating,
        'average_rating': average_rating,
        'user': request.user.username
    })

@login_required
def my_notes(request):
    notes = Note.objects.filter(user=request.user).order_by('-date', '-id')
    return JsonResponse({'notes': [note_payload(note) for note in notes]})


def _num(value, digits=2):
    if value is None:
        return None
    value = float(value)
    return int(value) if digits == 0 else round(value, digits)


def note_payload(note):
    blood = note.blood_data.first()
    pressure = note.pressure_data.first()
    bmi = note.bmi_data.first()
    return {
        'id': note.id,
        'date': note.date.strftime('%d.%m.%Y'),
        'text': note.additional_notes or '',
        'file_name': (note.file.name.rsplit('/', 1)[-1] if note.file else ''),
        'blood': {
            'hemoglobin': _num(blood.hemoglobin) if blood else None,
            'leukocytes': _num(blood.leukocytes) if blood else None,
            'lymphocytes': _num(blood.lymphocytes) if blood else None,
        } if blood else None,
        'pressure': {
            'systolic': pressure.systolic,
            'diastolic': pressure.diastolic,
            'pulse_rate': pressure.pulse_rate,
        } if pressure else None,
        'bmi': {
            'height': _num(bmi.height),
            'weight': _num(bmi.weight),
        } if bmi else None,
    }


def note_message_text(note):
    lines = [f"Заметка из профиля от {note.date.strftime('%d.%m.%Y')}"]
    if note.additional_notes:
        lines.append(note.additional_notes)
    blood = note.blood_data.first()
    if blood:
        parts = []
        if blood.hemoglobin:
            parts.append(f"гемоглобин {_num(blood.hemoglobin)} г/л")
        if blood.leukocytes:
            parts.append(f"лейкоциты {_num(blood.leukocytes)} тыс/мкл")
        if blood.lymphocytes:
            parts.append(f"лимфоциты {_num(blood.lymphocytes)} %")
        if parts:
            lines.append("Кровь: " + ", ".join(parts) + ".")
    pressure = note.pressure_data.first()
    if pressure and (pressure.systolic or pressure.diastolic):
        text = f"Давление: {pressure.systolic or '—'}/{pressure.diastolic or '—'} мм рт. ст."
        if pressure.pulse_rate:
            text += f", пульс {pressure.pulse_rate} уд/мин"
        lines.append(text + ".")
    bmi = note.bmi_data.first()
    if bmi and (bmi.height or bmi.weight):
        parts = []
        if bmi.height:
            parts.append(f"рост {_num(bmi.height)} см")
        if bmi.weight:
            parts.append(f"вес {_num(bmi.weight)} кг")
        lines.append("Показатели: " + ", ".join(parts) + ".")
    if note.file:
        lines.append("Файл: " + note.file.name.rsplit('/', 1)[-1])
    return "\n".join(lines)


@login_required
@require_POST
def send_notes(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user != chat.user:
        return JsonResponse({'error': 'Отправлять свои заметки можно только в своём диалоге со специалистом.'}, status=403)

    note_ids = request.POST.getlist('note_ids')
    comment = (request.POST.get('comment') or '').strip()
    if not note_ids and not comment:
        return JsonResponse({'error': 'Выберите заметку или напишите комментарий.'}, status=400)
    if len(note_ids) > 10:
        return JsonResponse({'error': 'Можно отправить не больше 10 заметок за раз.'}, status=400)

    notes = list(Note.objects.filter(user=request.user, id__in=note_ids).order_by('-date'))
    if len(notes) != len(set(note_ids)):
        return JsonResponse({'error': 'Часть заметок не найдена.'}, status=400)

    texts = [note_message_text(note) for note in notes]
    if comment:
        texts.append(comment)
    content = "\n\n".join(texts)

    Message.objects.create(chat=chat, sender=request.user, content=content)
    chat.last_message = content
    chat.save()
    notify_chat_recipient(request, chat, content)
    return JsonResponse({'status': 'success'})


@login_required
def send_message(request):
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        content = request.POST.get('message')
        chat = get_object_or_404(Chat, id=chat_id)
        if request.user != chat.user and request.user != chat.specialist.user:
            return JsonResponse({'error': 'You do not have permission to send messages in this chat.'}, status=403)

        message = Message.objects.create(chat=chat, sender=request.user, content=content)
        chat.last_message = content
        chat.save()
        notify_chat_recipient(request, chat, content)
        return JsonResponse(
            {'status': 'success', 'message': content, 'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'})


@login_required
@login_required
def search_specialist(request):
    query = request.GET.get('q', '')
    specialists = Specialist.objects.filter(
        is_published=True, name__icontains=query).values('id', 'name')
    return JsonResponse({'specialists': list(specialists)})


def specialists_catalog(request):
    query = (request.GET.get('q') or '').strip()
    specialty = request.GET.get('specialty') or ''

    specialists = Specialist.objects.filter(is_published=True).select_related('user').prefetch_related(
        'reviews__author', 'ratings')
    if query:
        specialists = specialists.filter(
            Q(name__icontains=query) | Q(about__icontains=query) | Q(city__icontains=query)
        )
    if specialty:
        specialists = specialists.filter(specialty=specialty)

    cards = []
    for specialist in specialists:
        ratings_count = specialist.ratings.count()
        if ratings_count % 10 == 1 and ratings_count % 100 != 11:
            rating_word = 'оценка'
        elif ratings_count % 10 in (2, 3, 4) and ratings_count % 100 not in (12, 13, 14):
            rating_word = 'оценки'
        else:
            rating_word = 'оценок'
        reviews = list(specialist.reviews.all()[:2])
        cards.append({
            'specialist': specialist,
            'rating': round(specialist.average_rating(), 1),
            'ratings_count': ratings_count,
            'rating_word': rating_word,
            'reviews': reviews,
            'reviews_count': specialist.reviews.count(),
        })

    return render(request, 'specialists/catalog.html', {
        'cards': cards,
        'query': query,
        'specialty': specialty,
        'specialties': Specialist.SPECIALTY_CHOICES,
        'total_published': Specialist.objects.filter(is_published=True).count(),
    })


def specialist_detail(request, specialist_id):
    specialist = get_object_or_404(
        Specialist.objects.select_related('user').prefetch_related('reviews__author'),
        id=specialist_id, is_published=True,
    )
    return render(request, 'specialists/detail.html', {
        'specialist': specialist,
        'rating': round(specialist.average_rating(), 1),
        'ratings_count': specialist.ratings.count(),
        'reviews': specialist.reviews.all(),
    })


@login_required
@require_POST
def start_chat(request):
    specialist_id = request.POST.get('specialist_id')
    specialist = get_object_or_404(Specialist, id=specialist_id)
    chat, created = Chat.objects.get_or_create(user=request.user, specialist=specialist)
    return JsonResponse({
        'status': 'success',
        'chatId': chat.id,
        'specialist_name': specialist.name,
        'specialist_photo': specialist.user.photo.url if specialist.user.photo else static('css/img/default-avatar.svg')
    })

@login_required
def get_note_details(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)

    blood_data = note.blood_data.first() if note.blood_data.exists() else None
    pressure_data = note.pressure_data.first() if note.pressure_data.exists() else None
    bmi_data = note.bmi_data.first() if note.bmi_data.exists() else None

    note_details = {
        'date': note.date,
        'additional_notes': note.additional_notes,
        'blood_data': {
            'hemoglobin': blood_data.hemoglobin,
            'leukocytes': blood_data.leukocytes,
            'lymphocytes': blood_data.lymphocytes,
        } if blood_data else None,
        'pressure_data': {
            'systolic': pressure_data.systolic,
            'diastolic': pressure_data.diastolic,
            'pulse_rate': pressure_data.pulse_rate,
        } if pressure_data else None,
        'bmi_data': {
            'height': bmi_data.height,
            'weight': bmi_data.weight,
        } if bmi_data else None
    }

    return JsonResponse(note_details)

@login_required
@require_POST
def set_rating(request):
    try:
        specialist_contact = request.POST.get('specialist_contact')
        rating_value = int(request.POST.get('rating'))
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid input data'})

    specialist = get_object_or_404(Specialist, user__email=specialist_contact)
    user = request.user

    # Update or create the rating
    rating, created = Rating.objects.update_or_create(
        user=user,
        specialist=specialist,
        defaults={'rating': rating_value}
    )

    # Recalculate the average rating
    new_average_rating = specialist.average_rating()

    return JsonResponse({'status': 'success', 'new_average_rating': new_average_rating})


@login_required
def delete_chat(request, chat_id):
    if request.method == 'POST':
        chat = get_object_or_404(Chat, id=chat_id)

        if request.user == chat.user or request.user == chat.specialist.user:
            chat.delete()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'У вас нет прав на удаление этого чата.'}, status=403)

    return JsonResponse({'status': 'error', 'message': 'Неверный метод запроса.'}, status=400)


@login_required
def get_bmi_data(request):
    user = request.user

    # Извлечение данных BMI
    bmi_data = BMI.objects.filter(note__user=user).values('note__date', 'height', 'weight')

    # Извлечение данных Blood
    blood_data = Blood.objects.filter(note__user=user).values('note__date', 'hemoglobin', 'leukocytes', 'lymphocytes')

    # Извлечение данных Pressure
    pressure_data = Pressure.objects.filter(note__user=user).values('note__date', 'systolic', 'diastolic', 'pulse_rate')

    data = {
        'dates': [item['note__date'] for item in bmi_data],
        'heights': [float(item['height']) if item['height'] is not None else None for item in bmi_data],
        'weights': [float(item['weight']) if item['weight'] is not None else None for item in bmi_data],
        'hemoglobin': [float(item['hemoglobin']) if item['hemoglobin'] is not None else None for item in blood_data],
        'leukocytes': [float(item['leukocytes']) if item['leukocytes'] is not None else None for item in blood_data],
        'lymphocytes': [float(item['lymphocytes']) if item['lymphocytes'] is not None else None for item in blood_data],
        'systolic': [float(item['systolic']) if item['systolic'] is not None else None for item in pressure_data],
        'diastolic': [float(item['diastolic']) if item['diastolic'] is not None else None for item in pressure_data],
        'pulse_rate': [float(item['pulse_rate']) if item['pulse_rate'] is not None else None for item in pressure_data],
    }

    return JsonResponse(data)