from django.shortcuts import render
from django.views import View


class IndexView(View):
    """
     定义首页广告视图：IndexView
    """

    def get(self,request):
        """
        提供首页广告界面
        """

        return render(request, 'index.html')
