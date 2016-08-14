from django.conf.urls import url
from . import views

app_name = 'sounds'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^update/$', views.update, name='update'),
]
