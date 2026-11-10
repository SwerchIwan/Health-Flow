from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from users.notifications import send_email
from .models import Payment, Plan

DEFAULT_PLANS = [
    {
        'code': 'STANDART',
        'name': 'STANDART',
        'price': Decimal('29'),
        'duration_days': 30,
        'sort_order': 1,
        'features': [
            'Общение со специалистами базового уровня',
            'Ответ на сообщение в течение дня',
            'Быстрое определение курса лечения',
        ],
    },
    {
        'code': 'PRO',
        'name': 'PRO',
        'price': Decimal('49'),
        'duration_days': 30,
        'sort_order': 2,
        'features': [
            'Общение со специалистами высшего уровня',
            'Моментальная реакция на сообщения',
            'Быстрое определение курса лечения',
        ],
    },
    {
        'code': 'PLUS',
        'name': 'PLUS',
        'price': Decimal('79'),
        'duration_days': 30,
        'sort_order': 3,
        'features': [
            'Общение со специалистами продвинутого уровня',
            'Приоритетная очередь к специалистам',
            'Быстрое определение курса лечения',
        ],
    },
]


def get_plans():
    plans = list(Plan.objects.filter(is_active=True))
    if plans:
        return plans
    for data in DEFAULT_PLANS:
        Plan.objects.update_or_create(code=data['code'], defaults=data)
    return list(Plan.objects.filter(is_active=True))


def luhn_valid(number):
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) != 16:
        return False
    checksum = 0
    for index, digit in enumerate(reversed(digits)):
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def validate_card(card_number, card_name, validity, cvv):
    number = ''.join(ch for ch in (card_number or '') if ch.isdigit())
    if not luhn_valid(number):
        return 'Проверьте номер карты.'
    if not (card_name or '').strip():
        return 'Укажите имя держателя карты.'
    try:
        month, year = [int(part) for part in (validity or '').split('/')]
    except ValueError:
        return 'Укажите срок действия в формате ММ/ГГ.'
    if not 1 <= month <= 12:
        return 'Неверный месяц срока действия.'
    today = date.today()
    if (2000 + year, month) < (today.year, today.month):
        return 'Срок действия карты истёк.'
    if not (cvv or '').isdigit() or len(cvv) != 3:
        return 'Проверьте CVV.'
    return None


def user_subscription_context(user):
    active = user.subscription_is_active()
    days_left = None
    if active and user.subscription_until:
        days_left = max((user.subscription_until - timezone.now()).days, 1)
    return {
        'subscription': user.subscription if active else 'FREE',
        'subscription_until': user.subscription_until if active else None,
        'subscription_days_left': days_left,
        'current_active': active,
    }


@login_required
def pay_page(request):
    plans = get_plans()
    requested = (request.GET.get('subscription') or request.GET.get('plan') or '').upper()
    plan = next((p for p in plans if p.code == requested), None)
    if requested and plan is None:
        messages.error(request, 'Такого тарифа нет. Выберите один из доступных.')
        return redirect('pay')
    if plan is None:
        plan = next((p for p in plans if p.code == 'STANDART'), plans[0] if plans else None)
    if plan is None:
        return render(request, 'additionally/pay_page.html', {'plans': [], 'plan': None})

    context = {
        'plan': plan,
        'plans': plans,
        'card_mask': '',
        'validity': '',
        'errors': [],
    }
    context.update(user_subscription_context(request.user))
    return render(request, 'additionally/pay_page.html', context)


@login_required
def process_payment(request):
    if request.method != 'POST':
        return redirect('pay')

    plans = get_plans()
    plan = next((p for p in plans if p.code == (request.POST.get('subscription') or '').upper()), None)
    if plan is None:
        messages.error(request, 'Тариф не найден.')
        return redirect('pay')

    card_number = request.POST.get('card_number', '')
    card_name = request.POST.get('card_name', '')
    validity = request.POST.get('validity', '')
    cvv = request.POST.get('cvv', '')

    error = validate_card(card_number, card_name, validity, cvv)
    user = request.user
    context = {
        'plan': plan,
        'plans': plans,
        'card_mask': card_number,
        'validity': validity,
        'card_name': card_name,
        'errors': [error] if error else [],
    }
    context.update(user_subscription_context(user))
    if error:
        return render(request, 'additionally/pay_page.html', context)

    digits = ''.join(ch for ch in card_number if ch.isdigit())
    Payment.objects.create(
        user=user,
        plan=plan,
        amount=plan.price,
        duration_days=plan.duration_days,
        card_mask=f'**** {digits[-4:]}',
    )
    user.subscription = plan.code
    user.subscription_until = timezone.now() + timedelta(days=plan.duration_days)
    user.save(update_fields=['subscription', 'subscription_until'])

    if user.email:
        send_email(
            user.email,
            f'Подписка {plan.name} активирована — Health Flow AI',
            'email_subscription.html',
            {
                'plan': plan,
                'until': user.subscription_until,
                'amount': plan.price,
                'card_mask': f'**** {digits[-4:]}',
            },
            text_body=f'Подписка {plan.name} активирована до {user.subscription_until:%d.%m.%Y}. '
                      f'Списано {plan.price} Br, карта **** {digits[-4:]}.',
        )

    return redirect('payment_success')


@login_required
def payment_success(request):
    latest = Payment.objects.filter(user=request.user).select_related('plan').first()
    context = {'payment': latest}
    context.update(user_subscription_context(request.user))
    return render(request, 'additionally/payment_success.html', context)


@login_required
def cancel_subscription(request):
    if request.method != 'POST':
        return redirect('profile_page')
    user = request.user
    Payment.objects.filter(user=user, status='succeeded').update(status='canceled')
    user.subscription = 'FREE'
    user.subscription_until = None
    user.save(update_fields=['subscription', 'subscription_until'])
    messages.success(request, 'Подписка отменена. Действие тарифа прекращено сразу.')
    return redirect('profile_page')
