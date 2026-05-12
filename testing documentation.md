# 🧪 Testing Documentation: Hiveflux
## Deterministic Verification & Validation Framework

This document outlines the multi-layered testing strategy for the **Hiveflux**. Given the high-fidelity nature of the institutional orchestration, the testing framework focuses on **State Integrity**, **Temporal Accuracy**, and **Deterministic Intelligence**.

---

## 🛡️ 1. Testing Philosophy
Our strategy moves beyond simple CRUD verification to **Operational Determinism**:
- **Atomic Validation**: Every state transition (e.g., Session Ready → Live) must be verified for atomicity.
- **Signal Integrity**: Automated verification of Success Signals derived from raw telemetry.
- **Zero-Latency UX Audit**: Manual and automated checks for HTMX partial rendering performance.

---

## 🤖 2. Automated Testing Suite

### 2.1 Unit Testing (Calculation Engines)
Focuses on pure logic isolated from the database where possible.
- **Payroll Logic**: Verifying complex allowance/deduction math across various tax regimes.
- **Success Score Algorithm**: Testing the weighted signal processing for student risk levels.
- **Time Intelligence**: Validating slot conflict detection logic (Overlapping Faculty/Rooms).

### 2.2 Integration Testing (HTMX & Partial Flows)
Ensures that the server-driven partials interact correctly with the frontend.
- **Partial Rendering**: Verifying that HTMX endpoints return valid HTML fragments with correct OOB (Out-of-Band) triggers.
- **State Synchronization**: Testing if deleting a slot in the grid correctly updates the OOB Toast and refreshes the parent fragment.
- **Identity Handshake**: Simulating the QR-rotation nonce validation between terminal and server.

### 2.3 End-to-End (E2E) Testing
Full-stack browser automation focusing on critical user journeys.
- **The Orchestration Loop**: Admin creates Timetable → Faculty enters Live Session → Attendance is marked → Success Signal is generated.
- **The Financial Chain**: Invoice generation → Payment Recording → Ledger Update → Payroll Run.

---

## 🖱️ 3. Manual Verification Framework

### 3.1 High-Fidelity UI/UX Audit
Manual inspection of the "SaaS Grade" visual layer:
- **Responsive Layouts**: Verifying the Timetable Orchestrator across desktop and mobile viewports.
- **Motion & Kinetic Signals**: Auditing the smoothness of animations and real-time state updates.
- **Dark Mode Integrity**: Ensuring high contrast and institutional color consistency across all 150+ views.

### 3.2 Hardware/Terminal Simulation
Manual verification of physical interaction points:
- **QR Scanning Edge Cases**: Testing expired tokens, duplicate scans, and unauthorized device attempts.
- **Terminal Heartbeats**: Simulating terminal disconnects and verifying system degradation behavior.

---

## 📋 4. Test Case Matrix (Core Modules)

| Module | Test Case ID | Description | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **Identity** | TC-ID-01 | QR Token Rotation | Token must expire in 60s; new token must be valid instantly. |
| **Identity** | TC-ID-02 | Device Binding | Authenticated session must fail if accessed from a non-trusted browser signature. |
| **Operations** | TC-OP-01 | Slot Allocation | Dragging a slot to a conflicted room must trigger an error toast and block save. |
| **Operations** | TC-OP-02 | Session Transition | A "Ready" session must auto-transition to "Live" exactly at the scheduled timestamp. |
| **Finance** | TC-FN-01 | Payroll Accuracy | Net salary must match (Gross - Deductions) precisely to 2 decimal places. |
| **Intelligence** | TC-IQ-01 | Signal Decay | 3 consecutive missed classes must trigger a "High Risk" signal for the student. |

---

## 📊 5. Performance & Stress Testing
- **Concurrency**: Simulating 1,000+ simultaneous QR scans during peak "Session Start" window.
- **Batch Processing**: Stress-testing the Payroll engine with 5,000+ faculty records to measure processing time (Target: < 30s).
- **Latency Monitoring**: Every HTMX request is monitored to ensure the server response time remains under **100ms**.

---

## 🧠 6. Observability & Audit
Testing failures are analyzed through:
1.  **OperationsActivityLog**: Every administrative action is traceable to a user/timestamp.
2.  **ExplanationTrace**: Every intelligence-driven state change provides a "Reasoning Log" for manual audit.
3.  **Audit Snapshots**: Financial records are compared against frozen snapshots to detect data tampering or unauthorized state changes.
