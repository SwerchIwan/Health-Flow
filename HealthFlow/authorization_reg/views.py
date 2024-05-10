from django.shortcuts import render


def auth_page(request):
    return render(request, 'additionally/base-auth.html')