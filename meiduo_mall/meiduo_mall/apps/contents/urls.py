# 从urls模块中导入url
from django.conf.urls import url


# 从当前目录导入我们的视图模块views
from . import views

urlpatterns = [
    # 首页广告
    url(r'^$', views.IndexView.as_view(), name='index'),
]
