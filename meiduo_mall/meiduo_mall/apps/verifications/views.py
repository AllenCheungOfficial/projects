import random
from django.shortcuts import render
from django.views import View
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django import http

from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from meiduo_mall.utils.response_code import RETCODE
import logging

logger = logging.getLogger('django')


class SMSCodeView(View):
    """短信验证码"""

    def get(self, request, mobile):
        """

        :param request: 请求对象
        :param mobile: 手机号
        :return:json
        """

        # 3.创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({'code':RETCODE.THROTTLINGERR,
                                      'errmsg':'发送短信过于频繁'
                                      })
        # 1.接收参数: 查询字符串: request.GET表单: request.POST
        # 客户端来的图形验证码:
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.校验参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必穿参数'})

        # 4.:获取服务端图行验证码
        image_code_server = redis_conn.get('img_code_%s' % uuid)

        # 5.判断服务端验证码是否过期
        if image_code_server is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR,
                                      'errmsg': '图行验证码已无效'
                                      })

        # 6.删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete('img_code_%s' % uuid)
        except Exception as e:
            # 打印错误日志
            logger.error(e)

        # 7.对比图形验证码  # bytes转字符串 # 转小写后比较
        if image_code_server.decode().lower() != image_code_client.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR,
                                      'errmsg': '输入验证码有误'})

        # 8.生成短信验证码:6位.随机
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        # 获取redis中的管道对象
        pl = redis_conn.pipeline()

        # 8. 保存短信验证码:redis,  将Redis请求添加到队列
        # 短信验证码有效期，单位：秒
        pl.setex('sms_code_%s' % mobile, 300, sms_code)
        pl.setex('sms_flag_%s' % mobile, 60, 1)

        # 执行请求
        pl.execute()

        # 9.发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)
        from celery_tasks.sms.tasks import send_sms_code
        # Celery 异步发送短信验证码
        send_sms_code.delay(mobile, sms_code)

        # 10.返回
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


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
