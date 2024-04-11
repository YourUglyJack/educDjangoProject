from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def course_chat_room(req, course_id):
    try:
        course = req.user.courses_joined.get(id=course_id)
    except:
        return HttpResponseForbidden
    return render(req, 'chat/room.html', {'course': course})
