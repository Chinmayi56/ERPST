import React from "react";
import StatusBadge from "../components/StatusBadge";
import { leaveBalance, leaveRequests } from "../data/demoPortalData";

const BALANCE_LABELS = {
  casual_leave: "Casual Leave",
  sick_leave: "Sick Leave",
  earned_leave: "Earned Leave",
};

export default function LeaveManagement() {
  return (
    <div>
      <div className="page-header">
        <h1>Leave Management</h1>
        <p className="page-subtitle">Your leave balance and recent leave requests.</p>
      </div>

      <div className="stat-grid">
        {Object.entries(leaveBalance).map(([key, balance]) => (
          <div className="stat-card" key={key}>
            <span className="stat-icon" aria-hidden="true">🗓️</span>
            <div>
              <p className="stat-value">
                {balance.remaining}/{balance.total}
              </p>
              <p className="stat-label">{BALANCE_LABELS[key] || key} remaining</p>
            </div>
          </div>
        ))}
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>From</th>
              <th>To</th>
              <th>Days</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {leaveRequests.map((leave) => (
              <tr key={leave.id}>
                <td>{leave.type}</td>
                <td>{leave.from}</td>
                <td>{leave.to}</td>
                <td>{leave.days}</td>
                <td>
                  <StatusBadge status={leave.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="table-note">Preview data — applying for leave will be enabled once the backend API is available.</p>
      </div>
    </div>
  );
}
