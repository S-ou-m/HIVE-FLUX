from django.urls import path
from . import views

urlpatterns = [
    # Command Center
    path('execution/', views.execution_command_center, name='execution_command_center'),
    path('execution/sessions/', views.execution_sessions_partial, name='execution_sessions_partial'),
    path('execution/scanner/', views.execution_scanner_partial, name='execution_scanner_partial'),
    path('execution/insights/', views.execution_insights_partial, name='execution_insights_partial'),
    path('execution/identity/', views.execution_identity_partial, name='execution_identity_partial'),
    path('execution/audit/', views.execution_audit_partial, name='execution_audit_partial'),
    
    # APIs
    path('api/execution/scan/<uuid:session_id>/', views.api_process_scan, name='api_process_scan'),
    path('api/execution/control/<uuid:execution_id>/<str:action>/', views.api_session_control, name='api_session_control'),
    path('api/execution/manual-drawer/<uuid:session_id>/', views.api_manual_marking_drawer, name='api_manual_marking_drawer'),
    path('api/execution/manual-mark/<uuid:session_id>/<uuid:student_id>/', views.api_manual_mark_execute, name='api_manual_mark_execute'),
]
