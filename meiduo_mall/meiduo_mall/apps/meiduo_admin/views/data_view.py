from datetime import date

from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User
from orders.models import OrderInfo
from datetime import timedelta
from goods.models import GoodsVisitCount
from rest_framework import serializers
from rest_framework.generics import ListAPIView


class GoodsVisitCountSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = GoodsVisitCount
        fields = ['count', 'category']


class GoodsVisitView(ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = GoodsVisitCount.objects.all()
    serializer_class = GoodsVisitCountSerializer

    def get_queryset(self):
        return self.queryset.filter(date=date.today())

# # 统 计最近30天，每一天新增用户量
# 请求方式：GET /meiduo_admin/statistical/month_increment/
# 请求参数： 通过请求头传递jwt token数据。
# 返回数据： JSON
class UserMonthIncrView(APIView):
    def get(self, request):
        # 获得当天日期
        cur_date = date.today()

        # 获得起始日期
        # 5-24  减去  29天
        # timedelta对象是一个时间段，days=29代表29天
        # cur_date是一个时间点对象
        start_date = cur_date - timedelta(days=29)

        user_list = []
        # 遍历这30天，统计每一天用户增量
        for index in range(30):
            # calc_date就是用于计算用户增量的那一天！
            calc_date = start_date + timedelta(days=index)

            # calc_date:  4-25
            # 4-25 0：0：0    <=  User.create_time   <  4-26 0:0:0
            count = User.objects.filter(date_joined__gte=calc_date,
                                        date_joined__lt=calc_date + timedelta(days=1)).count()

            data = {
                "count": count,
                "date": calc_date
            }

            user_list.append(data)
        # 构建数据返回
        return Response(user_list)


# 日下单用户量统计
# 请求方式：GET /meiduo_admin/statistical/day_orders/
# 请求参数： 通过请求头传递jwt token数据。
# 返回数据： JSON
class UserOrderCountView(APIView):
    def get(self, request):
        # 根据已知条件查询目标数据
        # 已知条件是从表条件还是主表条件
        # 1、从从表入手； 2、从主表入手查询

        # 获取当天日期
        cur_date = date.today()

        # 从从表入手查询： 分2部
        # 第一步：找从表对象
        # 第二步：在从表对象中找主表对象
        # # 根据当天日期过滤出所有订单
        # order_query = OrderInfo.objects.filter(create_time__gte=cur_date)
        # order_list = []
        # for order in order_query:
        #     # order: 订单对象
        #     order_list.append(order.user)
        # # 在所有订单中找出用户，统计用户数据, 去重
        # count = len(set(order_list))

        # 从主表入手
        # 已知条件：订单创建日期（从表）
        # 查询目标数据： 用户
        count = User.objects.filter(orders__create_time__gte=cur_date).count()
        # 返回
        return Response({
            'count': count,
            'date': cur_date
        })


# 日活跃用户统计
# 请求方式：GET
# 请求参数： 通过请求头传递jwt token数据。
# 返回数据： JSON
class UserActiveCountView(APIView):
    def get(self, request):
        # 获取当前日期
        cur_date = date.today()
        # 过滤最后登陆是当天
        query = User.objects.filter(last_login__gte=cur_date)
        count = query.count()
        # 返回
        return Response({
            'count': count,
            'date': cur_date
        })


# 日增用户统计
# get
# 通过请求头传递jwt token数据。
# 返回json(count, date)
class UserDayCountView(APIView):
    def get(self, request):
        # 获取当前日期
        cur_data = date.today()
        # 过滤当前日期 新创建的用户
        count = User.objects.filter(date_joined__gte=cur_data).count()

        # 返回数据
        return Response({
            'count': count,
            'date': cur_data
        })


# 获得用户总量统计
# get
# 通过请求头传递jwt token数据。
# 返回json
class UserTotalCountView(APIView):
    def get(self, request):
        # 获取当前日期
        cur_data = date.today()  # 当日，日期

        # 获取所有用户总数
        count = User.objects.count()

        # 构建返回数据
        return Response({
            'count': count,
            'date': cur_data
        })
