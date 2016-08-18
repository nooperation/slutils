from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.views import generic
from .models import Sound
from random import randint
import json


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
    def post(self, request):
        num_imported = 0
        try:
            json_data = json.loads(request.body.decode("utf-8"))
            for sound in json_data['sounds']:
                if Sound.objects.filter(uuid=sound['uuid']).count() == 0:
                    new_sound = Sound(uuid=sound['uuid'], duration=sound['duration'], created_on=sound['created_on'])
                    new_sound.full_clean()
                    new_sound.save()
                    num_imported += 1
        except IntegrityError:
            raise Http404("Integrity Error")
        except:
            raise Http404("Failed to import sounds")

        return JsonResponse({'num_imported': num_imported})
