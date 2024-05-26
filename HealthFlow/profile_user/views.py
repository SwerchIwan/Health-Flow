from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from .AI import new_request
from .models import Chat, Message, Specialist, Note, Blood, BMI, Pressure

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
        'email': user.email
    }

    return JsonResponse(response_data)


class PressureData:
    pass


class BloodData:
    pass


class BMIData:
    pass


@login_required
@csrf_exempt
def add_note(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        additional_notes = request.POST.get('additional_notes')
        blood_data = request.POST.getlist('blood[]')
        pressure_data = request.POST.getlist('pressure[]')
        bmi_data = request.POST.getlist('bmi[]')
        file = request.FILES.get('file')

        note = Note.objects.create(
            user=request.user,
            date=date,
            additional_notes=additional_notes,
            file=file
        )

        if blood_data:
            Blood.objects.create(
                note=note,
                hemoglobin=blood_data[0],
                leukocytes=blood_data[1],
                lymphocytes=blood_data[2]
            )

        if pressure_data:
            Pressure.objects.create(
                note=note,
                systolic=pressure_data[0],
                diastolic=pressure_data[1],
                pulse_rate=pressure_data[2]
            )

        if bmi_data:
            BMI.objects.create(
                note=note,
                height=bmi_data[0],
                weight=bmi_data[1]
            )

        return JsonResponse({'status': 'success', 'note_id': note.id})
    else:
        return JsonResponse({'status': 'error'})


# Обновление существующих представлений для загрузки заметок
@login_required
def profile_page(request):
    user = request.user
    try:
        specialist = Specialist.objects.get(user=user)
        chats = Chat.objects.filter(specialist=specialist)
    except Specialist.DoesNotExist:
        chats = Chat.objects.filter(user=user)

    notes = Note.objects.filter(user=user)

    return render(request, 'profile/profile.html', {
        "name": user.first_name if user.first_name else "Пользователь",
        "last_name": user.last_name,
        "additional": user.email,
        "avatar": user.photo.url if user.photo else 'https://avatars.mds.yandex.net/i?id=6f6125e91480fabbf7af426a0654d60c61c3f63e-12638015-images-thumbs&n=13',
        "chats": chats,
        "notes": notes,
    })

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    messages = chat.messages.all()
    messages_data = [{
        'sender': message.sender.username,
        'content': message.content,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for message in messages]

    # Проверяем наличие фото у специалиста
    specialist_photo = chat.specialist.user.photo.url if chat.specialist.user.photo else 'https://avatars.mds.yandex.net/i?id=6f6125e91480fabbf7af426a0654d60c61c3f63e-12638015-images-thumbs&n=13'

    # Проверяем наличие email у специалиста
    specialist_email = chat.specialist.user.email if chat.specialist.user.email else chat.specialist.user.phone

    return JsonResponse({
        'chat_id': chat.id,
        'specialist': chat.specialist.name,
        'specialist_photo': specialist_photo,  # Устанавливаем фото специалиста или дефолтное изображение
        'specialist_contact': specialist_email,  # Устанавливаем email специалиста или его номер телефона
        'messages': messages_data
    })


@login_required
@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        content = request.POST.get('message')
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        message = Message.objects.create(chat=chat, sender=request.user, content=content)
        chat.last_message = content
        chat.save()
        return JsonResponse({'status': 'success', 'message': content, 'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'})

@csrf_exempt
def process_message(request):
    if request.method == 'POST':
        message = request.POST.get('message')  # Предполагается, что вы отправляете сообщение с помощью POST запроса
        response = new_request(message)  # Вызов вашей функции для нейросети
        return JsonResponse({'response': response})
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'})

@login_required
def search_specialist(request):
    query = request.GET.get('q', '')
    specialists = Specialist.objects.filter(Q(name__icontains=query)).values('id', 'name')
    return JsonResponse({'specialists': list(specialists)})

@login_required
@csrf_exempt
@require_POST
def start_chat(request):
    specialist_id = request.POST.get('specialist_id')
    specialist = get_object_or_404(Specialist, id=specialist_id)
    chat, created = Chat.objects.get_or_create(user=request.user, specialist=specialist)
    return JsonResponse({'status': 'success', 'chat_id': chat.id})


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

