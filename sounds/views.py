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


def random(request, request_type):
    sounds = Sound.objects.all()
    num_sounds = len(sounds)
    if num_sounds == 0:
        raise Http404("No sounds")
    random_index = randint(0, num_sounds - 1)
    random_sound = sounds[random_index]

    if request_type is None or request_type == 'html':
        return render(request, 'sounds/random.html', context={
            'sound': random_sound
        })
    elif request_type == 'json':
        return JsonResponse({'uuid': random_sound.uuid, 'duration': random_sound.duration})
    else:
        raise Http404("Invalid format")


def update(request):
    return HttpResponse("Update")
