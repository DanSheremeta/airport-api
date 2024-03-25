from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/airport/", include("airport.urls", namespace="airport")),
    path("api/v1/user/", include("user.urls", namespace="user")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
