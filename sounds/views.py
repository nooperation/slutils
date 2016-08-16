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


class RandomJsonView(generic.View):
    def get(self, request):

        min_duration = request.GET.get('min_duration')
        max_duration = request.GET.get('max_duration')

        if min_duration is not None and max_duration is not None:
            sounds = Sound.objects.filter(duration__lte=max_duration).filter(duration__gte=min_duration)
        elif min_duration is not None:
            sounds = Sound.objects.filter(duration__gte=min_duration)
        elif max_duration is not None:
            sounds = Sound.objects.filter(duration__lte=max_duration)
        else:
            sounds = Sound.objects.all()

        num_sounds = len(sounds)

        if num_sounds == 0:
            raise Http404("No sounds available")

        random_index = randint(0, num_sounds - 1)
        random_sound = sounds[random_index]

        return JsonResponse({'uuid': random_sound.uuid, 'duration': random_sound.duration})


class AllJsonView(generic.View):
    def get(self, request):
        raise Http404("Not implemented")


class ImportJsonView(generic.View):
    def get(self, request):
        return HttpResponse("Update")
