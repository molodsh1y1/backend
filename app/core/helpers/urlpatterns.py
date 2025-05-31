import logging

from django.urls import get_resolver, URLPattern, URLResolver
from rest_framework.viewsets import ViewSetMixin

logger=logging.getLogger(__name__)


def print_urlpatterns(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):  # Для конечных URL-адресов
            view_class = pattern.callback.view_class if hasattr(pattern.callback, 'view_class') else None
            if view_class and issubclass(view_class, ViewSetMixin):  # Проверка, является ли вьюсетом
                methods = view_class.http_method_names  # Получение поддерживаемых методов
                logger.info(f"Path: {prefix}{pattern.pattern}, Methods: {methods}, ViewSet: {view_class.__name__}")
            else:
                logger.info(f"Path: {prefix}{pattern.pattern}, View: {pattern.callback}")
        elif isinstance(pattern, URLResolver):  # Для вложенных URL-конфигураций
            print_urlpatterns(pattern.url_patterns, prefix + str(pattern.pattern))
