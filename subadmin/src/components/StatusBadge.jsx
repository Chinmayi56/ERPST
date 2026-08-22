import React from "react";

const STATUS_CLASS_MAP = {
  PENDING: "badge badge-pending",
  APPROVED: "badge badge-approved",
  ACTIVE: "badge badge-approved",
  REJECTED: "badge badge-rejected",
  DISABLED: "badge badge-rejected",
  EXPIRED: "badge badge-neutral",
  USED: "badge badge-neutral",
};

export default function StatusBadge({ status }) {
  const cls = STATUS_CLASS_MAP[status] || "badge badge-neutral";
  return (
    <span className={cls}>
      <span className="badge-dot" aria-hidden="true" />
      {status}
    </span>
  );
}
