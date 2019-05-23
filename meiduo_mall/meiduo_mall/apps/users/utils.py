import re

from django.contrib.auth.backends import ModelBackend
from .models import User


def get_user_by_account(account):
    """
       根据account查询用户
       :param account: 用户名或者手机号
       :return: user
       """
    try:
        # 手机号登录
        if re.match('^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)

        else:
            # 用户名登录
            user = User.objects.get(username=account)
    except Exception as e:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定义用户认证后端"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
                重写认证方法，实现用户名和mobile登录功能
                :param request: 请求对象
                :param username: 用户名
                :param password: 密码
                :param kwargs: 其他参数
                :return: user
                """

        # 自定义验证用户是否存在的函数:
        # 根据传入的 username 获取 user 对象
        # username 可以是手机号也可以是账号
        user = get_user_by_account(username)

        # 如果此次身份认证是后台站点登陆
        # 值允许超级管理员登陆
        # 区分是后台站登陆的情况下才需要判断超级管理员
        if request == None:  # request == None
            # 后台管理站点登陆
            try:
                if not user.is_staff:
                    return None
            except:
                pass

        # 校验user是否存在并校验密码是否正确
        if user and user.check_password(password):
            return user


