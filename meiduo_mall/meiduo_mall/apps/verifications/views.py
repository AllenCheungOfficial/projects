from django.shortcuts import render
from django.views import View
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django import http


class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        """

        :param requset: 请求对象
        :param uuid: 唯一标识图形验证码所属于的用户
        :return: image/jpg
        """
        # 1.生成图片
        text, image = captcha.generate_captcha()

        # 2.服务端保存： redis
        # 2.1创建连接，生成图片验证码
        redis_conn = get_redis_connection('verify_code')

        # 保存图片验证码到reids
        # redis_conn.set()

        # 保存的同时有，有效期,声明图片类型
        # 图形验证码有效期，单位：秒
        # IMAGE_CODE_REDIS_EXPIRES = 300
        redis_conn.setex('img_code_%s' % uuid, 300, text)  # expire

        # 3.返回：图片
        # 响应图片验证码
        return http.HttpResponse(image, content_type='image/jpg')
