from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse

def home(request):
    return HttpResponse("API funcionando. Usa /api/resources/ o /api/reservations/")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.reservations.urls")),
    path("", home),
]