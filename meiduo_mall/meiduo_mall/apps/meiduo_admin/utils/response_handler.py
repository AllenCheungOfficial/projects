

# 定义一个函数
# 让obtain_jwt_token视图去使用获得返回结果

def jwt_response_payload_handler(token, user=None, request=None):
    """
    :param token: obtain_jwt_token视图生成的token
    :param user: 用户对象
    :param request: 请求对象
    :return:
    """
    return {
        "username": user.username,
        "user_id": user.id,
        "token": token
    }
