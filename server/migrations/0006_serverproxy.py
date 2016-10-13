# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-13 02:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0005_auto_20161008_2250'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServerProxy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proxy_name', models.CharField(max_length=255, unique=True)),
                ('forced_path', models.CharField(max_length=255, null=True)),
                ('allow_user_query', models.BooleanField(default=False)),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='server.Server')),
            ],
        ),
    ]
