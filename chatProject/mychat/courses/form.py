from django import forms
from django.forms.models import inlineformset_factory
from .models import Course, Module

# 这个 ModuleFormSet 可以在视图和模板中使用，以便用户可以在一个表单中编辑一个 Course 对象和它关联的多个 Module 对象。
# Course是父模型，Module是子模型；这个表单集将用于编辑 Course 对象关联的 Module 对象。
ModuleFormSet = inlineformset_factory(Course, Module, fields=['title', 'description'], extra=2, can_delete=True)