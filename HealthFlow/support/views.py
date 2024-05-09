from django.shortcuts import render, HttpResponse
from support.AI import new_request


# def support_page(request):
#     if request.method == "POST":
#         msg = request.POST['msg']
#         response_ai = new_request(msg)
#         print(response_ai)
#         return render(request, 'supports.html', {'msg': response_ai})
#     return render(request, 'supports.html', {'msg': ''})

from django.http import JsonResponse

def support_page(request):
    if request.method == "POST":
        msg = request.POST['msg']
        response_ai = new_request(msg)
        return JsonResponse({'msg': response_ai})
    return render(request, 'supports.html', {'msg': ''})