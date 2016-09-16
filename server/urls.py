from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from . import views

app_name = 'server'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^update/$', views.UpdateView.as_view(), name='update'),
]
