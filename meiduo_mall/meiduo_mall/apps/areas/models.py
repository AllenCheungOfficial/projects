from django.db import models


class Area(models.Model):
    """
    行政区划
    """
    # 创建 name 字段, 用户保存名称
    name = models.CharField(max_length=20, verbose_name='名称')

    # 自关联字段 parent
    # 外键 ForeignKey
    # 第一个参数是 self : parent关联自己.
    # on_delete=models.SET_NULL:  如果省删掉了,省内其他的信息为 NULL
    # related_name='subs': 设置之后(外键的别名，反向查询使用，父级查询子级)
    # 我们就这样调用获取市: area.area_set.all() ==> area.subs.all()
    # 这个字段可以为空null=True
    # 字段可以不写内容blank=True
    parent = models.ForeignKey('self',
                               on_delete=models.SET_NULL,
                               related_name='subs',
                               null=True,
                               blank=True,
                               verbose_name='上级行政区划'
                               )

    # 表的设置
    class Meta:
        db_table = 'tb_areas'
        verbose_name = '上级行政区划'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name