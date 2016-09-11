from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.views import generic
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Server
from random import randint
import json
import gzip

class IndexView(generic.ListView):
    def get_queryset(self):
        return Server.objects.all()[:100]
