from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from .AI import new_request
from .models import Chat, Message, Specialist, Note, Blood, BMI, Pressure, Rating, SpecialistApplication
import json


def create_specialist(request):
    user = request.user

    # Проверка на существование заявки
    if SpecialistApplication.objects.filter(user=user).exists():
        return redirect('another_page_url_name')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        contact = request.POST.get('contact')
        additional_info = request.POST.get('additional_info')
        attached_file = request.FILES.get('attached_file')

        # Сохраняем данные в базу
        SpecialistApplication.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            contact=contact,
            additional_info=additional_info,
            attached_file=attached_file
        )

        return redirect(
            'profile_page')  # Страница, на которую перенаправляется пользователь после успешной отправки заявки

    return render(request, 'profile/profile_specialist.html')


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
@csrf_exempt
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
    else:
        return render(request, 'profile/profile.html', {
            "name": user.first_name if user.first_name else "Пользователь",
            "last_name": user.last_name,
            "additional": user.email,
            "avatar": user.photo.url if user.photo else 'https://avatars.mds.yandex.net/i?id=6f6125e91480fabbf7af426a0654d60c61c3f63e-12638015-images-thumbs&n=13',
            "chats": chats,
            "notes": notes,
            "subscription": user.subscription,
            "is_specialist": is_specialist  # Передаем флаг в контекст
        })



@csrf_exempt
def process_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message')
        response = new_request(message)
        return JsonResponse({'response': response})
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'})


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

    other_user_photo = other_user.photo.url if hasattr(other_user,
                                                       'photo') and other_user.photo else 'https://avatars.mds.yandex.net/i?id=6f6125e91480fabbf7af426a0654d60c61c3f63e-12638015-images-thumbs&n=13'
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
@csrf_exempt
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
        return JsonResponse(
            {'status': 'success', 'message': content, 'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'})


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
    return JsonResponse({
        'status': 'success',
        'chatId': chat.id,
        'specialist_name': specialist.name,
        'specialist_photo': specialist.user.photo.url if specialist.user.photo else 'https://avatars.mds.yandex.net/i?id=6f6125e91480fabbf7af426a0654d60c61c3f63e-12638015-images-thumbs&n=13'
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
@csrf_exempt
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
@csrf_exempt
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