from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path

from portfolio import views

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    # serves uploads with Range support so videos can be seeked while developing
    urlpatterns += [re_path(r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"), views.media_serve)]
