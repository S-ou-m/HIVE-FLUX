# 👨‍🏫 Faculty Module: Operational Execution Surface
### Academic Delivery & Presence Intelligence

The **Faculty Module** is the high-fidelity operational command surface for the academic staff. It transforms the institutional blueprint into realized academic sessions, focusing on deterministic attendance marking, session execution, and proactive student mentorship. By providing faculty with real-time telemetry and professional transparency, the module ensures that academic delivery is both measurable and high-impact.

---

## 🚀 1. Key Features

### 📡 Session Execution Hub (The Command Center)
The Faculty Module features a specialized **Session Execution Hub**, where educators manage the "Live" lifecycle of their classes. Unlike traditional systems where attendance is a post-class chore, this hub allows faculty to "Initialize" a session, triggering a dynamic, rotating QR code for student check-ins. Faculty can monitor a live "Scan Counter" that updates in real-time via WebSockets as students enter the room. This ensures that attendance is a verified, non-repudiable presence event rather than a static list of names.

### 🧠 Student Success & Mentorship Intelligence
Integrated directly into the **Success OS**, faculty members act as the primary agents for institutional recovery. They have access to a **Success Signal Dashboard** for their assigned mentees, where the system flags "At-Risk" behaviors such as attendance decay or academic volatility. Faculty can initiate `SupportCases` and document interventions, transforming their role from mere lecturers to data-driven success coaches. This layer ensures that the faculty is always proactive in driving student retention and performance.

### 📊 Professional Workload & Transparency
The module provides faculty with absolute transparency regarding their professional standing and institutional contributions. The **Workload Telemetry** section provides a surgical breakdown of completed sessions, missed classes, and extra academic loads. Furthermore, faculty can access their **Financial Profile**, viewing their salary structures and downloading audit-ready payslips. This transparency fosters a high-trust environment by ensuring that every academic action is accurately reflected in their professional record.

### 🛡️ Institutional Identity & Security Hub
Faculty members maintain their own **Identity Perimeter** within the module. They manage their `TrustedDevices`, ensuring that institutional actions (like marking attendance or accessing student records) are only performed from authorized hardware. The module also generates their **Rotating Identity Token**, allowing them to verify their own presence at institutional `ScanTerminals` (Gates, Labs, Offices), maintaining a continuous and verified presence session throughout the campus.

---

## 🔄 2. Detailed Faculty Workflow

### Phase 1: Daily Preparation & Orchestration
Upon logging in, the faculty member is presented with their **Academic Agenda**. This dashboard prioritizes today's sessions and highlights any pending attendance audits from previous days. The system provides a quick-view of room assignments and student enrollment counts, allowing the educator to prepare for the day's delivery with total situational awareness.

### Phase 2: Live Session Execution
At the scheduled class time, the faculty member "Initializes" the session through the Command Hub. This action transitions the `TimetableSlotInstance` from `READY` to `LIVE`. The system then begins generating rotating QR tokens on the faculty's screen. As students scan, the faculty monitors the live telemetry. In cases where a student lacks a device, the faculty can use a manual "Override" to mark presence, ensuring the attendance log remains 100% accurate.

### Phase 3: Post-Session Audit & Lock
Once the class concludes, the faculty member "Ends" the session, which triggers an automated audit of the scan logs. They review the list of present and absent students, making any final surgical adjustments. By "Locking" the session, the faculty member freezes the state, converting the live session into a deterministic institutional record that then feeds into the student success engines and workload analytics.

### Phase 4: Proactive Mentorship & Recovery
Beyond the classroom, faculty members monitor the **Success Intelligence** layer. They review the signals for their assigned mentees, identifying students who are trending toward academic risk. They record "Mentorship Notes" and manage the lifecycle of interventions, ensuring that every at-risk student has a documented path toward recovery.

### Phase 5: Professional Admin & Growth
Faculty use the module to track their own professional progression. They review their monthly workload metrics to ensure alignment with institutional goals. They also access the **Compensation Drawer** to review salary components and tax deductions, ensuring that their institutional commitment is matched by financial transparency and accurate payroll processing.

---

## 🛠️ 3. Faculty Tech Stack

- **Backend Logic**: **Django 6.0.4** utilizing optimized ORM queries for real-time workload and student telemetry.
- **Zero-Latency Interaction**: **HTMX 1.9.11** powers the session command hub, allowing for "Live" attendance marking and session state transitions without page reloads.
- **Real-time Telemetry**: **Django Channels + WebSockets** (Daphne) deliver the "Live Scan Counter," providing instant visual feedback as students scan into the classroom.
- **Security Engineering**: **Device Fingerprinting** and **Rotating UUID Nonces** for the faculty's own campus identity and session QR generation.
- **Visual Analytics**: **Chart.js** for displaying faculty-specific performance metrics and mentee success trends.

---

## 📐 4. Integrated Database Models

The Faculty module utilizes a cross-section of institutional data to power its execution-focused surfaces:

| Domain | Integrated Models | Functional Role |
| :--- | :--- | :--- |
| **Identity** | `Faculty`, `User`, `TrustedDevice` | Professional Profile & Security Anchor |
| **Operations** | `TimetableSlotInstance`, `AttendanceSession`, `Attendance` | The Session Execution Engine |
| **Academics** | `SubjectAssignment`, `Subject`, `Semester` | Academic Load & Curriculum Mapping |
| **Intelligence** | `SuccessSignal`, `SupportCase`, `Intervention` | Mentorship & Success Orchestration |
| **Finance** | `SalaryProfile`, `Payroll`, `Payslip` | Compensation Transparency & Payroll Audit |
| **Audit** | `FacultyWorklog`, `OperationsActivityLog` | Performance Tracking & Audit Trail |
