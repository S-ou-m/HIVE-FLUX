# 📂 Code File Details: Hiveflux
### Surgical Mapping of Files, Features, and Institutional Roles

This document provides an exhaustive, directory-by-directory breakdown of every major code file within the **Hiveflux**. It defines the specific functional role and features handled by each file, creating a deterministic map for institutional maintenance and auditing.

---

## 🏛️ 1. Global Configuration (`college_erp/`)
The foundational orchestration layer for the entire platform.

| File Name | Role & Features |
| :--- | :--- |
| **`settings.py`** | **Master System Config**: Manages DB engines, security middleware, Celery broker URLs, and the multi-tenant `TenantMiddleware` registration. |
| **`urls.py`** | **Root Routing Table**: The primary entry point for all institutional requests, delegating traffic to specific application modules. |
| **`asgi.py`** | **Asynchronous Gateway**: Configures the **Daphne** server to handle high-concurrency WebSocket telemetry and standard HTTP traffic. |
| **`wsgi.py`** | **Standard Web Gateway**: Handles traditional synchronous request-response cycles for the platform. |

---

## 🛡️ 2. Identity & Accounts (`accounts/`)
Governing the security perimeter and personalized dashboard surfaces.

| File Name | Role & Features |
| :--- | :--- |
| **`models.py`** | **Identity Schema**: Defines the custom `User` model, `Faculty`/`Student` profiles, and non-repudiable `TrustedDevice` fingerprinting. |
| **`views.py`** | **Authentication Logic**: Manages multi-role login flows and institutional redirect rules. |
| **`dashboard_views.py`** | **Core Admin/Faculty Engine**: Hydrates the high-density command surfaces for administrators and faculty staff. |
| **`student_dashboard_views.py`** | **Success OS Engine**: Manages the student-facing identity hub, career intelligence, and academic telemetry views. |

---

## 🚀 3. Operational Execution (`operations/`)
The engine that transforms timetables into real-time session telemetry.

| File Name | Role & Features |
| :--- | :--- |
| **`models.py`** | **Session Schema**: Defines Timetable slots, instances, and the `AttendanceSession` state machine. |
| **`views.py`** | **Execution Logic**: Manages the "Live" session lifecycle, scanner panels, and manual attendance overrides. |
| **`tasks.py`** | **Background Orchestration**: Periodic Celery tasks for realizing timetable slots into actionable daily instances. |
| **`consumers.py`** | **WebSocket Engine**: Real-time handling of student scans and live session counters. |
| **`signals.py`** | **Event Emitter**: Pushes real-time UI updates to dashboard layers when session states change. |

---

## 💰 4. Financial Integrity (`finance/`)
The dual-ledger system for institutional revenue and expenditure.

| File Name | Role & Features |
| :--- | :--- |
| **`models.py`** | **Finance Schema**: Defines Fee Structures, Invoices, Payments, and audit-frozen Payroll breakdowns. |
| **`views.py`** | **Reconciliation Logic**: Manages payment processing, digital receipts, and payroll run orchestration. |
| **`tasks.py`** | **Batch Financial Processing**: Handles high-volume payroll calculations and invoice generation in the background. |

---

## 📅 5. Academics & Admissions (`academics/` & `admissions/`)
The blueprint of institutional knowledge and student onboarding.

| File Name | Role & Features |
| :--- | :--- |
| **`academics/models.py`** | **Curriculum Schema**: Maps Departments, Programs, Semesters, and SubjectSequences. |
| **`academics/views.py`** | **Enrollment Logic**: Manages the mapping of students to subjects and semesters. |
| **`admissions/views.py`** | **Onboarding Wizard**: A 5-step SaaS-grade flow for institutional registration and document verification. |

---

## 🧠 6. Intelligence & LMS (`lms/` & `brain/`)
Derived success signals and pedagogical telemetry.

| File Name | Role & Features |
| :--- | :--- |
| **`lms/models.py`** | **Pedagogical Signals**: Tracks learning signals, fraud detection in assignments, and skill rubrics. |
| **`core/models.py`** | **Institutional Anchors**: Defines the `College` tenant model and the `BaseModel` for UUID persistence. |

---

## 🎨 7. Frontend Layer (`Frontend/`)
The high-fidelity UI surfaces and design systems.

| File Name | Role & Features |
| :--- | :--- |
| **`static/css/dashboard_system.css`** | **Admin UI Skin**: Professional dark-mode and glassmorphism design tokens. |
| **`static/css/faculty_design_system.css`** | **Faculty UI Skin**: High-density operational styles for classroom execution. |
| **`static/js/main.js`** | **Global Interactivity**: HTMX error handling, WebSocket sync, and kinetic animation logic. |
| **`templates/base.html`** | **Master Shell**: The primary HTML orchestrator containing HTMX and WebSocket initialization. |

---

## 🛠️ 8. Institutional Tools & Scripts (Root)
Automated engines for data seeding, debugging, and system integrity.

| File Name | Role & Features |
| :--- | :--- |
| **`seed_db.py`** | **Global Seeder**: Initializing the entire database with a verified institutional skeleton. |
| **`seed_student_os.py`** | **Identity Seeder**: Generating thousands of high-fidelity student identity sessions and telemetry. |
| **`seed_payroll_defaults.py`** | **Finance Seeder**: Initializing institutional salary components and tax regimes. |
| **`debug_advance.py`** | **Operational Debugger**: Specialized tool for tracing state machine failures in the execution engine. |
| **`clear_data.py`** | **Surgical Purge**: Tool for cleaning specific data domains while preserving the core institutional anchor. |
| **`test_service.py`** | **Internal Health-Check**: Automated script for verifying the connectivity of Redis, Celery, and WebSockets. |
