import React from "react";
import EmptyState from "../components/EmptyState";

/**
 * Shared placeholder for ERP modules whose backend doesn't exist yet
 * (Clients, Projects, Tasks, Leave Requests, Attendance, Services/Bookings,
 * Documents). Same layout chrome as every other page — no fake data, no
 * fake statistics, just an honest "not built yet".
 */
export default function ComingSoon({ title, description }) {
  return (
    <div>
      <div className="page-header">
        <h1>{title}</h1>
        <p className="page-subtitle">{description}</p>
      </div>

      <EmptyState
        title="Coming soon"
        subtitle={`${title} will be available once its backend module is built in Phase 2.`}
      />
    </div>
  );
}
