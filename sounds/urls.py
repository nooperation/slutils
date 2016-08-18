from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from . import views

app_name = 'sounds'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^json/import/$', csrf_exempt(views.ImportJsonView.as_view()), name='import_json'),
    url(r'^json/random/$', views.RandomJsonView.as_view(), name='random_json'),
    url(r'^json/all/$', views.AllJsonView.as_view(), name='all_json'),
]
