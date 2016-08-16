from django.conf.urls import url
from . import views

app_name = 'sounds'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^json/import/$', views.ImportJsonView.as_view(), name='import_json'),
    url(r'^json/random/$', views.RandomJsonView.as_view(), name='random_json'),
    url(r'^json/all/$', views.AllJsonView.as_view(), name='all_json'),
]
