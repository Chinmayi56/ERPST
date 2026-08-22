/**
 * Placeholder data for Employee Portal modules that don't have a backend
 * API yet (Tasks, Projects, Clients, Attendance, Leave, Documents,
 * Payslips). Dashboard.jsx and My Tasks/My Projects/etc. all read from this
 * single file so the numbers shown on the Dashboard summary always match
 * the numbers shown on each module's own page.
 *
 * This is intentionally NOT wired to the backend/MongoDB — these modules
 * have no real API yet (see routes/employee_portal.py, which only exposes
 * /dashboard, /profile and /notifications). When real endpoints exist for
 * these modules, replace the constants below with API calls the same way
 * Dashboard.jsx already does for real data (see api/portal.js) — the page
 * components themselves would not need to change, only where the data
 * comes from.
 */

export const myTasks = [
  { id: "TSK-101", title: "Prepare Q3 client presentation", project: "Atlas CRM Revamp", priority: "High", status: "IN_PROGRESS", due_date: "2026-08-22" },
  { id: "TSK-102", title: "Fix invoice PDF export bug", project: "Orion Billing Portal", priority: "High", status: "PENDING", due_date: "2026-08-20" },
  { id: "TSK-103", title: "Code review for auth module", project: "Atlas CRM Revamp", priority: "Medium", status: "PENDING", due_date: "2026-08-25" },
  { id: "TSK-104", title: "Update onboarding documentation", project: "Internal Tools", priority: "Low", status: "DONE", due_date: "2026-08-12" },
  { id: "TSK-105", title: "Sprint planning notes", project: "Orion Billing Portal", priority: "Medium", status: "DONE", due_date: "2026-08-10" },
];

export const myProjects = [
  { id: "PRJ-01", name: "Atlas CRM Revamp", client: "Atlas Retail Pvt Ltd", role: "Backend Developer", status: "ACTIVE", deadline: "2026-10-15", progress: 62 },
  { id: "PRJ-02", name: "Orion Billing Portal", client: "Orion Logistics", role: "Full-stack Developer", status: "ACTIVE", deadline: "2026-09-05", progress: 40 },
  { id: "PRJ-03", name: "Internal Tools", client: "Strivenest Technologies", role: "Contributor", status: "ACTIVE", deadline: "Ongoing", progress: 85 },
  { id: "PRJ-04", name: "Nimbus Analytics Dashboard", client: "Nimbus Data Co.", role: "Developer", status: "COMPLETED", deadline: "2026-06-30", progress: 100 },
];

export const myClients = [
  { id: "CLT-01", name: "Atlas Retail Pvt Ltd", contact: "Rohan Mehta", email: "rohan.mehta@atlasretail.example", project: "Atlas CRM Revamp", status: "ACTIVE" },
  { id: "CLT-02", name: "Orion Logistics", contact: "Sara Iyer", email: "sara.iyer@orionlogistics.example", project: "Orion Billing Portal", status: "ACTIVE" },
  { id: "CLT-03", name: "Nimbus Data Co.", contact: "David Chen", email: "david.chen@nimbusdata.example", project: "Nimbus Analytics Dashboard", status: "COMPLETED" },
];

export const attendanceSummary = {
  month: "August 2026",
  present_days: 13,
  absent_days: 1,
  leave_days: 1,
  late_days: 2,
  working_days: 15,
};

export const recentAttendance = [
  { date: "2026-08-19", check_in: "09:12 AM", check_out: "—", status: "PRESENT" },
  { date: "2026-08-18", check_in: "09:05 AM", check_out: "06:20 PM", status: "PRESENT" },
  { date: "2026-08-17", check_in: "09:40 AM", check_out: "06:05 PM", status: "LATE" },
  { date: "2026-08-16", check_in: "—", check_out: "—", status: "LEAVE" },
  { date: "2026-08-15", check_in: "09:02 AM", check_out: "06:15 PM", status: "PRESENT" },
];

export const leaveBalance = {
  casual_leave: { total: 12, used: 4, remaining: 8 },
  sick_leave: { total: 10, used: 2, remaining: 8 },
  earned_leave: { total: 15, used: 6, remaining: 9 },
};

export const leaveRequests = [
  { id: "LV-201", type: "Casual Leave", from: "2026-08-16", to: "2026-08-16", days: 1, status: "APPROVED" },
  { id: "LV-202", type: "Sick Leave", from: "2026-07-28", to: "2026-07-29", days: 2, status: "APPROVED" },
  { id: "LV-203", type: "Earned Leave", from: "2026-09-01", to: "2026-09-03", days: 3, status: "PENDING" },
];

export const myDocuments = [
  { id: "DOC-01", name: "Offer Letter.pdf", type: "Offer Letter", uploaded_date: "2026-06-01", status: "APPROVED" },
  { id: "DOC-02", name: "PAN Card.pdf", type: "ID Proof", uploaded_date: "2026-06-01", status: "APPROVED" },
  { id: "DOC-03", name: "Experience Certificate.pdf", type: "Certificate", uploaded_date: "2026-06-02", status: "APPROVED" },
  { id: "DOC-04", name: "Address Proof.pdf", type: "ID Proof", uploaded_date: "2026-06-02", status: "PENDING" },
];

export const payslips = [
  { id: "PS-2026-07", month: "July 2026", gross: 75000, deductions: 9800, net: 65200, status: "PAID" },
  { id: "PS-2026-06", month: "June 2026", gross: 75000, deductions: 9800, net: 65200, status: "PAID" },
  { id: "PS-2026-05", month: "May 2026", gross: 72000, deductions: 9400, net: 62600, status: "PAID" },
];
