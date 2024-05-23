# diary/views.py

from django.shortcuts import render, redirect
from .models import Entry
from .forms import EntryForm

def entry_list(request):
    entries = Entry.objects.all()
    return render(request, 'diary/entry_list.html', {'entries': entries})

def entry_create(request):
    if request.method == 'POST':
        form = EntryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('entry_list')
    else:
        form = EntryForm()
    return render(request, 'diary/entry_form.html', {'form': form})
