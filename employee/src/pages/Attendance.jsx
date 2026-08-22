import React from "react";
import StatusBadge from "../components/StatusBadge";
import { attendanceSummary, recentAttendance } from "../data/demoPortalData";

const CARDS = [
  { key: "present_days", label: "Present Days", icon: "🟢" },
  { key: "absent_days", label: "Absent Days", icon: "🔴" },
  { key: "leave_days", label: "Leave Days", icon: "🟡" },
  { key: "late_days", label: "Late Days", icon: "⏰" },
];

export default function Attendance() {
  return (
    <div>
      <div className="page-header">
        <h1>Attendance</h1>
        <p className="page-subtitle">
          {attendanceSummary.month} · {attendanceSummary.working_days} working days
        </p>
      </div>

      <div className="stat-grid">
        {CARDS.map((card) => (
          <div className="stat-card" key={card.key}>
            <span className="stat-icon" aria-hidden="true">
              {card.icon}
            </span>
            <div>
              <p className="stat-value">{attendanceSummary[card.key]}</p>
              <p className="stat-label">{card.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Check-in</th>
              <th>Check-out</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {recentAttendance.map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td>{row.check_in}</td>
                <td>{row.check_out}</td>
                <td>
                  <StatusBadge status={row.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="table-note">Preview data — this module will connect to live attendance data once the backend API is available.</p>
      </div>
    </div>
  );
}
