from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    return HttpResponse("Sound index");

def update(request):
    return HttpResponse("Update")
