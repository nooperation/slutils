# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-13 01:38
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='auth_token',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='agent',
            name='auth_token_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='auth_token',
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='public_token',
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='uuid',
            field=models.CharField(max_length=36, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_uuid', message='Invalid UUID', regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')]),
        ),
        migrations.AlterUniqueTogether(
            name='agent',
            unique_together=set([('uuid', 'shard')]),
        ),
        migrations.AlterUniqueTogether(
            name='region',
            unique_together=set([('name', 'shard')]),
        ),
    ]
