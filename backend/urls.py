from django.contrib import admin
from django.urls import path, include
from backend.views import index


urlpatterns = [
    path('', index),
    path("admin/", admin.site.urls),
    path("api/", include("simplyshop.urls")),
]
