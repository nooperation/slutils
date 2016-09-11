from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from . import views

app_name = 'server'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
]
