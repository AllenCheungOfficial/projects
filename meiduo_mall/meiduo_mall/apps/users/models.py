from django.contrib.auth.models import AbstractUser
from django.db import models


# 我们重写用户模型类, 继承自 AbstractUser
class User(AbstractUser):
    """自定义用户模型类"""

    # 在用户模型类中增加 mobile 字段
    # models.CharField这个位置指出了当前字段的类型:
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    # 对当前表进行相关设置:
    class Meta:

        db_table = 'tu_users' # 指明数据库表名
        verbose_name = '用户' # 在admin站点中显示的名称
        verbose_name_plural = verbose_name  # 显示的复数名称

    # 在 str 魔法方法中, 返回用户名称
    def __str__(self):
        """定义每个数据对象的显示信息"""
        return self.username









