from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Message
from .forms import MessageForm

@login_required
def message_list(request):
    messages_received = Message.objects.filter(receiver=request.user)
    messages_sent = Message.objects.filter(sender=request.user)
    return render(request, 'messenger/message_list.html', {
        'messages_received': messages_received,
        'messages_sent': messages_sent,
    })

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('message_list')
    else:
        form = MessageForm()
    return render(request, 'messenger/send_message.html', {'form': form})
