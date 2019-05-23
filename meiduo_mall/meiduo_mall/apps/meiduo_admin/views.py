from django.shortcuts import render
# 视图采用
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.response import Response
from users.models import User
from rest_framework_jwt.utils import jwt_payload_handler, jwt_encode_handler


# 序列化器
class UserSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # 用户名和密码的校验逻辑
        username = attrs['username']
        password = attrs['password']

        # 获得用户对象
        user = User.objects.get(username=username)
        # 如果用户存在 并且 密码正确
        if user and user.check_password(password):
            # 传统的身份认证通过
            # 签发token
            payload = jwt_payload_handler(user)
            jwt_token = jwt_encode_handler(payload)

            return {
                "user": user,
                "token": jwt_token
            }

        raise serializers.ValidationError("用户校验失败！")


class JWTLogin(APIView):
    # POST
    # 参数： username和password -- json body
    # 返回数据json
    # {
    #    "username":xxx,
    #    "user_id":xxx,
    #    "token": xxxx,
    # }
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # serializer.validated_data

        # 返回数据
        return Response({
            "username": serializer.validated_data['user'].username,
            "user_id": serializer.validated_data['user'].id,
            "token": serializer.validated_data['token']
        })
