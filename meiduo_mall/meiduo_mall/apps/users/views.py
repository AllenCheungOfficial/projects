from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import re
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredMixin
from .models import User
from django.db import DatabaseError
from django_redis import get_redis_connection


# 添加用户中心类:
class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""

    def get(self, request):
        """提供个人信息界面"""

        return render(request, 'user_center_info.html')


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """实现退出登录逻辑"""

        # 1退出登陆
        logout(request)

        # 2清除cookie
        response = redirect(reverse('contents:index'))
        # response = http.HttpResponseRedirect(reverse('contents:index'))

        # 退出登录时清除 cookie 中的 username
        response.delete_cookie('username')

        # 返回响应
        return response


class LoginView(View):
    """用户名登录"""

    def get(self, request):
        """
        提供登录界面的接口
        返回前端登录页面
        :param request:
        :return: 登陆页面
        """

        return render(request, 'login.html')

    def post(self, request):
        """实现登录逻辑
        :param request: 请求对象
        :return: 登录结果

        """

        # 1. 接收前端传递参数
        # 用户名
        username = request.POST.get('username')
        # 密码
        password = request.POST.get('password')
        # 是否记住用户
        remembered = request.POST.get('remembered')

        # 2. 校验参数

        # 判断参数是否齐全
        # 这里注意: remembered 这个参数可以是 None 或是 'on'
        # 所以我们不对它是否存在进行判断:
        if not all([username, password]):
            return http.HttpResponseForbidden('缺少参数')

        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')

        # 3. 获取登录用户,并查看是否存在
        # 获取数据库信息对比
        user = authenticate(username=username, password=password)

        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 4. 实现状态保持
        login(request, user)

        # 设置状态保持的周期
        if remembered != 'on':
            # 不记住用户：浏览器会话结束就过期
            request.session.set_expiry(0)

        else:
            # 记住用户：None 表示两周后过期
            request.session.set_expiry(None)

        # 5. 返回响应
        # return redirect(reverse('contents:index'))

        # 改
        # 生成响应对象
        # response = redirect(reverse('contents:index'))

        # 获取跳转过来的地址(查询字符串)
        next = request.GET.get('next')

        # 判断参数是否存在:
        if next:
            # 如果是从别的页面跳转过来的, 则重新跳转到原来的页面
            response = redirect(next)

        else:
            # 如果是直接登陆成功，就重定向到首页
            response = redirect(reverse('contents:index'))

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 15 天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

        # 返回相应结果
        return response


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        # 获取手机号, 查询手机号数量, 并返回
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """

        # 去数据库中查询该用户名的个数
        count = User.objects.filter(mobile=mobile).count()
        # 返回个数
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'count': count
        })


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    # /usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/
    def get(self, request, username):
        """
        获取手机号,查询用户名数量,并返回
        :param request: 请求对象
        :param username:  用户名
        :return: JSON
        """
        # 去数据库中查询该用户名的个数
        count = User.objects.filter(username=username).count()
        # 返回个数
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok',
                                  'count': count})


# 类视图
class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面返回前端
        """

        return render(request, 'register.html')

    def post(self, request):
        """
        实现用户注册
        :param request:请求对象
        :return: 注册
        """
        # 1.接收参数

        # 用户名
        username = request.POST.get('username')

        # 密码
        password = request.POST.get('password')

        # 确认密码
        password2 = request.POST.get('password2')

        # 手机号码
        mobile = request.POST.get('mobile')

        # TODO sms_code
        sms_code_client = request.POST.get('sms_code')

        # 是否同意用户协议
        allow = request.POST.get('allow')

        # 2.校验参数

        # 判断参数是否齐全
        if not all([username, password, password2, mobile, allow]):
            # 状态码403,资源不可用,比如IIS或者apache设置了访问权限不当
            return http.HttpResponseForbidden('缺少必传参数')

        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次密码输入不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确手机号')
        # TODO sms_code 短信验证码 没接收处理

        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        # 增加的部分：校验sms_code短信验证码:
        # 获取 redis 链接对象
        redis_conn = get_redis_connection('verify_code')

        # 从 redis 中获取保存的 sms_code
        sms_code_server = redis_conn.get('sms_code_%s' % mobile)

        # 判断 sms_code_server 是否存在
        if sms_code_server is None:
            # 不存在直接返回, 说明服务器的过期了, 超时
            return render(request, 'register.html', {'sms_code_errmsg': '验证码失效'})

        # 如果 sms_code_server 存在, 则对比两者:
        if sms_code_server.decode() != sms_code_client:
            # 对比失败, 说明短信验证码有问题, 直接返回:
            return render(request, 'register.html', {'sms_code_errmsg': '输入验证码的有误'})

        # 3.保持注册数据
        try:
            #  create_user() 方法中封装了 set_password() 方法加密密码
            user = User.objects.create_user(username=username, password=password, mobile=mobile)

        except DatabaseError:
            # 出现错误返回register.html的页面
            return render(request, 'register.html', {'register_errmsg': '保存用户名失败'})

        # 实现状态保持
        # request.session[] = 'value'
        login(request, user)

        # 4.返回前端 TODO
        # return http.HttpResponse('注册成功，应该跳转到首页')

        # 响应注册结果：重定向到首页
        # return redirect(reverse('contents:index'))

        # 改
        # 生成相应对象
        response = redirect(reverse('contents:index'))

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 15 天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

        # 返回相应结果
        return response
