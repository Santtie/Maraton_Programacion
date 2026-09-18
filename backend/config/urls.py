"""URL configuration for config project (ProyectadurIA backend)."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/chat/", include("apps.chat.urls")),
    path("api/documents/", include("apps.documents.urls")),
]
