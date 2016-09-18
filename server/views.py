from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import generic
from .models import *
import requests
from django.contrib.auth.mixins import LoginRequiredMixin

class IndexView(generic.ListView):
    def get_queryset(self):
        return Server.objects.all()[:100]


class RegisterView(generic.View):
    def post(self, request):
        shard_name = request.POST.get('shard')
        region_name = request.POST.get('region')
        owner_name = request.POST.get('owner_name')
        owner_key = request.POST.get('owner_key')
        server_key = request.POST.get('object_key')
        address = request.POST.get('address')
        server_name = request.POST.get('object_name')
        position_x = request.POST.get('x')
        position_y = request.POST.get('y')
        position_z = request.POST.get('z')

        if not all(item is not None for item in [shard_name, region_name, owner_name, owner_key, server_key, address, server_name, position_x, position_y, position_z]):
            return JsonResponse({'Error': 'One or more missing arguments'})

        shard, created = Shard.objects.get_or_create(name=shard_name)
        region, created = Region.objects.get_or_create(shard=shard, name=region_name)
        owner, created = Agent.objects.get_or_create(shard=shard, name=owner_name, uuid=owner_key)
        auth_token = Server.generate_auth_token()
        public_token = Server.generate_public_token()

        if auth_token is None or public_token is None:
            return JsonResponse({'Error': 'Failed to generate auth tokens'})

        try:
            Server.objects.create(
                uuid=server_key,
                type=Server.TYPE_UNREGISTERED,
                shard=shard,
                region=region,
                owner=owner,
                user=None,
                address=address,
                auth_token=auth_token,
                public_token=public_token,
                name=server_name,
                position_x=position_x,
                position_y=position_y,
                position_z=position_z,
                enabled=False
            )
        except Exception:
            return JsonResponse({'Error': 'Failed to create server'})

        return JsonResponse({'Success': auth_token})


class UpdateView(generic.View):
    def post(self, request):
        auth_token = request.POST.get('auth_token')
        address = request.POST.get('address')

        if not all(item is not None for item in [auth_token, address]):
            return JsonResponse({'Error': 'One or more missing arguments'})

        existing_server = Server.objects.filter(auth_token=auth_token).first()
        if existing_server is None:
            return JsonResponse({'Error': 'No such server'})

        existing_server.address = address
        existing_server.save()

        return JsonResponse({'Success': 'OK'})


class ConfirmView(LoginRequiredMixin, generic.View):
    def get(self, request):
        auth_token = request.GET.get('auth_token')

        if not all(item is not None for item in [auth_token]):
            return render(request, 'server/confirm.html', {'error': 'One or more missing arguments'})

        if request.user.is_authenticated():
            existing_server = Server.objects.filter(auth_token=auth_token).first()
            if existing_server is None:
                return render(request, 'server/confirm.html', {'error': 'Auth token does not belong to any unregistered servers.'})
            elif existing_server.user is not None:
                return render(request, 'server/confirm.html', {'error': 'Server already registered.'})
            else:
                # Can we actually read from the server...
                server_request = requests.get(existing_server.address)
                status = server_request.status_code
                if status != 200 or server_request.text != 'OK.':
                    return render(request, 'server/confirm.html', {'error': 'Unable to contact server.'})

                existing_server.type = Server.TYPE_DEFAULT
                existing_server.regenerate_auth_token()
                existing_server.user = request.user
                existing_server.save()
                return render(request, 'server/confirm.html', {'success': 'You have successfully registered this server.'})
        else:
            return render(request, 'server/confirm.html', {'error': 'Not logged in.'})
