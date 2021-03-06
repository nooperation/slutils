from __future__ import unicode_literals

from django.db import models
from django.core.validators import RegexValidator


# Create your models here.
class Sound(models.Model):
    def __str__(self):
        return self.uuid

    # Note: Sound UUIDs lack variant information
    uuid = models.CharField(max_length=36, unique=True, validators=[
        RegexValidator(
            regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            message='Invalid UUID',
            code='invalid_uuid'
        ),
    ])
    duration = models.FloatField()
    created_on = models.DateTimeField()
