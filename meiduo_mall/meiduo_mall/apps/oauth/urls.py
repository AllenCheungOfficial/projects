# 从urls模块中导入url
from django.conf.urls import url


# 从当前目录导入我们的视图模块views
from . import views

urlpatterns = [
    # 获取QQ扫码登录链接
    url(r'^qq/authorization/$', views.QQURLView.as_view()),
    # QQ用户部分接口:
    url(r'^oauth_callback/$', views.QQUserView.as_view()),
]
