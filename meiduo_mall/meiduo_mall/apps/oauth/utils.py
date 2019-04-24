from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings


def generate_access_token(openid):
    """
   签名(程序界加密的意思) openid
   :param openid: 用户的 openid
   :return: access_token
   """

    # 使用方式:
    # TimedJSONWebSignatureSerializer(秘钥, 有效期秒)
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=300)

    data = {'openid': openid}

    # serializer.dumps(数据):加密, 返回值二进 bytes 类型
    token = serializer.dumps(data)

    return token.decode()


# 定义函数, 检验传入的 access_token 里面是否包含有 openid
def check_access_token(access_token):
    """
    检验用户传入的 token
    :param token: token
    :return: openid or None
    """
    # 调用 itsdangerous 中的类, 生成对象
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=300)

    try:
        # 尝试使用对象的 loads 函数:解密
        # 对 access_token 进行反序列化( 类似于解密 )
        # 查看是否能够获取到数据:
        data = serializer.loads(access_token)

    except BadData:
        # 如果出错, 则说明 access_token 里面不是我们认可的.
        # 返回 None
        return None

    else:
        # 如果能够从中获取 data, 则把 data 中的 openid 返回
        return data.get('openid')
