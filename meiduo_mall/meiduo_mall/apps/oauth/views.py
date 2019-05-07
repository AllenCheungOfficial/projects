from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django.contrib.auth import login
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import logging
import re
from oauth.models import OAuthQQUser
from oauth.utils import generate_access_token, check_access_token
from django_redis import get_redis_connection
from users.models import User
logger = logging.getLogger('django')
from meiduo_mall.utils.response_code import RETCODE


class QQUserView(View):
    """用户扫码登录的回调处理"""

    def get(self, request):
        '''
        接收code值, 去qq服务器验证, 去数据库中验证是否有该用户直接让他登录.
        如果用户不存在,则把openid加密生成token, 返回
        :param request:
        :return:
        '''

        # 1.code的接收
        code = request.GET.get('code')

        # 2.判断是否存在code
        if not code:
            return http.HttpResponseForbidden('缺少code参数')
        # 3.获取工具类对象

        # 创建对象
        # 创建对象的时候, 需要传递四个参数:
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 4.调用对象函数，获取access_token
            access_token = oauth.get_access_token(code)
            # 5.调用access_token获取openid
            openid = oauth.get_open_id(access_token)

        except Exception as e:

            # 如果上面获取 openid 出错, 则验证失败
            logger.error(e)

            # 返回结果
            return http.HttpResponseServerError('OAuth2.0认证失败')

        # 6.判断openid是否在db中
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:

            # 8.如果不在
            # 把openid加密成access_token
            # 如果 openid 没绑定美多商城用户,进入这里:
            # 调用我们封装好的方法, 对 openid 进行加密, 生成 access_token 字符串
            access_token = generate_access_token(openid)

            # 让他重新跳转到下一个绑定页面
            # 拿到 access_token 字符串后, 拼接字典
            context = {
                'access_token': access_token
            }

            # 返回响应, 重新渲染
            return render(request, 'oauth_callback.html', context=context)


        else:
            # 7.如果在：
            # 如果 openid 已绑定美多商城用户
            # 根据 user 外键, 获取对应的 QQ用户
            qq_user = oauth_user.user

            # 状态保持
            login(request, qq_user)

            # 创建重定向到主页的对象
            response = redirect(reverse('contents:index'))

            # 设置cookie # 将用户信息写入到 cookie 中，有效期14天
            response.set_cookie('username', qq_user.username, max_age=3600 * 24 * 14)

            # 重定向到首页
            return response

    def post(self, request):
        """美多商城用户绑定到openid"""

        # 1.接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        access_token = request.POST.get('access_token')

        # 2.校验参数( mobile, password, sms_code:redis中取,对比,  access_token)
        # 判断参数是否齐全
        if not all([mobile, password, sms_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')

        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        # 3.判断短信验证码是否一致
        # 创建 redis 链接对象:
        redis_conn = get_redis_connection('verify_code')

        # 从 redis 中获取 sms_code 值:
        sms_code_server = redis_conn.get('sms_code_%s' % mobile)

        # 判断获取出来的有没有:
        if sms_code_server is None:
            # 如果没有, 直接返回:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码'})

        # 如果有, 则进行判断:
        if sms_code_server.decode() != sms_code_client:
            # 如果不匹配, 则直接返回:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入的验证码错误'})

        # 调用我们自定义的函数, 检验传入的 access_token 是否正确:
        # 错误提示放在 sms_code_errmsg 位置
        openid = check_access_token(access_token)

        if openid is None:
            return render(request, 'oauth_callback.html', {'openid_errmsg': '无效的openid'})

        # 4.查看mobile有没有与之关联的账,保存注册数据
        try:
            user = User.objects.get(mobile=mobile)

        except Exception as e:

            # 用户不存在,新建用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)

        else:
            # 如果用户存在，检查用户密码
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})

        # 5.将用户绑定 openid,如果有: 绑定:  创建一个OAuthQQUser 与之绑定
        try:
            OAuthQQUser.objects.create(openid=openid, user=user)

        except DatabaseError:

            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})

        # 6.实现状态保持
        login(request, user)

        # 7.响应绑定结果
        next = request.GET.get('state')

        if next:

            response = redirect(next)

        else:
            response = redirect(reverse('contents:index'))

        # 8.登录时用户名写入到 cookie，有效期14天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        # 响应
        return response


class QQURLView(View):
    """返回QQ登录页面网址；方便用户登陆
     https://graph.qq.com/oauth2.0/authorize?
     response_type=code&
     client_id=xxx&
     redirect_uri=xxx&
     state=xxx
     """

    def get(self, request):
        # 1.接收参数（该参数不是必传的）
        # next 表示从哪个页面进入到的登录页面，将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')

        # 2.生成工具类(QQloginTool)的对象
        # 创建对象
        # 创建对象的时候, 需要传递四个参数:
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 3.调用函数，生成url
        login_url = oauth.get_qq_url()

        # 4.返回
        return http.JsonResponse({'code':RETCODE.OK, 'errmsg': 'ok', 'login_url': login_url})
