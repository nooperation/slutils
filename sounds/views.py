from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse
from django.views import generic
from .models import Sound
from random import randint
from django.shortcuts import render
# Create your views here.


class IndexView(generic.ListView):
    def get_queryset(self):
        return Sound.objects.all()


class RandomView(generic.View):
    def get(self, request):
        sounds = Sound.objects.all()
        num_sounds = len(sounds)
        if num_sounds == 0:
            raise Http404("No sounds available")

        random_index = randint(0, num_sounds - 1)
        random_sound = sounds[random_index]

        return JsonResponse({'uuid': random_sound.uuid, 'duration': random_sound.duration})


class AllView(generic.View):
    def get(self, request):
        raise Http404("Not implemented")


class UpdateView(generic.View):
    def get(self, request):
        return HttpResponse("Update")
