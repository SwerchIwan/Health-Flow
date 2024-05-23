from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .AI import new_request
from .models import Chat, Message, Specialist, Note, Blood, BMI, Pressure

@login_required
@require_POST
def update_profile(request):
    if request.method == 'POST':
        # Обработка данных профиля и сохранение в базе данных
        # Обработка изображения профиля
        photo = request.FILES.get('photo')
        if photo:
            request.user.photo = photo

        # Обработка других данных профиля
        request.user.first_name = request.POST.get('name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.save()

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'})


@require_POST
@login_required
def add_note(request):
    date = request.POST.get('date')
    additional_notes = request.POST.get('additional_notes')
    file = request.FILES.get('file')
    height = request.POST.get('height')
    weight = request.POST.get('weight')

    note = Note.objects.create(user=request.user, date=date, additional_notes=additional_notes,
                               file=file)

    # Если данные для крови, давления и ИМТ предоставлены, сохраняем их
    blood_data = request.POST.getlist('blood[]')
    if blood_data:
        hemoglobin, leukocytes, lymphocytes = blood_data
        blood = Blood.objects.create(note=note, hemoglobin=hemoglobin, leukocytes=leukocytes, lymphocytes=lymphocytes)

    pressure_data = request.POST.getlist('pressure[]')
    if pressure_data:
        systolic, diastolic, pulse_rate = pressure_data
        pressure = Pressure.objects.create(note=note, systolic=systolic, diastolic=diastolic, pulse_rate=pulse_rate)

    bmi_data = request.POST.getlist('bmi[]')
    if bmi_data:
        height, weight = bmi_data
        bmi = BMI.objects.create(note=note, height=height, weight=weight)

    return JsonResponse({'status': 'success', 'note_id': note.id})
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
    return JsonResponse({
        'chat_id': chat.id,
        'specialist': chat.specialist.name,
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
