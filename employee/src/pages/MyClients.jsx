import React from "react";
import StatusBadge from "../components/StatusBadge";
import { myClients } from "../data/demoPortalData";

export default function MyClients() {
  return (
    <div>
      <div className="page-header">
        <h1>My Clients</h1>
        <p className="page-subtitle">Clients linked to the projects you're working on.</p>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Client</th>
              <th>Contact Person</th>
              <th>Email</th>
              <th>Project</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {myClients.map((client) => (
              <tr key={client.id}>
                <td>{client.name}</td>
                <td>{client.contact}</td>
                <td>{client.email}</td>
                <td>{client.project}</td>
                <td>
                  <StatusBadge status={client.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="table-note">Preview data — this module will connect to live client data once the backend API is available.</p>
      </div>
    </div>
  );
}
