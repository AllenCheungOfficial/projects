from django import http
from django.contrib.auth.decorators import login_required
from meiduo_mall.utils.response_code import RETCODE
from django.utils.decorators import wraps


# 添加扩展类:
# 因为这类扩展其实就是 Mixin 扩展类的扩展方式
# 所以我们起名时, 最好也加上 Mixin 字样, 不加也可以.
class LoginRequiredMixin(object):
    '''
       作用: 检验用户是否登录, 如果没有登录, 跳转到login页面
    '''

    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类的 as_view() 函数
        view = super().as_view()
        return login_required(view)


def login_required_json(view_func):
    """
    判断用户是否登录的装饰器，并返回 json
    :param view_func: 被装饰的视图函数
    :return: json、view_func
    """

    # @wraps: 返回view_func的函数名和文档
    @wraps(view_func)
    def wrapper(requset, *args, **kwargs):
        # 如果用户未登录，返回 json 数据
        if not requset.user.is_authenticated():
            return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})

        else:
            # 如果用户登录，进入到 view_func 中
            return view_func(requset, *args, **kwargs)

    return wrapper


class LoginRequiredJSONMixin(object):
    '''
    作用: 检验用户是否登录, 如果没有登录,返回json格式的结果
    '''

    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类的 as_view() 函数
        view = super().as_view()
        return login_required_json(view)

    # def view(self):
    #     '''
    #     111
    #     :return:
    #     '''
    #     pass
    #
    # help(view)  # 111
    # view ----> view()
    #
    #
    #
    #
    #
    #
    # @viewfunc(view)    #  == = > view = viewfunc(view)
    # def view(self):
    #     '''
    #     1111
    #     :return:
    #     '''
    #     pass
    #
    # help(view)  # 222
    # view ----> wrapper
    #
    #
    #
    # @viewfunc(view)    #  == = > view = viewfunc(view)
    # def func(self):
    #     '''
    #     1111
    #     :return:
    #     '''
    #     pass
    #
    # help(view)  # 222