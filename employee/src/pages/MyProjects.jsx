import React from "react";
import StatusBadge from "../components/StatusBadge";
import { myProjects } from "../data/demoPortalData";

export default function MyProjects() {
  return (
    <div>
      <div className="page-header">
        <h1>My Projects</h1>
        <p className="page-subtitle">Projects you're currently assigned to.</p>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Project</th>
              <th>Client</th>
              <th>Your Role</th>
              <th>Deadline</th>
              <th>Progress</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {myProjects.map((project) => (
              <tr key={project.id}>
                <td>{project.name}</td>
                <td>{project.client}</td>
                <td>{project.role}</td>
                <td>{project.deadline}</td>
                <td>{project.progress}%</td>
                <td>
                  <StatusBadge status={project.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="table-note">Preview data — this module will connect to live project data once the backend API is available.</p>
      </div>
    </div>
  );
}
