from django.urls import include, path

urlpatterns = [
    path("", include("projets.urls")),
]
