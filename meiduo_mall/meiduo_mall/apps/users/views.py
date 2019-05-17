from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django import http
import re
import json

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredMixin, LoginRequiredJSONMixin
from .models import User, Address
from django.db import DatabaseError
from django_redis import get_redis_connection
import logging

logger = logging.getLogger('django')


class UserBrowseHistory(LoginRequiredJSONMixin, View):
    """用户浏览记录"""

    def get(self, request):
        """获取用户浏览记录"""
        # 1. 创建redis链接对象
        redis_conn = get_redis_connection('history')

        # 2. 获取sku_ids(value): lrange(key, 开始位置, 结束为止)
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)

        # 3. 遍历:
        skus = []
        for sku_is in sku_ids:
            # 4. 根据id获取商品信息
            sku = SKU.objects.get(id=sku_is)

            # 5. 拼接商品信息
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image_url,
                'price': sku.price
            })

            # 6.返回
            return http.JsonResponse({
                'code': RETCODE.OK,
                'errmsg': 'ok',
                'skus': skus
            })

    def post(self, request):
        """保存用户浏览记录"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 校验参数
        try:
            SKU.objects.get(id=sku_id)

        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不正确')

        # 链接redis
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        user_id = request.user.id

        # 4.去重
        pl.lrem('history_%s' % user_id, 0, sku_id)

        # 5.存储
        pl.lpush('history_%s' % user_id, sku_id)

        # 6.截取
        pl.ltrim('history_%s' % user_id, 0, 4)

        # 管道执行:
        pl.execute()

        # 7.返回
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""

    def get(self, request):
        """展示修改密码界面"""
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """实现修改密码逻辑"""
        print(request.body)
        # 接收参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return http.HttpResponseForbidden('缺少必传参数')

        try:
            request.user.check_password(old_password)

        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')

        if new_password != new_password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()

        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})

        # 清除状态保持信息
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')

        # 响应密码修改结果：重定向到登录界面
        return response


class UpdateTitleAddressView(LoginRequiredJSONMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({
                'code': RETCODE.DBERR,
                'errmsg': '设置地址标题失败'
            })

        # 4.响应删除地址结果
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': '设置地址标题成功'
        })


class DefaultAddressView(LoginRequiredJSONMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({
                'code': RETCODE.DBERR,
                'errmsg': '设置默认地址失败'
            })

        # 响应设置默认地址结果
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': '设置默认地址成功'

        })


class UpdateDestroyAddressView(LoginRequiredJSONMixin, View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""
        # 拼接参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')

        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email

            )

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({
                'code': RETCODE.DBERR,
                'errmsg': '更新地址失败'
            })

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': '更新地址成功',
            'address': address_dict
        })

    def delete(self, request, address_id):
        """逻辑删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})
        # 响应删除地址结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class CreateAddressView(LoginRequiredJSONMixin, View):
    """新增地址"""

    def post(self, request):
        """实现新增地址逻辑"""

        # 1. 获取数量,判断是否超过20
        # request.user.addresses 得到（唯一用户）address一张表
        count = request.user.addresses.count()

        # 判断是否超过地址上限：最多20个
        if count >= 20:
            # RETCODE.THROTTLINGERR:  4002
            return http.JsonResponse({
                'code': RETCODE.THROTTLINGERR,
                'errmsg': '超过地址数量上限'
            })

        # 2.接收参数
        json_dict = json.loads(request.body.decode())

        receiver = json_dict.get('receiver')

        province_id = json_dict.get('province_id')

        city_id = json_dict.get('city_id')

        district_id = json_dict.get('district_id')

        place = json_dict.get('place')

        mobile = json_dict.get('mobile')

        tel = json_dict.get('tel')

        email = json_dict.get('email')

        # 3.校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')

        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 4.保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email

            )

            # 4.1设置默认地址

            # 如果没有默认地址
            if not request.user.default_address:
                # 把新增加的地址设置为默认地址
                request.user.default_address = address

                # 保存到db
                request.user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({
                'code': RETCODE.DBERR,
                'errmsg': '新增地址失败'
            })

        # 新增地址成功，将新增的地址 拼接 响应给前端实现局部刷新
        address_data = {
            "id": address.id,

            "title": address.title,

            "receiver": address.receiver,

            "province": address.province.name,

            "city": address.city.name,

            "district": address.district.name,

            "place": address.place,

            "mobile": address.mobile,

            "tel": address.tel,

            "email": address.email
        }

        # 响应保存结果
        return http.JsonResponse({
            'code': RETCODE.OK,
            'address': address_data
        })


class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """提供地址管理界面
                """
        # 获取所有的地址:
        # is_deleted 可执行逻辑删除
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        # 创建空的列表
        address_dict_list = []
        # 遍历
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }

            # 将默认地址移动到最前面
            default_address = request.user.default_address
            if default_address.id == address.id:
                # 查询集 addresses 没有 insert 方法
                address_dict_list.insert(0, address_dict)
            else:
                address_dict_list.append(address_dict)

        context = {
            'default_address_id': request.user.default_address_id,
            'addresses': address_dict_list,
        }

        return render(request, 'user_center_site.html', context=context)


class VerifyEmailView(View):
    """验证邮箱"""

    def get(self, request):
        # 接收参数
        token = request.GET.get('token')

        # 校验参数：判断 token 是否为空和过期，提取 user
        if not token:
            return http.HttpResponseForbidden('缺少token')

        # 调用上面封装好的方法, 将 token 传入
        user = User.check_verify_email_token(token)

        if not user:
            return http.HttpResponseForbidden('无效的token')

        # 修改 email_active 的值为 True
        try:
            user.email_active = True
            user.save()

        except Exception as e:
            logging.error(e)
            return http.HttpResponseForbidden('激活邮件失败')

        login(request, user)
        # 返回邮箱验证结果
        return redirect(reverse('users:info'))


class EmailView(LoginRequiredJSONMixin, View):
    """添加邮箱"""

    def put(self, request):
        """接收邮箱,保存到数据库中"""

        # 1.接收参数
        # request.POST
        # request.GET
        # json_str = request.body.decode()
        # json_dict = json.loads(json_str)
        # email = json_dict.get('email')

        # 接收，解码，str转dict获取key(email,参数)
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 2. 校验参数
        if not email:
            return http.HttpResponseForbidden('缺少email参数')

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('email格式不正确')

        # 更改数据库,赋值 email 字段
        # User.objects.update()
        try:
            # 赋值前段传的email到db
            request.user.email = email
            # 修改db保存
            request.user.save()
        except Exception as e:
            logging.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '保存邮箱失败'})

        # 发送验证邮件:
        from celery_tasks.email.tasks import send_verify_email

        # 异步发送验证邮件
        verify_url = request.user.generate_verify_email_url()
        send_verify_email.delay(email, verify_url)

        # 返回
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '邮箱保存成功'})


# 添加用户中心类:
class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""

    def get(self, request):
        """提供个人信息界面"""
        # 将验证用户的信息进行拼接
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active,

        }
        # 返回响应
        print(context)
        return render(request, 'user_center_info.html', context=context)


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

        # 合并购物车
        response = merge_cart_cookie_to_redis(request=request, user=user, response=response)

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
