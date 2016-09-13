from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

# Create your models here.


class ServerType(models.Model):
    name = models.CharField(max_length=64, unique=True)


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
    auth_token = models.CharField(max_length=64, null=True, blank=True)
    auth_token_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('uuid', 'shard')


class Server(models.Model):
    uuid = models.CharField(max_length=36, unique=True, validators=[
        RegexValidator(
            regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            message='Invalid UUID',
            code='invalid_uuid'
        ),
    ])
    type = models.ForeignKey(ServerType, on_delete=models.DO_NOTHING)
    shard = models.ForeignKey(Shard, on_delete=models.DO_NOTHING)
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING)
    owner = models.ForeignKey(Agent, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    address = models.URLField()
    auth_token = models.CharField(max_length=64, unique=True)
    public_token = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    position_x = models.FloatField()
    position_y = models.FloatField()
    position_z = models.FloatField()
    enabled = models.BooleanField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
