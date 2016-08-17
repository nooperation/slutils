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

        try:
            min_duration = int(request.GET.get('min_duration'))
        except:
            min_duration = None
        try:
            max_duration = int(request.GET.get('max_duration'))
        except:
            max_duration = None

        has_min_duration = isinstance(min_duration, int)
        has_max_duration = isinstance(max_duration, int)

        try:
            if has_min_duration and has_max_duration:
                sounds = Sound.objects.filter(duration__lte=max_duration).filter(duration__gte=min_duration)
            elif has_min_duration:
                sounds = Sound.objects.filter(duration__gte=min_duration)
            elif has_max_duration:
                sounds = Sound.objects.filter(duration__lte=max_duration)
            else:
                sounds = Sound.objects.all()
        except:
            raise Http404("Invalid parameters")

        num_sounds = len(sounds)

        if num_sounds == 0:
            raise Http404("No sounds available")

        random_index = randint(0, num_sounds - 1)
        random_sound = sounds[random_index]

        return JsonResponse({'uuid': random_sound.uuid, 'duration': random_sound.duration})


class AllJsonView(generic.View):
    def get(self, request):
        sounds = Sound.objects.all()
        sounds_json = []
        for sound in sounds:
            sounds_json.append({'uuid': sound.uuid, 'duration': sound.duration})
        return JsonResponse({"sounds": sounds_json})


class ImportJsonView(generic.View):
    def get(self, request):
        return HttpResponse("Update")
