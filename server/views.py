from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import generic
from .models import *
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

JSON_RESULT_SUCCESS = 'success'
JSON_RESULT_ERROR = 'error'
JSON_TAG_RESULT = 'result'
JSON_TAG_MESSAGE = 'payload'


def json_success(message):
    return {JSON_TAG_RESULT: JSON_RESULT_SUCCESS, JSON_TAG_MESSAGE: message}


def json_error(message):
    return {JSON_TAG_RESULT: JSON_RESULT_ERROR, JSON_TAG_MESSAGE: message}


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
            return JsonResponse(json_error('One or more missing arguments'))

        shard, created = Shard.objects.get_or_create(name=shard_name)
        region, created = Region.objects.get_or_create(shard=shard, name=region_name)
        owner, created = Agent.objects.get_or_create(shard=shard, name=owner_name, uuid=owner_key)
        private_token = Server.generate_private_token()
        public_token = Server.generate_public_token()

        if private_token is None or public_token is None:
            return JsonResponse(json_error('Failed to generate auth tokens'))

        try:
            existing_server = Server.objects.filter(uuid=server_key).first()
            if existing_server is not None:
                if existing_server.type != Server.TYPE_UNREGISTERED:
                    return JsonResponse(json_error('Server already registered'))
                else:
                    existing_server.type = Server.TYPE_UNREGISTERED
                    existing_server.shard = shard
                    existing_server.region = region
                    existing_server.owner = owner
                    existing_server.user = None
                    existing_server.address = address
                    existing_server.private_token = private_token
                    existing_server.public_token = public_token
                    existing_server.name = server_name
                    existing_server.position_x = position_x
                    existing_server.position_y = position_y
                    existing_server.position_z = position_z
                    existing_server.enabled = False
                    existing_server.save()
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
        except Exception as ex:
            return JsonResponse(json_error('Failed to create server'))

        return JsonResponse(json_success(private_token))


@method_decorator(csrf_exempt, name='dispatch')
class UpdateView(generic.View):
    def post(self, request):
        private_token = request.POST.get('private_token')
        address = request.POST.get('address')

        if not all(item is not None for item in [private_token, address]):
            return JsonResponse(json_error('One or more missing arguments'))

        try:
            server = Server.objects.get(private_token=private_token)
        except Server.DoesNotExist:
            return JsonResponse(json_error('Server does not exist'))
        except Server.MultipleObjectsReturned:
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server.type == Server.TYPE_UNREGISTERED:
            return JsonResponse(json_error('Server not registered'))

        server.address = address
        server.save()

        return JsonResponse(json_success('OK'))


class ConfirmView(LoginRequiredMixin, generic.View):
    def get(self, request, private_token):

        try:
            server = Server.objects.get(private_token=private_token)
        except Server.DoesNotExist:
            return render(request, 'server/confirm.html', json_error('Auth token does not belong to any unregistered servers.'))
        except Server.MultipleObjectsReturned:
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server.type != Server.TYPE_UNREGISTERED:
            return JsonResponse(json_error('Server already registered'))
        elif server.user is not None:
            return render(request, 'server/confirm.html', json_error('Server already registered.'))
        else:
            try:
                # Can we actually read from the server...
                server_request = requests.get(server.address + "?path=/Base/InitComplete")
                status = server_request.status_code
                if status != 200 or server_request.text != 'OK.':
                    return render(request, 'server/confirm.html', json_error('Unable to contact server.'))
            except:
                return render(request, 'server/confirm.html', json_error('Unable to contact server.'))

            server.type = Server.TYPE_DEFAULT
            server.user = request.user
            server.save()
            return render(request, 'server/confirm.html', json_success('You have successfully registered this server.'))


class SetEnabledView(LoginRequiredMixin, generic.View):
    def get(self, request, public_token, enabled):
        try:
            server = Server.objects.get(user=request.user, public_token=public_token)
        except Server.DoesNotExist:
            return JsonResponse(json_error('Server does not exist'))
        except Server.MultipleObjectsReturned:
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server.type == Server.TYPE_UNREGISTERED:
            return JsonResponse(json_error('Server not registered'))

        server.enabled = enabled
        server.save()
        return JsonResponse(json_success('Server enabled set to {}.'.format(enabled)))


class RegenerateTokensView(LoginRequiredMixin, generic.View):
    def get(self, request, public_token, token_type):
        try:
            server = Server.objects.get(user=request.user, public_token=public_token)
        except Server.DoesNotExist:
            return JsonResponse(json_error('Server does not exist'))
        except Server.MultipleObjectsReturned:
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server is None:
            return JsonResponse(json_error('Invalid server'))
        elif server.type == Server.TYPE_UNREGISTERED:
            return JsonResponse(json_error('Server not registered'))

        if token_type == 'public':
            server.regenerate_public_token()
        elif token_type == 'auth':
            server.regenerate_private_token()
        elif token_type == 'both':
            server.regenerate_private_token()
            server.regenerate_public_token()
        else:
            return JsonResponse(json_error('Invalid token type specified'))

        server.save()
        return JsonResponse(json_success('Successfully regenerated {} token(s)'.format(token_type)))


class ServerView(generic.View):
    def get(self, request, public_token):
        try:
            server = Server.objects.get(public_token=public_token)
        except Server.DoesNotExist:
            return render(request, 'server/view.html', json_error('Server does not exist'))
        except Server.MultipleObjectsReturned:
            return render(request, 'server/view.html', json_error('Multiple servers contain the same token'))

        return render(request, 'server/view.html', json_success(server))


class StatusView(generic.View):
    def get(self, request, public_token):
        try:
            server = Server.objects.get(public_token=public_token)
        except Server.DoesNotExist:
            return JsonResponse(json_error('Server does not exist'))
        except Server.MultipleObjectsReturned:
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server.type == Server.TYPE_UNREGISTERED:
            return JsonResponse(json_error('Server not registered'))

        try:
            server_request = requests.get(server.address + "?path=/Base/Status")
            status = server_request.status_code
            if status != 200 or server_request.text != 'OK.':
                return JsonResponse(json_error('Server offline'))
        except:
            return JsonResponse(json_error('Unable to contact server'))

        return JsonResponse(json_success('Server online'))

