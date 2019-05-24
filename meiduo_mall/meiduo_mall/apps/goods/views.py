from django.shortcuts import render
import datetime
from django import http
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render
from django.utils import timezone
from datetime import date
from django.views import View

from goods.models import GoodsCategory, SKU, GoodsVisitCount
from goods.utils import get_categories, get_breadcrumb, get_goods_and_spec
from meiduo_mall.utils.response_code import RETCODE
import logging
logger = logging.getLogger('django')


class DetailVisitView(View):
    """详情页分类商品访问量"""

    def post(self, request, category_id):
        """记录分类商品访问量"""
        # 1.根据传入的 category_id 值, 获取对应类别的商品:
        try:
            category = GoodsCategory.objects.get(id=category_id,date=date.today)

        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('缺少必传参数')
        # 2.创建当前时间

        # 先获取时间对象
        t = timezone.localtime()

        # 根据时间对象拼接日期的字符串形式:
        today_str = '%d-%02d-%02d' % (t.year, t.month, t.day)

        # 将字符串转为日期格式:
        today_date = datetime.datetime.strptime(today_str, '%Y-%m-%d')

        # 3.将今天的日期传入进去, 获取该商品今天的访问量:
        try:

            # 查询今天该类别的商品的访问量
            counts_data = category.goodsvisitcount_set.get(date=today_date)

        except GoodsVisitCount.DoesNotExist:
            # 4.如果不存在记录，新建一个
            counts_data = GoodsVisitCount()

        # 5.更改
        try:
            # 更新模型类对象里面的属性: category 和 count
            counts_data.category = category
            counts_data.count += 1
            counts_data.save()

        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('服务器异常')

        # 6.返回
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class DetailView(View):
    """商品详情页"""
    def get(self, request, sku_id):
        """提供商品详情页"""

        # 商品分类菜单
        categories = get_categories()

        # 调用封装的函数, 根据 sku_id 获取对应的
        # 1. 类别( sku )
        # 2. 商品( goods )
        # 3. 商品规格( spec )
        data = get_goods_and_spec(sku_id, request)

        # 拼接数据，渲染页面
        context = {
            'categories': categories,
            'goods': data.get('goods'),
            'specs': data.get('goods_specs'),
            'sku': data.get('sku')
        }

        # 返回
        return render(request, 'detail.html', context)


class HotGoodsView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行 JSON 数据"""
        # 1. 根据category_id(类别id),获取商品:  排序(销量) + 切片
        skus = SKU.objects.filter(category_id=category_id,
                                  is_launched=True).order_by('-sales')[:2]

        hot_skus = []
        # 2. 遍历商品, 获取每一个===> 拼接成字典 ===> 放到列表 ===> json
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url,
                'name': sku.name,
                'price': sku.price
            })

        # 3. 返回
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})


class ListView(View):
    """商品列表页,展示列表页面"""

    def get(self, request, category_id, page_num):
        """提供商品列表页"""

        # 1. 校验:category_id是否正确
        try:

            # 获取三级菜单分类信息:
            category = GoodsCategory.objects.get(id=category_id)

        except GoodsCategory.DoesNotExist:
            return http.HttpResponseNotFound('GoodsCategory 不存在')

        # 2. 获取商品频道
        categories = get_categories()

        # 3. 面包屑效果三级展示
        breadcrumb = get_breadcrumb(category)

        # 增加的内容:
        # 1.1 获取排序方式: 查询字符串
        # 接收sort参数：如果用户不传，就是默认的排序规则
        sort = request.GET.get('sort', 'default')

        # 1.2 判断排序方式, 确定排序依据,按照排序规则查询该分类商品SKU信息
        if sort == 'price':

            # 按照价格由低到高
            sortkind = 'price'

        elif sort == 'hot':

            # 按照销量由高到低
            sortkind = '-sales'

        else:

            # 'price'和'sales'以外的所有排序方式都归为'default'
            sort = 'default'

            # 上架默认时间
            sortkind = 'create_time'

        # 1.3 获取所有商品,并且排序
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(sortkind)

        # 1.4 创建一个分页器对象,每页5条记录
        paginator = Paginator(skus, 5)

        # 1.5 获取对应页面的商品
        try:
            page_skus = paginator.page(page_num)

        except EmptyPage:

            return http.HttpResponseNotFound('empty page')

        # 1.6 获取总计的页数
        total_page = paginator.num_pages

        # 4. 拼接数据,渲染页面
        context = {
            'categories': categories,  # 频道分类
            'breadcrumb': breadcrumb,  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码

        }

        # 5. 返回
        return render(request, 'list.html', context=context)