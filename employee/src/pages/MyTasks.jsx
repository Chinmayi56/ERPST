import React from "react";
import StatusBadge from "../components/StatusBadge";
import { myTasks } from "../data/demoPortalData";

const PRIORITY_CLASS = {
  High: "badge badge-rejected",
  Medium: "badge badge-pending",
  Low: "badge badge-neutral",
};

export default function MyTasks() {
  return (
    <div>
      <div className="page-header">
        <h1>My Tasks</h1>
        <p className="page-subtitle">Tasks assigned to you across your active projects.</p>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Project</th>
              <th>Priority</th>
              <th>Due Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {myTasks.map((task) => (
              <tr key={task.id}>
                <td>{task.title}</td>
                <td>{task.project}</td>
                <td>
                  <span className={PRIORITY_CLASS[task.priority] || "badge badge-neutral"}>{task.priority}</span>
                </td>
                <td>{task.due_date}</td>
                <td>
                  <StatusBadge status={task.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="table-note">Preview data — this module will connect to live task data once the backend API is available.</p>
      </div>
    </div>
  );
}
