from django.shortcuts import render
from django.views import View

from .models import ContentCategory
from goods.utils import get_categories


class IndexView(View):
    """
     定义首页广告视图：IndexView
    """

    def get(self,request):
        """
        提供首页广告界面
        """

        # 1.获取分类的三级数据
        categories = get_categories()

        # 5.定义一个空的字典
        dict = {}

        # 2.获取所有的广告分类
        content_categories = ContentCategory.objects.all()

        # 3遍历所有的广告分类，获取每一个分类，然后放入到定义的空字典中:
        for cat in content_categories:

            # 4.获取类别所对应的展示数据, 并对数据进行排序:
            # key:value  ==>  商品类别.key:具体的所有商品(排过序)
            dict[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # 6.拼接参数:
        context = {
            # 这是首页需要的一二级分类信息:
            'categories': categories,
            # 这是首页需要的能展示的三级信息:
            'contents': dict,
        }

        # 返回界面, 同时传入参数:
        return render(request, 'index.html',context=context)