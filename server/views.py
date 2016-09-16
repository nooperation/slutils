from django.http import Http404, JsonResponse
from django.views import generic
from .models import *
import os
import binascii


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
        server_type, created = ServerType.objects.get_or_create(name='Unassigned')
        auth_token = None
        public_token = None

        for i in range(0, 10):
            auth_token = binascii.hexlify(os.urandom(16)).decode('utf-8')
            if Server.objects.filter(auth_token=auth_token).count() != 0:
                print('auth_token already taken')
                auth_token = None
            else:
                break

        for i in range(0, 10):
            public_token = binascii.hexlify(os.urandom(16)).decode('utf-8')
            if Server.objects.filter(public_token=public_token).count() != 0:
                print('public_token already taken')
                public_token = None
            else:
                break

        if auth_token is None or public_token is None:
            return JsonResponse({'Error': 'Failed to generate auth tokens'})

        try:
            Server.objects.create(
                uuid=server_key,
                type=server_type,
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
