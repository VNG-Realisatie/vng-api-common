from django.urls import path

from .views import CreateJWTSecretView

urlpatterns = [
    path("jwtsecret/", CreateJWTSecretView.as_view(), name="jwtsecret-create")
]
