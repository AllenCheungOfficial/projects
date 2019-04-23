from django.db import models


class BaseModel(models.Model):
    """为模型类补充字段"""

    # auto_now_add：当前时间会随着创建自动生成,创建或添加对象时的时间, 修改或更新对象时, 不会更改时间
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    # auto_now：当前模型类被修改时，时被重新赋值,凡是对对象进行操作(创建/添加/修改/更新),时间都会随之改变
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        # 说明是抽象模型类 :声明该模型类仅继承使用，数据库迁移时不会创建 BaseModel 的表
        abstract = True
