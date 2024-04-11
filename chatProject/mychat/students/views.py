from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from .forms import CourseEnrollForm
from courses.models import Course


# Create your views here.
class StudentRegistrationView(CreateView):
    template_name = 'students/student/registration.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('students:student_course_list')

    def form_valid(self, form):
        res = super().form_valid(form)
        cd = form.cleaned_data
        user = authenticate(username=cd['username'], password=cd['password1'])
        login(self.request, user)
        return res


class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm
    template_name = 'students/course/detail.html'

    def form_valid(self, form):
        # 表单通过is_valid得验证后才会调用该函数
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('students:student_course_detail', args=[self.course.id])


class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'students/course/list.html'

    def get_queryset(self):
        qs = super(StudentCourseListView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])


class StudentCourseDetailView(DetailView):
    model = Course
    template_name = 'students/course/detail.html'

    def get_queryset(self):
        qs = super(StudentCourseDetailView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])

    def get_context_data(self, **kwargs):
        ctx = super(StudentCourseDetailView, self).get_context_data(**kwargs)
        course = self.get_object()
        # 在 Django 中，self.kwargs 是一个字典，它包含了所有从 URL 模式中捕获的参数
        # 在 Django 中，kwargs 是传递给视图的关键字参数，它们通常是通过 URL 模式中的命名组捕获的。在类视图中，这些参数会被存储在视图实例的 self.kwargs 属性中
        # 直接调用 kwargs 可能会有问题，具体看attention.txt
        if self.kwargs.get('module_id'):
            ctx['module'] = course.modules.get(id=self.kwargs['module_id'])
        else:
            if course.modules.all():
                ctx['module'] = course.modules.all()[0]
            else:
                ctx['module'] = None
        return ctx