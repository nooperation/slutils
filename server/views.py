from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import generic
from .models import *
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class IndexView(LoginRequiredMixin, generic.View):
    def get(self, request):
        return render(request, 'server/server_list.html', {'servers_list': Server.objects.filter(user=request.user)})


@method_decorator(csrf_exempt, name='dispatch')
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
        private_token = Server.generate_private_token()
        public_token = Server.generate_public_token()

        if private_token is None or public_token is None:
            return JsonResponse({'Error': 'Failed to generate auth tokens'})

        try:
            existing_server = Server.objects.filter(uuid=server_key).first()
            if existing_server is not None:
                if existing_server.type != Server.TYPE_UNREGISTERED:
                    return JsonResponse({'Error': 'Server already registered'})
                else:
                    existing_server.regenerate_private_token()
                    existing_server.regenerate_public_token()
                    existing_server.save()
                    private_token=existing_server.private_token
            else:
                Server.objects.create(
                    uuid=server_key,
                    type=Server.TYPE_UNREGISTERED,
                    shard=shard,
                    region=region,
                    owner=owner,
                    user=None,
                    address=address,
                    private_token=private_token,
                    public_token=public_token,
                    name=server_name,
                    position_x=position_x,
                    position_y=position_y,
                    position_z=position_z,
                    enabled=False
                )
        except Exception:
            return JsonResponse({'Error': 'Failed to create server'})

        return JsonResponse({'Success': private_token})


@method_decorator(csrf_exempt, name='dispatch')
class UpdateView(generic.View):
    def post(self, request):
        private_token = request.POST.get('private_token')
        address = request.POST.get('address')

        if not all(item is not None for item in [private_token, address]):
            return JsonResponse({'Error': 'One or more missing arguments'})

        existing_server = Server.objects.filter(private_token=private_token).first()
        if existing_server is None:
            return JsonResponse({'Error': 'No such server'})

        existing_server.address = address
        existing_server.save()

        return JsonResponse({'Success': 'OK'})


class ConfirmView(LoginRequiredMixin, generic.View):
    def get(self, request, private_token):
        existing_server = Server.objects.filter(private_token=private_token).first()
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
            existing_server.regenerate_private_token()
            existing_server.user = request.user
            existing_server.save()
            return render(request, 'server/confirm.html', {'success': 'You have successfully registered this server.'})


class SetEnabledView(LoginRequiredMixin, generic.View):
    def get(self, request, public_token, enabled):
        server = Server.objects.filter(user=request.user).filter(public_token=public_token).first()
        if server is None:
            return JsonResponse({'error': 'Invalid server'})

        server.enabled = enabled
        server.save()
        return JsonResponse({'success': 'Server enabled set to {}.'.format(enabled)})


class RegenerateTokensView(LoginRequiredMixin, generic.View):
    def get(self, request, public_token, token_type):
        server = Server.objects.filter(user=request.user).filter(public_token=public_token).first()
        if server is None:
            return JsonResponse({'error': 'Invalid server'})

        if token_type == 'public':
            server.regenerate_public_token()
        elif token_type == 'auth':
            server.regenerate_private_token()
        elif token_type == 'both':
            server.regenerate_private_token()
            server.regenerate_public_token()
        else:
            return JsonResponse({'error': 'Invalid token type specified'})

        server.save()
        return JsonResponse({'success': 'Successfully regenerated {} token(s)'.format(token_type)})


class ServerView(generic.View):
    def get(self, request, public_token):
        server = Server.objects.filter(public_token=public_token)
        if server is None:
            return render(request, 'server/view.html', {'error': 'Invalid server specified'})
        return render(request, 'server/view.html', {'server': server})
