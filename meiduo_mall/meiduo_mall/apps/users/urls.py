
# 总路由

from django.conf.urls import url
from django.contrib import admin

from meiduo_mall.apps.users import views

urlpatterns = [
    # 注册
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
]