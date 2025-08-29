from django.contrib import admin
from django.urls import path, include
from tasks import views   # ✅ import home view from tasks app

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),   # Home page
    path("tasks/", include("tasks.urls")),  # All task routes
]
