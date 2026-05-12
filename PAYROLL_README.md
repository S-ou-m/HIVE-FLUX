# 💎 Dynamic Compensation & Payroll Engine
**Enterprise-Grade Financial Micro-System for Modern ERPs**

## 📖 Overview
The Dynamic Compensation Engine is a modular, multi-tenant payroll system designed for scalable educational institutions. It moves away from static, hardcoded salary fields toward a **Rules-Based Calculation Engine** that ensures financial precision, historical integrity, and administrative efficiency.

## 💡 Why This Engine Matters
- **Eliminates Manual Errors**: Automated multi-pass calculations remove the risk of human error in complex salary structures.
- **Scalable Structures**: Supports unlimited components and templates, allowing the system to grow with the institution.
- **Audit Compliance**: Strict lifecycle management and snapshots provide a clear audit trail for financial regulators.
- **Cost Transparency**: Provides full visibility into the **Cost-to-Company (CTC)**, enabling better budget planning.

---

## 🏗️ Core Features

### 1. Modular Component Architecture
Instead of fixed fields, the system uses a **Component-Based Model**:
- **Earnings/Allowances**: HRA, Medical, Travel, Performance Bonuses, etc.
- **Deductions**: Professional Tax, Provident Fund (PF), Income Tax, etc.
- **Impact Types**: Distinguishes between **Net Pay** (Employee Payout) vs. **Employer Contributions** (CTC Impact only).

### 2. Intelligent Salary Templates
- Create blueprints for different roles (e.g., "HOD", "Assistant Professor").
- Templates are "snapshotted" onto Faculty Profiles, ensuring that global template changes do not retroactively alter past payroll records.

### 3. Historical Integrity
- Effective-from/to dating allows for seamless salary revisions.
- Tracks salary evolution for every employee over their entire tenure.

---

## 🔄 Payroll Data Flow
1. **Definition**: Admin defines global **Salary Components**.
2. **Blueprinting**: Components are grouped into **Salary Templates**.
3. **Assignment**: Templates are applied to **Faculty**, creating a unique **Salary Profile**.
4. **Execution**: The `CompensationEngine` processes profiles for a specific month.
5. **Review**: Payroll is generated in a **DRAFT** state for administrative check.
6. **Finalization**: Admin approves and moves records to **LOCKED** status (Data Frozen).
7. **Disbursement**: Payments are recorded, moving status to **PAID**, and payslips are dispatched.

---

## ⚙️ Calculation Engine Overview
The `CompensationEngine` service processes components using a prioritized, multi-pass logic:
1. **Initialization**: Base Salary is retrieved from the Profile.
2. **Pass 1 (Allowances)**: Earnings are calculated based on scope (**BASE** or **GROSS**) and added to the gross.
3. **Pass 2 (Deductions)**: Deductions are computed (scoped to Base or Gross) and subtracted from the net.
4. **Pass 3 (CTC Logic)**: Employer-specific contributions (e.g., Employer PF) are added to compute total **CTC**.
5. **Finalization**: Rounding logic is applied, and negative net pay is automatically floored to ₹0.

---

## 🖥️ UI/UX Layer
- **Salary Setup Drawer**: A high-fidelity sliding panel for real-time configuration.
- **Live Preview Sidebar**: Powered by **HTMX**, this sidebar provides instant feedback on Net Pay and CTC as admins adjust values.
- **Responsive Viewer**: Mobile-first payslip previewer for faculty access on any device.

---

## 🔐 Security & Multi-Tenancy
- **Strict Data Isolation**: All payroll data is strictly scoped to the `College` (Tenant), ensuring zero cross-tenant data leakage.
- **Role-Based Access (RBAC)**:
    - **Admin**: Full system configuration and template management.
    - **Finance**: Execution, approval, and disbursement.
    - **Faculty**: Read-only access to their own payslips.
- **Audit Logging**: Every state change (Draft → Locked → Paid) is logged with a timestamp and the initiating user.

---

## ⚠️ Edge Case Handling
- **Missing Profiles**: Automatically flagged and skipped during bulk runs with a detailed warning.
- **Pro-rata Calculation**: Integrated support for mid-month joinees or exits.
- **Negative Net Pay**: System safeguards prevent negative payouts; net pay is floored to zero with a warning flag.

---

## 🛠️ Technical Stack
- **Backend**: Django (Python 3.14)
- **Calculation Logic**: Custom `CompensationEngine` Python service.
- **Frontend Interactivity**: HTMX for real-time setup feedback.
- **Document Rendering**: `xhtml2pdf` for server-side PDF generation.

---

## 🔌 Extensibility
The engine is architected for future integrations:
- **REST APIs**: Future endpoints for external payroll automation.
- **Attendance Integration**: Plug-and-play logic for leave-based deductions.
- **Accounting Bridges**: Exportable data formats for Tally and QuickBooks.

---

## 🛣️ Roadmap
- [ ] **Tax Slab Engine**: Country-specific automated tax calculations.
- [ ] **Bulk Execution**: One-click payroll generation for thousands of employees.
- [ ] **Employee Self-Service**: Portal for faculty to download history and tax documents.
- [ ] **Bonus/Incentive Module**: Automated ad-hoc payout triggers.

---

