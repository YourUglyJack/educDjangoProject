from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms.models import modelform_factory
from django.core.cache import cache
from django.db.models import Count
from django.apps import apps
from django.db import transaction
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from .models import Course, Module, Content, Subject
from .form import ModuleFormSet
from students.forms import CourseEnrollForm


# Create your views here.
class OwnerMixin(object):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin(object):
    # 设置表单实例的 owner 属性为当前用户。这样做的目的是为了在创建或更新对象时自动设置其拥有者
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerCourseMixin(LoginRequiredMixin, PermissionRequiredMixin, OwnerMixin):
    model = Course
    fields = ['subject', 'title', 'slug', 'overview']
    success_url = reverse_lazy('courses:manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'manage/course/list.html'
    permission_required = 'courses.view_course'


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'manage/course/delete.html'
    permission_required = 'courses.delete_course'


class CourseModuleUpdateView(TemplateResponseMixin, View):
    # 更新module
    template_name = 'manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)

    def dispatch(self, request, *args, **kwargs):
        # pk应该是从url获取的
        # 在这个URL模式中，<int:pk> 是一个关键字参数。当用户访问一个像 /course/1/update/ 这样的 URL 时，Django 会将 1 作为 pk 参数传递给 CourseModuleUpdateView 视图。
        pk = kwargs['pk']
        self.course = get_object_or_404(Course, id=pk, owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({'course': self.course, 'formset': formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            for form in formset:
                form.save()
            return redirect('courses:manage_course_list')
        return self.render_to_response({'course': self.course, 'formset': formset})


class ContentCreateUpdateView(TemplateResponseMixin, View):
    # 新增与更新content
    module = None
    model = None
    obj = None
    template_name = 'manage/content/form.html'

    def get_model(self, model_name):
        if model_name in {'text', 'video', 'image', 'file'}:
            return apps.get_model(app_label='courses', model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(model, exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        module_id = kwargs['module_id']
        model_name = kwargs['model_name']
        pk = kwargs.get('pk', None)
        self.module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        self.model = self.get_model(model_name)
        if pk:
            self.obj = get_object_or_404(self.model, id=pk, owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form, 'object': self.obj})

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.model, instance=self.obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not kwargs.get('pk', None):
                # new content
                Content.objects.create(module=self.module, content_obj=obj)
            return redirect('courses:module_content_list', self.module.id)
        return self.render_to_response({'form': form, 'object': self.obj})


class ContentDeleteView(View):
    # 删除content
    def post(self, request, pk):
        content = get_object_or_404(Content, id=pk, module__course__owner=request.user)
        module = content.module
        with transaction.atomic():
            content.content_obj.delete()
            content.delete()  # 引用这个content的会自动删除，如module，但是content引用的要手动删除，所以有了上面的 content.content_obj.delete()
        return redirect('courses:module_content_list', module.id)


class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'manage/module/content_list.html'

    def get(self, request, *args, **kwargs):
        module_id = kwargs['module_id']
        module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        return self.render_to_response({'module': module})


class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(id=id, course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id, module__course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = 'course/list.html'

    def get(self, request, *args, **kwargs):
        subject = kwargs.get('subject', None)

        subject_list = cache.get('all_subject_list')
        if not subject_list:
            subject_list = Subject.objects.annotate(total_courses=Count('courses'))  # total number of courses for each subject
            cache.set('all_subject_list', subject_list)

        all_course_list = cache.get('all_courses_list')
        if not all_course_list:
            all_course_list = Course.objects.annotate(total_modules=Count('modules'))  # total number of modules contained in each course
            cache.set('all_courses_list', all_course_list)

        if subject:
            subject = get_object_or_404(Subject, slug=subject)
            key = f'subject_{subject.id}_courses'
            course_list = cache.get(key)
            if not course_list:
                course_list = all_course_list.filter(subject=subject)
                cache.set(key, course_list)
        else:
            course_list = all_course_list

        ctx = {
            'subject_list': subject_list,
            'course_list': course_list,
            'subject': subject
        }

        return self.render_to_response(ctx)


class CourseDetailView(DetailView):
    model = Course
    template_name = 'course/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['enroll_form'] = CourseEnrollForm(initial={'course': self.object})
        return ctx
