"""
URL configuration for college_erp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.http import HttpResponse
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from accounts.views import login_view, logout_view
from accounts import dashboard_views, finance_views, student_dashboard_views
from communication import views as communication_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', login_view, name='login'),
    path('', login_view, name='login_root'),
    path('logout/', logout_view, name='logout'),
    
    # Dashboard Routes
    path('dashboard/admin/', dashboard_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/overview/', dashboard_views.admin_dashboard, name='admin_dashboard_overview'),
    path('dashboard/admin/academics/', dashboard_views.admin_dashboard, name='admin_dashboard_academics'),
    path('dashboard/admin/students/', dashboard_views.admin_dashboard, name='admin_dashboard_students'),
    path('dashboard/admin/faculty/', dashboard_views.admin_dashboard, name='admin_dashboard_faculty'),
    path('dashboard/admin/finance/', dashboard_views.admin_dashboard, name='admin_dashboard_finance'),
    path('dashboard/admin/timetable/', dashboard_views.admin_dashboard, name='admin_dashboard_timetable'),
    
    # Faculty Module
    path('dashboard/faculty/partial/identity-hub/', dashboard_views.faculty_identity_hub_partial, name='faculty_identity_hub_partial'),
    path('dashboard/faculty/partial/profile/', dashboard_views.faculty_profile_dashboard_partial, name='faculty_profile_dashboard_partial'),
    path('dashboard/faculty/partial/profile/kpi/', dashboard_views.faculty_profile_kpi_partial, name='faculty_profile_kpi_partial'),
    path('dashboard/faculty/partial/profile/analytics/', dashboard_views.faculty_profile_analytics_partial, name='faculty_profile_analytics_partial'),
    path('dashboard/faculty/partial/profile/insights/', dashboard_views.faculty_profile_insights_partial, name='faculty_profile_insights_partial'),
    path('dashboard/faculty/partial/profile/activity/', dashboard_views.faculty_profile_activity_partial, name='faculty_profile_activity_partial'),
    path('dashboard/faculty/partial/profile/settings/', dashboard_views.faculty_profile_settings_partial, name='faculty_profile_settings_partial'),
    path('dashboard/faculty/partial/overview/', dashboard_views.faculty_overview_partial, name='faculty_overview_partial'),
    path('dashboard/faculty/attendance/', dashboard_views.faculty_attendance_dashboard, name='faculty_attendance_dashboard'),
    path('dashboard/faculty/partial/performance/', dashboard_views.faculty_performance_partial, name='faculty_performance_partial'),
    path('dashboard/admin/partial/timetable/', dashboard_views.admin_timetable_management, name='admin_timetable_management'),
    path('dashboard/admin/partial/timetable/create/', dashboard_views.admin_timetable_create, name='admin_timetable_create'),
    path('dashboard/admin/partial/timetable/generate/', dashboard_views.admin_timetable_generate, name='admin_timetable_generate'),
    path('dashboard/admin/partial/timetable/export/', dashboard_views.admin_timetable_export, name='admin_timetable_export'),
    path('dashboard/admin/partial/timetable/import/', dashboard_views.admin_timetable_import, name='admin_timetable_import'),
    
    # 📊 KPI Drill-down Routes
    path('dashboard/admin/partial/timetable/class-directory/', dashboard_views.admin_timetable_class_directory, name='admin_timetable_class_directory'),
    path('dashboard/admin/partial/timetable/utilization/', dashboard_views.admin_timetable_utilization, name='admin_timetable_utilization'),
    path('dashboard/admin/partial/timetable/faculty-availability/', dashboard_views.admin_timetable_faculty_availability, name='admin_timetable_faculty_availability'),
    path('dashboard/admin/partial/timetable/room-occupancy/', dashboard_views.admin_timetable_room_occupancy, name='admin_timetable_room_occupancy'),
    path('dashboard/admin/partial/timetable/live-monitor/', dashboard_views.admin_timetable_live_monitor, name='admin_timetable_live_monitor'),
    path('dashboard/admin/partial/timetable/slot-optimization/', dashboard_views.admin_timetable_slot_optimization, name='admin_timetable_slot_optimization'),
    path('dashboard/admin/partial/timetable/drilldown/content/', dashboard_views.admin_timetable_drilldown_content_action, name='admin_timetable_drilldown_content_action'),
    
    # 📅 Slot Orchestration
    path('dashboard/admin/partial/timetable/slot/add/', dashboard_views.admin_timetable_slot_add, name='admin_timetable_slot_add'),
    path('dashboard/admin/partial/timetable/slot/edit/', dashboard_views.admin_timetable_slot_edit, name='admin_timetable_slot_edit'),
    path('dashboard/admin/partial/timetable/slot/delete/', dashboard_views.admin_timetable_slot_delete, name='admin_timetable_slot_delete'),
    path('dashboard/faculty/partial/performance/kpi/<str:metric_type>/', dashboard_views.faculty_performance_kpi_detail, name='faculty_performance_kpi_detail'),
    path('dashboard/faculty/partial/attendance-logs/', dashboard_views.faculty_attendance_logs_partial, name='faculty_attendance_logs_partial'),
    path('dashboard/faculty/partial/earnings/', finance_views.faculty_earnings_partial, name='faculty_earnings_partial'),
    path('dashboard/faculty/partial/tax-documents/', dashboard_views.faculty_tax_documents_partial, name='faculty_tax_documents_partial'),
    path('dashboard/faculty/partial/notifications/', dashboard_views.faculty_notifications_partial, name='faculty_notifications_partial'),
    path('dashboard/faculty/partial/security/', dashboard_views.faculty_security_partial, name='faculty_security_partial'),
    path('dashboard/faculty/partial/payout/<int:payroll_id>/drawer/', finance_views.faculty_payout_details_drawer, name='faculty_payout_details_drawer'),
    path('dashboard/faculty/partial/evaluation/hub/', dashboard_views.faculty_assignment_review_hub, name='faculty_assignment_review_hub'),
    path('dashboard/faculty/partial/evaluation/review/<uuid:submission_id>/', dashboard_views.faculty_submission_review_mode, name='faculty_submission_review_mode'),
    path('dashboard/faculty/partial/evaluation/action/bulk-approve/', dashboard_views.faculty_evaluation_bulk_approve, name='faculty_evaluation_bulk_approve'),
    path('dashboard/faculty/attendance/scanner/launcher/', dashboard_views.faculty_attendance_scanner_launcher, name='faculty_attendance_scanner_launcher'),
    path('dashboard/faculty/attendance/scan/process/', dashboard_views.faculty_attendance_process_scan, name='faculty_attendance_process_scan'),
    path('dashboard/faculty/identity/digital-id/', dashboard_views.faculty_get_digital_id_partial, name='faculty_digital_id_partial'),
    path('dashboard/faculty/identity/refresh/', dashboard_views.faculty_refresh_identity_token, name='faculty_refresh_identity_token'),
    path('dashboard/faculty/ops-control/', dashboard_views.faculty_operations_control_partial, name='faculty_ops_control_partial'),
    
    path('dashboard/faculty/', dashboard_views.faculty_dashboard, name='faculty_dashboard'),
    path('dashboard/faculty/overview/', dashboard_views.faculty_dashboard, name='faculty_dashboard_overview'),
    path('dashboard/faculty/performance/', dashboard_views.faculty_dashboard, name='faculty_dashboard_performance'),
    path('dashboard/faculty/attendance/', dashboard_views.faculty_dashboard, name='faculty_dashboard_attendance'),
    path('dashboard/faculty/timetable/', dashboard_views.faculty_dashboard, name='faculty_dashboard_timetable'),
    path('dashboard/faculty/assignments/', dashboard_views.faculty_dashboard, name='faculty_dashboard_assignments'),
    path('dashboard/faculty/finance/', dashboard_views.faculty_dashboard, name='faculty_dashboard_finance'),
    # Student Success OS: Full Shell Deep-Linking
    path('dashboard/student/', student_dashboard_views.student_dashboard, name='student_dashboard'),
    path('dashboard/student/overview/', student_dashboard_views.student_dashboard, name='student_dashboard_overview'),
    path('dashboard/student/radar/', student_dashboard_views.student_dashboard, name='student_dashboard_radar'),
    path('dashboard/student/career/', student_dashboard_views.student_dashboard, name='student_dashboard_career'),
    path('dashboard/student/achievements/', student_dashboard_views.student_dashboard, name='student_dashboard_achievements'),
    path('dashboard/student/support/', student_dashboard_views.student_dashboard, name='student_dashboard_support'),
    path('dashboard/student/finance/', student_dashboard_views.student_dashboard, name='student_dashboard_finance'),
    path('dashboard/student/assignments/', student_dashboard_views.student_dashboard, name='student_dashboard_assignments'),
    path('dashboard/student/attendance-trend/', student_dashboard_views.student_dashboard, name='student_dashboard_attendance_trend'),

    # Student Success OS: HTMX Partials
    path('dashboard/student/partial/identity-command/', student_dashboard_views.student_identity_command_center, name='student_identity_command_center_partial_route'),
    path('dashboard/student/partial/overview/', student_dashboard_views.student_dashboard_overview_partial, name='student_dashboard_overview_partial'),
    path('dashboard/student/partial/identity-hub/', student_dashboard_views.student_identity_hub_partial, name='student_identity_hub_partial'),
    path('dashboard/student/partial/radar/', student_dashboard_views.student_academic_radar_partial, name='student_academic_radar_partial'),
    path('dashboard/student/partial/attendance-trend/', student_dashboard_views.student_attendance_trend_partial, name='student_attendance_trend_partial'),
    path('dashboard/student/partial/assignment-os/', student_dashboard_views.student_assignment_os_partial, name='student_assignment_os_partial'),
    path('dashboard/student/partial/assignment-workspace/<uuid:assignment_id>/', student_dashboard_views.student_assignment_workspace_partial, name='student_assignment_workspace_partial'),
    
    # 🧠 Intelligence OS: Advanced Partials
    path('dashboard/student/partial/confidence-breakdown/', student_dashboard_views.student_confidence_breakdown_partial, name='student_confidence_breakdown_partial'),
    path('dashboard/student/partial/daily-agenda/', student_dashboard_views.student_daily_agenda_partial, name='student_daily_agenda_partial'),
    path('dashboard/student/partial/risk-signals/', student_dashboard_views.student_risk_signals_partial, name='student_risk_signals_partial'),
    path('dashboard/student/partial/critical-banner/', student_dashboard_views.get_critical_banner, name='get_critical_banner'),
    path('dashboard/student/partial/assignment-selector/', student_dashboard_views.student_assignment_selector_partial, name='student_assignment_selector_partial'),
    path('dashboard/student/action/submit-assignment/<uuid:assignment_id>/', student_dashboard_views.student_submit_assignment, name='student_submit_assignment'),
    path('dashboard/student/partial/competency-heatmap/', student_dashboard_views.student_competency_heatmap_partial, name='student_competency_heatmap_partial'),
    path('dashboard/student/partial/achievement-tracker/', student_dashboard_views.student_achievement_tracker_partial, name='student_achievement_tracker_partial'),
    path('dashboard/student/partial/support-hub/', student_dashboard_views.student_support_hub_partial, name='student_support_hub_partial'),
    path('dashboard/student/partial/service-portal/<slug:service_slug>/', student_dashboard_views.student_service_portal_partial, name='student_service_portal_partial'),
    path('dashboard/student/action/service-request/<slug:service_slug>/', student_dashboard_views.student_initiate_service_request, name='student_initiate_service_request'),
    path('dashboard/student/action/view-ticket/<str:ticket_id>/', student_dashboard_views.student_view_ticket_status, name='student_view_ticket_status'),
    path('dashboard/student/action/add-to-roadmap/<slug:service_slug>/', student_dashboard_views.student_add_to_roadmap, name='student_add_to_roadmap'),
    path('dashboard/student/action/schedule-consultation/<slug:service_slug>/', student_dashboard_views.student_schedule_consultation, name='student_schedule_consultation'),
    path('dashboard/student/partial/finance-ledger/', student_dashboard_views.student_finance_ledger_partial, name='student_finance_ledger_partial'),
    path('dashboard/student/partial/career-radar/', student_dashboard_views.student_career_radar_partial, name='student_career_radar_partial'),
    path('dashboard/student/partial/risk-signals/', student_dashboard_views.student_risk_signals_partial, name='student_risk_signals_partial'),
    path('dashboard/student/partial/rotate-pass/', student_dashboard_views.student_rotate_pass_partial, name='student_rotate_pass_partial'),
    path('dashboard/student/partial/payment-checkout/', student_dashboard_views.student_payment_orchestration_partial, name='student_payment_orchestration_partial'),
    path('dashboard/student/partial/payment-method-intelligence/', student_dashboard_views.student_payment_method_intelligence_partial, name='student_payment_method_intelligence_partial'),
    path('dashboard/student/partial/verify-vpa/', student_dashboard_views.student_verify_vpa_partial, name='student_verify_vpa_partial'),
    path('dashboard/student/partial/define-goal/', student_dashboard_views.student_define_goal_partial, name='student_define_goal_partial'),
    path('dashboard/student/partial/goal-intelligence/<uuid:goal_id>/', student_dashboard_views.student_goal_intelligence_partial, name='student_goal_intelligence_partial'),
    path('dashboard/student/action/save-goal/', student_dashboard_views.student_save_goal, name='student_save_goal'),
    path('dashboard/student/action/update-goal/<uuid:goal_id>/', student_dashboard_views.student_update_goal_progress, name='student_update_goal_progress'),
    path('dashboard/student/action/process-payment/', student_dashboard_views.student_process_payment, name='student_process_payment'),
    path('dashboard/student/partial/resume-builder/', student_dashboard_views.student_resume_builder_partial, name='student_resume_builder_partial'),
    path('dashboard/student/partial/subject-intelligence/', student_dashboard_views.student_subject_intelligence_partial, name='student_subject_intelligence_partial'),

    # Student Success OS: Identity Actions
    path('dashboard/student/action/update-preferences/', student_dashboard_views.update_student_preferences, name='student_update_preferences'),
    path('dashboard/student/action/update-password/', student_dashboard_views.update_student_password, name='student_update_password'),
    path('dashboard/student/action/identity-freeze/', student_dashboard_views.execute_identity_freeze, name='student_identity_freeze'),
    path('dashboard/student/action/run-skill-audit/', student_dashboard_views.run_skill_audit, name='student_run_skill_audit'),
    path('dashboard/student/action/generate-resume-pdf/', student_dashboard_views.generate_resume_pdf, name='student_generate_resume_pdf'),
    path('dashboard/student/action/push-to-placement/', student_dashboard_views.push_to_placement, name='student_push_to_placement'),


    path('api/attendance/qr/', dashboard_views.get_attendance_qr, name='get_attendance_qr'),
    path('dashboard/admin/partial/profile/', dashboard_views.admin_profile_partial, name='admin_profile_partial'),
    path('dashboard/admin/partial/profile/edit/', dashboard_views.admin_profile_edit_partial, name='admin_profile_edit_partial'),
    path('dashboard/admin/partial/profile/password/', dashboard_views.admin_password_change_partial, name='admin_password_change_partial'),
    path('dashboard/admin/partial/profile/switch-tenant/', dashboard_views.admin_tenant_switch_partial, name='admin_tenant_switch_partial'),
    path('dashboard/admin/partial/profile/sessions/', dashboard_views.admin_sessions_partial, name='admin_sessions_partial'),
    
    # HTMX Partial Routes (No hard refresh)
    path('dashboard/admin/partial/overview/', dashboard_views.admin_overview_partial, name='admin_overview_partial'),
    path('dashboard/admin/partial/overview/hero/', dashboard_views.admin_overview_hero_partial, name='admin_overview_hero_partial'),
    path('dashboard/admin/partial/overview/analytics/', dashboard_views.admin_overview_analytics_partial, name='admin_overview_analytics_partial'),
    path('dashboard/admin/partial/overview/distribution/', dashboard_views.admin_overview_distribution_partial, name='admin_overview_distribution_partial'),
    path('dashboard/admin/partial/overview/intelligence/', dashboard_views.admin_overview_intelligence_partial, name='admin_overview_intelligence_partial'),
    path('dashboard/admin/partial/overview/intelligence/day/', dashboard_views.admin_day_intelligence_partial, name='admin_day_intelligence_partial'),
    path('dashboard/admin/partial/overview/insights/', dashboard_views.admin_overview_insights_partial, name='admin_overview_insights_partial'),
    
    # Academics Module
    path('dashboard/admin/partial/academics/', dashboard_views.admin_academics_partial, name='admin_academics_partial'),
    path('dashboard/admin/partial/academics/stats/', dashboard_views.admin_academics_stats_partial, name='admin_academics_stats_partial'),
    path('dashboard/admin/partial/academics/charts/', dashboard_views.admin_academics_charts_partial, name='admin_academics_charts_partial'),
    path('dashboard/admin/partial/academics/chart/data/', dashboard_views.admin_academics_chart_data, name='admin_academics_chart_data'),
    path('dashboard/admin/partial/academics/departments/', dashboard_views.admin_departments_partial, name='admin_departments_partial'),
    path('dashboard/admin/partial/academics/departments/create/', dashboard_views.admin_department_create, name='admin_department_create'),
    path('dashboard/admin/partial/academics/departments/<uuid:dept_id>/view/', dashboard_views.admin_department_view, name='admin_department_view'),
    path('dashboard/admin/partial/academics/departments/<uuid:dept_id>/edit/', dashboard_views.admin_department_edit, name='admin_department_edit'),
    path('dashboard/admin/partial/academics/departments/<uuid:dept_id>/delete/', dashboard_views.admin_department_delete, name='admin_department_delete'),
    path('dashboard/admin/partial/academics/departments/<uuid:dept_id>/export/', dashboard_views.admin_department_export, name='admin_department_export'),
    path('dashboard/admin/partial/academics/departments/<uuid:dept_id>/health/', dashboard_views.admin_department_health_audit, name='admin_department_health_audit'),
    path('dashboard/admin/partial/academics/programs/', dashboard_views.admin_programs_partial, name='admin_programs_partial'),
    path('dashboard/admin/partial/academics/programs/create/', dashboard_views.admin_program_create, name='admin_program_create'),
    path('dashboard/admin/partial/academics/programs/<uuid:program_id>/edit/', dashboard_views.admin_program_edit, name='admin_program_edit'),
    path('dashboard/admin/partial/academics/programs/<uuid:program_id>/delete/', dashboard_views.admin_program_delete, name='admin_program_delete'),
    path('dashboard/admin/partial/academics/semesters/', dashboard_views.admin_semesters_partial, name='admin_semesters_partial'),
    path('dashboard/admin/partial/academics/semesters/create/', dashboard_views.admin_semester_create, name='admin_semester_create'),
    path('dashboard/admin/partial/academics/semesters/<uuid:semester_id>/edit/', dashboard_views.admin_semester_edit, name='admin_semester_edit'),
    path('dashboard/admin/partial/academics/semesters/<uuid:semester_id>/delete/', dashboard_views.admin_semester_delete, name='admin_semester_delete'),
    path('dashboard/admin/partial/academics/subjects/', dashboard_views.admin_subjects_partial, name='admin_subjects_partial'),
    path('dashboard/admin/partial/academics/subjects/create/', dashboard_views.admin_subject_create, name='admin_subject_create'),
    path('dashboard/admin/partial/academics/subjects/<uuid:subject_id>/edit/', dashboard_views.admin_subject_edit, name='admin_subject_edit'),
    path('dashboard/admin/partial/academics/subjects/<uuid:subject_id>/delete/', dashboard_views.admin_subject_delete, name='admin_subject_delete'),
    
    # Student Module
    path('dashboard/admin/partial/students/', dashboard_views.admin_students_partial, name='admin_students_partial'),
    path('dashboard/admin/partial/students/stats/', dashboard_views.admin_students_stats_partial, name='admin_students_stats_partial'),
    path('dashboard/admin/partial/students/charts/', dashboard_views.admin_students_charts_partial, name='admin_students_charts_partial'),
    path('dashboard/admin/partial/students/chart/enrollment/', dashboard_views.admin_students_chart_enrollment, name='admin_students_chart_enrollment'),
    path('dashboard/admin/partial/students/chart/department/', dashboard_views.admin_students_chart_department, name='admin_students_chart_department'),
    path('dashboard/admin/partial/students/chart/semester/', dashboard_views.admin_students_chart_semester, name='admin_students_chart_semester'),
    path('dashboard/admin/partial/students/chart/finance/', dashboard_views.admin_students_chart_finance, name='admin_students_chart_finance'),
    path('dashboard/admin/student/create/', dashboard_views.admin_student_create, name='admin_student_create'),
    path('dashboard/admin/partial/students/<uuid:student_id>/edit/', dashboard_views.admin_student_edit, name='admin_student_edit'),
    path('dashboard/admin/partial/students/<uuid:student_id>/delete/', dashboard_views.admin_student_delete, name='admin_student_delete'),
    path('dashboard/admin/partial/academics/semesters/load/', dashboard_views.get_semesters_for_program, name='get_semesters_for_program'),

    # Faculty Module
    path('dashboard/admin/partial/faculty/', dashboard_views.admin_faculty_partial, name='admin_faculty_partial'),
    path('dashboard/admin/partial/faculty/stats/', dashboard_views.admin_faculty_stats_partial, name='admin_faculty_stats_partial'),
    path('dashboard/admin/partial/faculty/charts/', dashboard_views.admin_faculty_charts_partial, name='admin_faculty_charts_partial'),
    path('dashboard/admin/partial/faculty/chart/dept/', dashboard_views.admin_faculty_chart_dept, name='admin_faculty_chart_dept'),
    path('dashboard/admin/partial/faculty/chart/desig/', dashboard_views.admin_faculty_chart_desig, name='admin_faculty_chart_desig'),
    path('dashboard/admin/partial/faculty/directory/', dashboard_views.admin_faculty_directory_partial, name='admin_faculty_directory_partial'),
    path('dashboard/admin/partial/faculty/workload/', dashboard_views.admin_workload_partial, name='admin_workload_partial'),
    path('dashboard/admin/partial/faculty/workload/create/', dashboard_views.admin_workload_create, name='admin_workload_create'),
    path('dashboard/admin/partial/faculty/workload/<uuid:workload_id>/edit/', dashboard_views.admin_workload_edit, name='admin_workload_edit'),
    path('dashboard/admin/partial/faculty/workload/<uuid:workload_id>/delete/', dashboard_views.admin_workload_delete, name='admin_workload_delete'),
    
    # Faculty Intelligence Views
    path('dashboard/faculty/partial/workload/<uuid:workload_id>/detail/', dashboard_views.faculty_workload_detail_partial, name='faculty_workload_detail_partial'),
    path('dashboard/admin/partial/faculty/create/', dashboard_views.admin_faculty_create, name='admin_faculty_create'),
    path('dashboard/admin/partial/faculty/<uuid:faculty_id>/edit/', dashboard_views.admin_faculty_edit, name='admin_faculty_edit'),
    path('dashboard/admin/partial/faculty/<uuid:faculty_id>/delete/', dashboard_views.admin_faculty_delete, name='admin_faculty_delete'),
    
    # Faculty HTMX Partials

    
    # Communication & Notifications Module
    path('dashboard/', include('communication.urls')),
    
    # Operations & Attendance Module
    path('dashboard/operations/', include('operations.urls')),

    # Finance Module
    path('dashboard/admin/partial/finance/', finance_views.admin_finance_partial, name='admin_finance_partial'),
    path('dashboard/admin/partial/finance/stats/', finance_views.admin_finance_stats_partial, name='admin_finance_stats_partial'),
    path('dashboard/admin/partial/finance/chart/revenue/', finance_views.admin_finance_chart_revenue_trend, name='admin_finance_chart_revenue_trend'),
    path('dashboard/admin/partial/finance/chart/payment-modes/', finance_views.admin_finance_chart_payment_modes, name='admin_finance_chart_payment_modes'),
    path('dashboard/admin/partial/finance/chart/departments/', finance_views.admin_finance_chart_dept_revenue, name='admin_finance_chart_dept_revenue'),
    path('dashboard/admin/partial/finance/fees/', finance_views.admin_fee_setup_partial, name='admin_fee_setup_partial'),
    path('dashboard/admin/partial/finance/fees/create/', finance_views.admin_fee_create, name='admin_fee_create'),
    path('dashboard/admin/partial/finance/fees/<uuid:fee_id>/edit/', finance_views.admin_fee_edit, name='admin_fee_edit'),
    path('dashboard/admin/partial/finance/fees/<uuid:fee_id>/delete/', finance_views.admin_fee_delete, name='admin_fee_delete'),
    path('dashboard/admin/partial/finance/payments/', finance_views.admin_student_payments_partial, name='admin_student_payments_partial'),
    path('dashboard/admin/partial/finance/payments/batch-modal/', finance_views.admin_invoice_batch_modal, name='admin_invoice_batch_modal'),
    path('dashboard/admin/partial/finance/payments/batch-preview/', finance_views.admin_invoice_batch_preview, name='admin_invoice_batch_preview'),
    path('dashboard/admin/partial/finance/payments/batch-generate/', finance_views.admin_invoice_batch_generate, name='admin_invoice_batch_generate'),
    path('dashboard/admin/partial/finance/payments/record-global/', finance_views.admin_payment_global_modal, name='admin_payment_global_modal'),
    path('dashboard/admin/partial/finance/payments/search-students/', finance_views.admin_student_search, name='admin_student_search'),
    path('dashboard/admin/partial/finance/payments/get-context/<uuid:student_id>/', finance_views.admin_get_student_payment_context, name='admin_get_student_payment_context'),
    path('dashboard/admin/partial/finance/payments/get-ledger/<uuid:student_id>/', finance_views.admin_get_student_ledger_partial, name='admin_get_student_ledger_partial'),
    path('dashboard/admin/partial/finance/payments/get-invoices/<uuid:student_id>/', finance_views.admin_get_student_invoices_partial, name='admin_get_student_invoices_partial'),
    path('dashboard/admin/partial/finance/payments/advance/<uuid:student_id>/', finance_views.admin_advance_payment_modal, name='admin_advance_payment_modal'),
    path('dashboard/admin/partial/finance/payments/record-advance/<uuid:student_id>/', finance_views.admin_advance_payment_save, name='admin_advance_payment_save'),
    path('dashboard/admin/partial/finance/payments/<uuid:invoice_id>/record/', finance_views.admin_payment_record_modal, name='admin_payment_record_modal'),
    path('dashboard/admin/partial/finance/payments/<uuid:invoice_id>/save/', finance_views.admin_payment_record_save, name='admin_payment_record_save'),
    path('dashboard/admin/partial/finance/payroll/', finance_views.admin_payroll_partial, name='admin_payroll_partial'),
    path('dashboard/admin/partial/finance/payroll/preview/', finance_views.admin_payroll_preview, name='admin_payroll_preview'),
    path('dashboard/admin/partial/finance/payroll/run-modal/', finance_views.admin_payroll_run_modal, name='admin_payroll_run_modal'),
    path('dashboard/admin/partial/finance/payroll/run-execute/', finance_views.admin_payroll_run_execute, name='admin_payroll_run_execute'),
    path('dashboard/admin/partial/finance/payroll/<uuid:payroll_id>/breakdown/', finance_views.admin_payroll_breakdown, name='admin_payroll_breakdown'),
    path('dashboard/admin/partial/finance/payroll/<uuid:payroll_id>/payslip/', finance_views.admin_payroll_payslip_preview, name='admin_payroll_payslip_preview'),
    path('dashboard/admin/partial/finance/payroll/<uuid:payroll_id>/payslip/download/', finance_views.admin_payroll_payslip_download, name='admin_payroll_payslip_download'),
    path('dashboard/admin/partial/finance/payroll/<uuid:payroll_id>/payslip/email/', finance_views.admin_payroll_payslip_email, name='admin_payroll_payslip_email'),
    path('dashboard/admin/partial/finance/payroll/<uuid:payroll_id>/status/<str:status>/', finance_views.admin_payroll_update_status, name='admin_payroll_update_status'),
    path('dashboard/admin/partial/finance/payroll/bulk/', finance_views.admin_payroll_bulk_action, name='admin_payroll_bulk_action'),
    
    # SaaS Compensation
    path('dashboard/admin/partial/finance/salary/setup/<uuid:faculty_id>/', finance_views.admin_salary_setup_drawer, name='admin_salary_setup_drawer'),
    path('dashboard/admin/partial/finance/salary/setup/<uuid:faculty_id>/save/', finance_views.admin_salary_setup_save, name='admin_salary_setup_save'),
    path('dashboard/admin/partial/finance/salary/setup/<uuid:faculty_id>/add-component/', finance_views.admin_salary_setup_add_comp, name='admin_salary_setup_add_comp'),
    path('dashboard/admin/partial/finance/salary/setup/<uuid:faculty_id>/render-row/', finance_views.admin_salary_setup_render_comp_row, name='admin_salary_setup_render_comp_row'),
    path('dashboard/admin/partial/finance/salary/preview/<uuid:faculty_id>/', finance_views.admin_salary_preview_hx, name='admin_salary_preview_hx'),
    path('dashboard/admin/partial/finance/tax-regime/<uuid:regime_id>/details/', finance_views.admin_tax_regime_details, name='admin_tax_regime_details'),
    path('dashboard/admin/partial/finance/payroll/batch/<uuid:batch_id>/status/', finance_views.admin_payroll_batch_status, name='admin_payroll_batch_status'),
    path('dashboard/admin/finance/payroll/export/neft/<int:month>/<int:year>/', finance_views.admin_payroll_export_neft, name='admin_payroll_export_neft'),
    path('dashboard/admin/partial/finance/payroll/tds/summary/', finance_views.admin_payroll_tds_summary, name='admin_payroll_tds_summary'),
    path('favicon.ico', lambda x: HttpResponse(status=204)),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'Frontend' / 'static'}),
    ]
