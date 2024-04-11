from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/room/(?P<course_id>\d+)/$', consumers.ChatConsumer),
]

# ?P<name> 是一个特殊的语法，用于给匹配的模式命名。这是Python的一个特性，被称为"命名组"。
# 在你的正则表达式 (?P<course_id>\d+) 中，?P<course_id> 定义了一个名为 course_id 的组，\d+ 是匹配的模式，表示一个或多个数字。所以，这个正则表达式匹配一个或多个数字，并将这个匹配的结果命名为 course_id