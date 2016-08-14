from __future__ import unicode_literals

from django.db import models
from django.core.validators import RegexValidator

# Create your models here.
class Sound(models.Model):
    uuid = models.CharField( max_length=36, unique=True, validators=[RegexValidator(
        regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', message='Invalid UUID', code = 'invalid_uuid')
    ])
    duration = models.PositiveIntegerField()
    created_on = models.DateTimeField(auto_now=True)
