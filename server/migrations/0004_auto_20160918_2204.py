# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-19 02:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0003_auto_20160917_1642'),
    ]

    operations = [
        migrations.RenameField(
            model_name='agent',
            old_name='auth_token',
            new_name='private_token',
        ),
        migrations.RenameField(
            model_name='agent',
            old_name='auth_token_date',
            new_name='private_token_date',
        ),
        migrations.RenameField(
            model_name='server',
            old_name='auth_token',
            new_name='private_token',
        ),
    ]