from django.urls import path, include
from rest_framework import routers
from . import views

app_name = 'api'
router = routers.DefaultRouter()
router.register('courses', views.CourseViewSet)


urlpatterns = [
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/<pk>/', views.SubjectDetailView.as_view(), name='subject_detail'),
    # path('courses/<pk>/enroll/', views.CourseEnrollView.as_view(), name='course_enroll'),  # 最后没有/的话会匹配不上。。。
    path('', include(router.urls))
]
