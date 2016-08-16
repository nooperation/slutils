from django.conf.urls import url
from . import views

app_name = 'sounds'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^json/update/$', views.UpdateView.as_view(), name='update_json'),
    url(r'^json/random/$', views.RandomView.as_view(), name='random_json'),
    url(r'^json/all/$', views.AllView.as_view(), name='all_json'),
]
