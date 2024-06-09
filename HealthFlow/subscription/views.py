from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def pay_page(request):
    subscription = request.GET.get('subscription', 'STANDART')
    return render(request, 'additionally/pay_page.html', {'subscription': subscription})

@login_required
def process_payment(request):
    if request.method == 'POST':
        # Получите данные из формы
        subscription = request.POST.get('subscription')
        card_number = request.POST.get('card_number')
        card_name = request.POST.get('card_name')
        validity = request.POST.get('validity')
        cvv = request.POST.get('cvv')

        # Здесь вы можете добавить логику обработки платежа

        # Обновите подписку пользователя
        user = request.user
        user.subscription = subscription
        user.save()

        # Сообщение об успешной оплате
        messages.success(request, 'Оплата прошла успешно. Ваша подписка обновлена.')

        return redirect('additionally/payment_success')
    else:
        return redirect('index_page')

def payment_success(request):
    return render(request, 'payment_success.html')