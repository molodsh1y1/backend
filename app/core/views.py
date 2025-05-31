import re

from django.urls import re_path
from django.views.static import serve
from django.http import JsonResponse
from django.db.migrations.recorder import MigrationRecorder


async def start(request):
    migration = await MigrationRecorder.Migration.objects.order_by('-id').afirst()
    return JsonResponse({'some_id': migration.id})


async def error(request):
    a = 1 / 0
    return JsonResponse({})


def static(prefix, view=serve, **kwargs):
    return re_path(
        r"^%s(?P<path>.*)$" % re.escape(prefix.lstrip("/")), view, kwargs=kwargs
    )
