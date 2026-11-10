from django.shortcuts import render

from profile_user.models import Specialist


def index_page(request):
    return render(request, 'index.html', {
        'specialists_count': Specialist.objects.filter(is_published=True).count(),
    })

def window_page(request):
    return render(request, 'window.html')
