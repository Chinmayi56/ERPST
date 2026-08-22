import React from "react";
import StatusBadge from "../components/StatusBadge";
import { payslips } from "../data/demoPortalData";

function formatINR(amount) {
  return `₹${amount.toLocaleString("en-IN")}`;
}

export default function Payslips() {
  return (
    <div>
      <div className="page-header">
        <h1>Payslips</h1>
        <p className="page-subtitle">Your recent payslips.</p>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Month</th>
              <th>Gross</th>
              <th>Deductions</th>
              <th>Net Pay</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {payslips.map((slip) => (
              <tr key={slip.id}>
                <td>{slip.month}</td>
                <td>{formatINR(slip.gross)}</td>
                <td>{formatINR(slip.deductions)}</td>
                <td>{formatINR(slip.net)}</td>
                <td>
                  <StatusBadge status={slip.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="table-note">Preview data — payslip download will be enabled once the backend API is available.</p>
      </div>
    </div>
  );
}
