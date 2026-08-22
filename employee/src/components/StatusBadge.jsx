import React from "react";

const STATUS_CLASS_MAP = {
  PENDING: "badge badge-pending",
  APPROVED: "badge badge-approved",
  ACTIVE: "badge badge-approved",
  REJECTED: "badge badge-rejected",
  DISABLED: "badge badge-rejected",
  // Additional statuses used by the demo-data ERP modules (Tasks,
  // Attendance, Leave, Payslips) — purely additive, existing keys above
  // are unchanged.
  IN_PROGRESS: "badge badge-pending",
  DONE: "badge badge-approved",
  COMPLETED: "badge badge-approved",
  PRESENT: "badge badge-approved",
  ABSENT: "badge badge-rejected",
  LATE: "badge badge-pending",
  LEAVE: "badge badge-neutral",
  PAID: "badge badge-approved",
};

export default function StatusBadge({ status }) {
  const cls = STATUS_CLASS_MAP[status] || "badge badge-neutral";
  return <span className={cls}>{status}</span>;
}
