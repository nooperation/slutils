from django.contrib import admin
from server.models import *

# Register your models here.
admin.site.register(Server)
admin.site.register(Shard)
admin.site.register(Region)
admin.site.register(Agent)
