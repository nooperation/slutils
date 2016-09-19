import binascii
import os

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

# Create your models here.


class Shard(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Region(models.Model):
    name = models.CharField(max_length=255)
    shard = models.ForeignKey(Shard, on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = ('name', 'shard')


class Agent(models.Model):
    name = models.CharField(max_length=64)
    uuid = models.CharField(max_length=36, validators=[
        RegexValidator(
            regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            message='Invalid UUID',
            code='invalid_uuid'
        ),
    ])
    shard = models.ForeignKey(Shard, on_delete=models.DO_NOTHING)
    private_token = models.CharField(max_length=64, null=True, blank=True)
    private_token_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('uuid', 'shard')


class Server(models.Model):
    TYPE_UNREGISTERED = 0
    TYPE_DEFAULT = 1
    TYPE_MAP = 2
    SERVER_TYPE_CHOICES = (
        (TYPE_UNREGISTERED, 'Unregistered'),
        (TYPE_DEFAULT, 'Default'),
        (TYPE_MAP, 'Map'),
    )

    @staticmethod
    def generate_private_token():
        token = None
        for i in range(0, 10):
            token = binascii.hexlify(os.urandom(16)).decode('utf-8')
            if Server.objects.filter(private_token=token).count() != 0:
                token = None
            else:
                break
        return token

    @staticmethod
    def generate_public_token():
        token = None
        for i in range(0, 10):
            token = binascii.hexlify(os.urandom(16)).decode('utf-8')
            if Server.objects.filter(public_token=token).count() != 0:
                token = None
            else:
                break
        return token

    def regenerate_private_token(self):
        self.private_token = self.generate_private_token()

    def regenerate_public_token(self):
        self.public_token = self.generate_public_token()

    uuid = models.CharField(max_length=36, unique=True, validators=[
        RegexValidator(
            regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            message='Invalid UUID',
            code='invalid_uuid'
        ),
    ])
    type = models.IntegerField(choices=SERVER_TYPE_CHOICES, default=TYPE_UNREGISTERED)
    shard = models.ForeignKey(Shard, on_delete=models.DO_NOTHING)
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING)
    owner = models.ForeignKey(Agent, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    address = models.URLField()
    private_token = models.CharField(max_length=64, unique=True)
    public_token = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    position_x = models.FloatField()
    position_y = models.FloatField()
    position_z = models.FloatField()
    enabled = models.BooleanField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
