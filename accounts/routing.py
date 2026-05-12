from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/faculty/hub/', consumers.FacultyConsumer.as_asgi()),
    path('ws/attendance/<uuid:session_id>/', consumers.AttendanceConsumer.as_asgi()),
]
