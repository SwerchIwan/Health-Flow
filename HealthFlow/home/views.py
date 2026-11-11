import hmac
import io
import os
from hashlib import sha256

from django.conf import settings
from django.core.management import call_command
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from profile_user.models import Specialist


def index_page(request):
    return render(request, 'index.html', {
        'specialists_count': Specialist.objects.filter(is_published=True).count(),
    })

def window_page(request):
    return render(request, 'window.html')


def seed_token():
    key = f'healthflow-seed:{settings.SECRET_KEY}'.encode()
    return hmac.new(key, b'demo-data', sha256).hexdigest()[:20]


@require_GET
def seed_demo_data(request, token):
    # На free-плане Render нет Shell, а внешний Postgres отсекается сетью:
    # демо-данные засеваются через URL с токеном, выведенным из SECRET_KEY.
    if not hmac.compare_digest(token, seed_token()):
        raise Http404
    images_dir = os.path.join(settings.BASE_DIR.parent, 'vibe_images')
    out = io.StringIO()
    call_command('seed_specialists', '--images-dir', images_dir, stdout=out)
    call_command('seed_patients', stdout=out)
    return JsonResponse({
        'specialists': Specialist.objects.filter(is_published=True).count(),
        'log': out.getvalue().strip().splitlines()[-5:],
    })
