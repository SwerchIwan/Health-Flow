from django.shortcuts import render, HttpResponse


def support_page(request):
    return HttpResponse('Страница поддержки')