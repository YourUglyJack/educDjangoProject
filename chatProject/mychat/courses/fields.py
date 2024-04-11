from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class OrderField(models.PositiveIntegerField):
    def __init__(self, for_fields=None, *args, **kwargs):
        self.for_fields = for_fields
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if getattr(model_instance, self.attname) is None:  # 如果没有显式指定order，就自己计算一个
            try:
                qs = self.model.objects.all()
                if self.for_fields:  # 筛选出是在哪个范围内进行排序，自己get一下。。。
                    query = {field: getattr(model_instance, field) for field in self.for_fields}
                    qs = qs.filter(**query)  # 在 Django中，filter 方法应当接收关键字参数，而不是字典。你应该将字典解包，将其作为关键字参数传递给 filter 方法
                last_item = qs.latest(self.attname)  # attname 应该就是order了
                value = last_item.order + 1
            except ObjectDoesNotExist:
                value = 0
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super().pre_save(model_instance, add)