import React, { useEffect, useState } from "react";
import { listUsers } from "../api/users";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import StatusBadge from "../components/StatusBadge";

export default function UserRoleManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listUsers()
      .then(setUsers)
      .catch(() => setError("Could not load users."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>User &amp; Role Management</h1>
        <p className="page-subtitle">
          Every login account on the platform and its role. Role assignment for individual
          employees is managed from Employee Management.
        </p>
      </div>

      {loading ? (
        <Loader label="Loading users..." />
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : users.length === 0 ? (
        <EmptyState title="No user accounts yet." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Mobile</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id}>
                  <td>{u.name}</td>
                  <td>{u.email}</td>
                  <td>{u.mobile}</td>
                  <td>
                    <span className="badge badge-neutral">{u.role}</span>
                  </td>
                  <td>
                    <StatusBadge status={u.status} />
                  </td>
                  <td>{u.created_date ? new Date(u.created_date).toLocaleDateString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
