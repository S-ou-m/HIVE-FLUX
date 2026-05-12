from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path('notifications/dropdown/', views.get_notifications_dropdown_partial, name='notifications_dropdown'),
    path('notifications/center/', views.notification_center_view, name='notification_center'),
    path('notifications/<uuid:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<uuid:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/settings/', views.notification_settings_view, name='notification_settings'),
    
    # Notice Center
    path('notices/', views.notice_center_view, name='notice_center'),
    path('notices/partial/list/', views.notice_list_partial, name='notice_list_partial'),
    path('notices/create/', views.create_notice_view, name='create_notice'),
    path('notices/<uuid:notice_id>/read/', views.mark_notice_read, name='mark_notice_read'),
    path('notices/<uuid:notice_id>/receipts/', views.notice_read_receipts, name='notice_read_receipts'),
    path('notices/banner/', views.get_critical_banner, name='get_critical_banner'),
    path('notices/counts/', views.get_notice_sidebar_counts, name='get_sidebar_counts'),
]
