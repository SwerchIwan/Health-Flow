from django.shortcuts import render, HttpResponse


def sub_page(request):
    return HttpResponse('Страница подписок')