from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from . import views

app_name = 'server'

pattern_private_token = '(?P<private_token>[a-f0-9]{32})'
pattern_public_token = '(?P<public_token>[a-f0-9]{32})'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^update/$', views.UpdateView.as_view(), name='update'),
    url(r'^{}/confirm/$'.format(pattern_private_token), views.ConfirmView.as_view(), name='confirm'),
    url(r'^{}/set_enabled/(?P<enabled>True|False)/$'.format(pattern_public_token), views.SetEnabledView.as_view(), name='set_enabled'),
    url(r'^{}/regenerate_tokens/(?P<token_type>public|auth|both)/$'.format(pattern_public_token), views.RegenerateTokensView.as_view(), name='regenerate_tokens'),
]
