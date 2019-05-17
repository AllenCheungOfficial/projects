# 从urls模块中导入url
from django.conf.urls import url


# 从当前目录导入我们的视图模块views
from . import views

urlpatterns = [
    # 购物车查询和新增和修改和删除
    url(r'^carts/$', views.CartsView.as_view(), name='info'),
    # 购物车全选
    url(r'^carts/selection/$', views.CartSelectAllView.as_view()),

]
