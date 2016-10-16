from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import generic
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from .models import *
import requests
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

JSON_RESULT_SUCCESS = 'success'
JSON_RESULT_ERROR = 'error'
JSON_TAG_RESULT = 'result'
JSON_TAG_MESSAGE = 'payload'


def json_success(message):
    return {JSON_TAG_RESULT: JSON_RESULT_SUCCESS, JSON_TAG_MESSAGE: message}


def json_error(message):
    return {JSON_TAG_RESULT: JSON_RESULT_ERROR, JSON_TAG_MESSAGE: message}


def get_lsl_headers(request):
    position = request.META['HTTP_X_SECONDLIFE_LOCAL_POSITION'][1:-1].split(', ')
    region = request.META['HTTP_X_SECONDLIFE_REGION'].split(' ')
    region_name = region[0]

    return {
        'owner_name': request.META['HTTP_X_SECONDLIFE_OWNER_NAME'],
        'object_name': request.META['HTTP_X_SECONDLIFE_OBJECT_NAME'],
        'object_key': request.META['HTTP_X_SECONDLIFE_OBJECT_KEY'],
        'owner_key': request.META['HTTP_X_SECONDLIFE_OWNER_KEY'],
        'shard': request.META['HTTP_X_SECONDLIFE_SHARD'],
        'region': region_name,
        'position_x': position[0],
        'position_y': position[1],
        'position_z': position[2],
    }


class IndexView(LoginRequiredMixin, generic.View):
    def get(self, request):
        return render(request, 'server/server_list.html', {'servers_list': Server.objects.filter(user=request.user)})


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generic.View):
    def post(self, request):
        address = request.POST.get('address')

        try:
            headers = get_lsl_headers(request)
        except:
            return JsonResponse(json_error('Missing or incorrect SL headers'))

        if not all(item is not None for item in [address]):
            return JsonResponse(json_error('One or more missing arguments'))
        if not all(value is not None for key, value in headers.items()):
            return JsonResponse(json_error('One or more missing META arguments'))

        shard, created = Shard.objects.get_or_create(name=headers['shard'])
        region, created = Region.objects.get_or_create(shard=shard, name=headers['region'])
        owner, created = Agent.objects.get_or_create(shard=shard, name=headers['owner_name'], uuid=headers['owner_key'])
        private_token = Server.generate_private_token()
        public_token = Server.generate_public_token()

        if private_token is None or public_token is None:
            return JsonResponse(json_error('Failed to generate auth tokens'))

        try:
            existing_server = Server.objects.filter(object_key=headers['object_key']).first()
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
                    existing_server.object_name = headers['object_name']
                    existing_server.position_x = headers['position_x']
                    existing_server.position_y = headers['position_y']
                    existing_server.position_z = headers['position_z']
                    existing_server.enabled = False
                    existing_server.save()
            else:
                Server.objects.create(
                    object_key=headers['object_key'],
                    object_name=headers['object_name'],
                    type=Server.TYPE_UNREGISTERED,
                    shard=shard,
                    region=region,
                    owner=owner,
                    user=None,
                    address=address,
                    private_token=private_token,
                    public_token=public_token,
                    position_x=headers['position_x'],
                    position_y=headers['position_y'],
                    position_z=headers['position_z'],
                    enabled=False
                )
        except Exception as ex:
            logging.exception("Failed to create server")
            return JsonResponse(json_error('Failed to create server'))

        return JsonResponse(json_success(private_token))


@method_decorator(csrf_exempt, name='dispatch')
class UpdateView(generic.View):
    def post(self, request):
        private_token = request.POST.get('private_token')
        address = request.POST.get('address')

        try:
            headers = get_lsl_headers(request)
        except:
            return JsonResponse(json_error('Missing or incorrect SL headers'))

        if not all(item is not None for item in [private_token, address]):
            return JsonResponse(json_error('One or more missing arguments'))
        if not all(value is not None for key, value in headers.items()):
            return JsonResponse(json_error('One or more missing META arguments'))

        if Server.objects.filter(object_key=headers['object_key']).count() == 0:
            return JsonResponse(json_error('Object not registered.'))

        try:
            server = Server.objects.get(private_token=private_token, object_key=headers['object_key'])
        except Server.DoesNotExist:
            return JsonResponse(json_error('Server does not exist'))
        except Server.MultipleObjectsReturned:
            logging.exception("Multiple objects returned")
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server.type == Server.TYPE_UNREGISTERED:
            return JsonResponse(json_error('Server not registered'))

        server.object_name = headers['object_name']
        server.address = address
        server.position_x = headers['position_x']
        server.position_y = headers['position_y']
        server.position_z = headers['position_z']
        server.save()

        return JsonResponse(json_success('OK'))


class ConfirmView(LoginRequiredMixin, generic.View):
    def get(self, request, private_token):

        try:
            server = Server.objects.get(private_token=private_token)
        except Server.DoesNotExist:
            return render(request, 'server/confirm.html', json_error('Auth token does not belong to any unregistered servers.'))
        except Server.MultipleObjectsReturned:
            logging.exception("Multiple objects returned")
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server.type != Server.TYPE_UNREGISTERED:
            return render(request, 'server/confirm.html', json_error('Server already registered'))
        elif server.user is not None:
            return render(request, 'server/confirm.html', json_error('Server already registered.'))
        else:
            try:
                # Can we actually read from the server...
                server_request = requests.get(server.address + "?path=/Base/InitComplete", verify=False)
                status = server_request.status_code
                if status != 200 or server_request.text != 'OK.':
                    return render(request, 'server/confirm.html', json_error('Unable to contact server.'))
            except:
                logging.exception("Failed to confirm view")
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
            logging.exception("Multiple objects returned")
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
            logging.exception("Multiple objects returned")
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
            logging.exception("Multiple objects returned")
            return render(request, 'server/view.html', json_error('Multiple servers contain the same token'))

        return render(request, 'server/view.html', json_success(server))


class StatusView(generic.View):
    def get(self, request, public_token):
        try:
            server = Server.objects.get(public_token=public_token)
        except Server.DoesNotExist:
            return JsonResponse(json_error('Server does not exist'))
        except Server.MultipleObjectsReturned:
            logging.exception("Multiple objects returned")
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server.type == Server.TYPE_UNREGISTERED:
            return JsonResponse(json_error('Server not registered'))

        try:
            server_request = requests.get(server.address + "?path=/Base/Status", verify=False)
            status = server_request.status_code
            if status != 200 or server_request.text != 'OK.':
                return JsonResponse(json_error('Server offline'))
        except:
            logging.exception("Failed to connect to server for StatusView")
            return JsonResponse(json_error('Unable to contact server'))

        return JsonResponse(json_success('Server online'))


class CreateProxyView(LoginRequiredMixin, generic.View):
    def get(self, request):
        return HttpResponse('Invalid method', status=405)

    def post(self, request):
        public_token = request.POST.get('public_token')
        proxy_name = request.POST.get('proxy_name')
        forced_path = request.POST.get('forced_path')
        allow_user_query = request.POST.get('allow_user_query')

        if not all(item is not None for item in [public_token, proxy_name]):
            return JsonResponse(json_error('One or more missing arguments'))

        if allow_user_query is not None:
            allow_user_query = True
        else:
            allow_user_query = False

        try:
            server = Server.objects.get(user=request.user, public_token=public_token)
        except Server.DoesNotExist:
            return JsonResponse(json_error('Server does not exist'))
        except Server.MultipleObjectsReturned:
            logging.exception("Multiple objects returned")
            return JsonResponse(json_error('Multiple servers contain the same token'))

        if server.type == Server.TYPE_UNREGISTERED:
            return JsonResponse(json_error('Server not registered'))

        try:
            server_proxy = ServerProxy.objects.create(proxy_name=proxy_name, server=server, forced_path=forced_path, allow_user_query=allow_user_query)
        except ServerProxy.DoesNotExist:
            return JsonResponse(json_error('Server does not exist'))
        except ServerProxy.MultipleObjectsReturned:
            logging.exception("Multiple objects returned")
            return JsonResponse(json_error('Multiple servers contain the same token'))
        except IntegrityError:
            return JsonResponse(json_error('Proxy name already exists'))
        except Exception as ex:
            logging.exception("CreateProxyView error: " + str(ex))
            return JsonResponse(json_error('Error'))

        return JsonResponse(json_success(server_proxy.proxy_name + (server_proxy.forced_path or "")))


class ProxyView(generic.View):
    def get(self, request, proxy_name, user_query):
        try:
            server_proxy = ServerProxy.objects.get(proxy_name=proxy_name)
        except ServerProxy.DoesNotExist:
            return JsonResponse(json_error('Unknown proxy'))
        except ServerProxy.MultipleObjectsReturned:
            logging.exception("Multiple proxies with the same name")
            return JsonResponse(json_error('Multiple proxies with the same name'))

        try:
            full_path = server_proxy.server.address
            if server_proxy.forced_path is not None:
                full_path = full_path + server_proxy.forced_path
            if server_proxy.allow_user_query:
                full_path = full_path + user_query

            logging.debug("Requesting: " + full_path)
            server_request = requests.get(full_path, verify=False)
            return HttpResponse(server_request.text, status=server_request.status_code, content_type=server_request.headers['Content-Type'])
        except:
            logging.exception("Failed to connect to server for ProxyView")
            return JsonResponse(json_error('Unable to contact server'))


class DebugConfirmView(generic.View):
    def get(self, request, server_name):
        # Note to self: Never remove the 'request' parameter or you'll end up with "get() got multiple values for argument 'server_name'"
        return HttpResponse('OK.')


class DebugProxyView(generic.View):
    def get(self, request, server_name, user_query):
        return JsonResponse({'path': request.get_full_path()})
