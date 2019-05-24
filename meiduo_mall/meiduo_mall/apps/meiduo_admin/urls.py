from django.conf.urls import url, include
from django.contrib import admin
from .views import *
from rest_framework_jwt.views import obtain_jwt_token
from meiduo_admin.views.data_view import *
urlpatterns = [
    # url(r'^authorizations/', JWTLogin.as_view()),
    url(r'^authorizations/', obtain_jwt_token),
    # 获得用户总量
    url(r'^statistical/total_count/', UserTotalCountView.as_view()),
    # 获得当日新增用户
    url(r'^statistical/day_increment/', UserDayCountView.as_view()),
    # 日活跃度
    url(r'^statistical/day_active/', UserActiveCountView.as_view()),
    # 日下单
    url(r'^statistical/day_orders/', UserOrderCountView.as_view()),
    # 最近30，每以天的用户量
    url(r'^statistical/month_increment/', UserMonthIncrView.as_view()),
    # 返回商品类别访问量
    url(r'^statistical/goods_day_views/', GoodsVisitView.as_view()),
]
