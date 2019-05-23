from django.conf.urls import url, include
from django.contrib import admin
from .views import *
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    # url(r'^authorizations/', JWTLogin.as_view()),
    url(r'^authorizations/', obtain_jwt_token),
]
