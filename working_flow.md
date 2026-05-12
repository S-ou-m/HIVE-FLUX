# ⚙️ Hiveflux: Operational Working Flow
### The Lifecycle of Institutional Orchestration

This document outlines the detailed working principles of the **Hiveflux**, explaining how data flows through the system to transform static institutional management into real-time operational intelligence.

---

## 🏗️ 1. Institutional Foundation (Onboarding)
Every college starts as a blank tenant. The flow begins with the initialization of the core academic and administrative hierarchy:
1.  **Multi-Tenancy Setup**: A `College` entity is created, serving as the master container.
2.  **Academic Architecture**: Administrators define `Departments`, `Programs`, and `Semesters`.
3.  **Knowledge Mapping**: `Subjects` are created and sequenced into Semesters with specific Credit weights.
4.  **Resource Allocation**: Physical `Rooms` (Classrooms/Labs) are registered with GPS coordinates and capacity limits.

---

## 🛡️ 2. Identity & Trust Layer (Presence Governance)
Before any operation can occur, the system establishes a secure identity perimeter:
1.  **User Provisioning**: Faculty and Students are registered as `Users` with specific `Roles`.
2.  **Device Fingerprinting**: Users must register `TrustedDevices`. The system fingerprints the hardware ID and browser signature.
3.  **Identity Pairing**: Every login generates an `IdentitySession`, linking a User to a specific Device with a dynamic `Trust Score`.
4.  **Dynamic Verification**: Users use the **Identity Command Surface** (QR-based) to verify their presence at `ScanTerminals`.

---

## 📅 3. Academic Orchestration (Timetable -> Sessions)
The core "Heartbeat" of the institution is the Timetable Orchestrator:
1.  **Subject Assignment**: Admin links a Faculty member to a Subject (e.g., "Dr. Smith" teaches "DBMS").
2.  **Timetable Design**: The Orchestrator grid allows Admin to drag-and-drop these assignments into temporal slots (e.g., Monday 9 AM in Room 201).
3.  **Slot instantiation**: Every `TimetableSlot` is a recurring rule. The system realizes these into daily `TimetableSlotInstance` records.
4.  **Session Lifecycle**: 
    - **Ready**: A session is queued for execution.
    - **Live**: When the scheduled time hits, the session becomes "Live".
    - **Execution**: Faculty marks attendance manually or students use QR-Check-in.
    - **Completed**: The session is audited and the state is frozen for analytics.

---

## 💰 4. Financial Integrity (Revenue & Expenditure)
The system maintains a deterministic dual-ledger for all financial events:
1.  **Fee Invoicing**: Based on `FeeStructure`, the system auto-generates `Invoices` for students every semester.
2.  **Payment Processing**: Students pay via various modes (UPI/Bank/Cash). Each `Payment` is reconciled against its `Invoice`, updating the `credit_balance`.
3.  **Payroll Orchestration**: 
    - Faculty `SalaryProfiles` are configured with Allowance/Deduction components.
    - Monthly `PayrollRunBatches` process thousands of records simultaneously.
    - `Payslips` are generated as audit-ready PDF artifacts.

---

## 🚀 5. Success OS (The Intelligence Layer)
Raw data from attendance, grades, and finance is piped into the Success Intelligence engine:
1.  **Telemetry Bus**: Every scan, grade update, or payment event is logged as an `OperationalEvent`.
2.  **Signal Processing**: Engines analyze these events to detect `SuccessSignals` (e.g., "80% Attendance Drop in 1 Week" -> Critical Warning).
3.  **Proactive Nudging**: The system generates `SystemRecommendations` (e.g., "Revision recommended for Student X in Subject Y").
4.  **Human Intervention**: At-risk students are automatically flagged for `SupportCases`, assigned to Mentors for personalized recovery.

---

## 📊 6. Technology Philosophy
- **HTMX Execution**: Zero-latency dashboard experience with partial page updates.
- **SaaS Aesthetics**: High-fidelity, dark-mode-first design system with premium typography and glassmorphism.
- **Data Integrity**: Soft-delete patterns (`is_deleted`) and optimistic locking for high-concurrency operations.
