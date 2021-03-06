# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-17 20:42
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0002_auto_20160912_2138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='auth_token',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='agent',
            name='auth_token_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='server',
            name='type',
            field=models.IntegerField(choices=[(0, 'Unregistered'), (1, 'Default'), (2, 'Map')], default=0),
        ),
        migrations.AlterField(
            model_name='server',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='ServerType',
        ),
    ]
