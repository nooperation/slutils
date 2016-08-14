from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from .models import Sound
# Create your views here.


class IndexView(generic.ListView):
    def get_queryset(self):
        return Sound.objects.all()


def update(request):
    return HttpResponse("Update")
