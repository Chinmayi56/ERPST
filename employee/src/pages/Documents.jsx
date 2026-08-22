import React from "react";
import StatusBadge from "../components/StatusBadge";
import { myDocuments } from "../data/demoPortalData";

export default function Documents() {
  return (
    <div>
      <div className="page-header">
        <h1>Documents</h1>
        <p className="page-subtitle">Documents on file with HR.</p>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th>Uploaded</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {myDocuments.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.name}</td>
                <td>{doc.type}</td>
                <td>{doc.uploaded_date}</td>
                <td>
                  <StatusBadge status={doc.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="table-note">Preview data — document upload/download will be enabled once the backend API is available.</p>
      </div>
    </div>
  );
}
