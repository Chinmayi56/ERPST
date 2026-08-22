import React from "react";
import { useAuth } from "../context/AuthContext";
import Loader from "../components/Loader";
import StatusBadge from "../components/StatusBadge";

export default function Profile() {
  const { user, loading } = useAuth();

  if (loading) return <Loader fullPage label="Loading profile..." />;
  if (!user) return null;

  return (
    <div>
      <div className="page-header">
        <h1>Profile</h1>
        <p className="page-subtitle">Your SuperAdmin account details.</p>
      </div>

      <div className="detail-section" style={{ maxWidth: 480 }}>
        <div className="detail-field">
          <span className="detail-field-label">Name</span>
          <span className="detail-field-value">{user.name}</span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Email</span>
          <span className="detail-field-value">{user.email}</span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Mobile</span>
          <span className="detail-field-value">{user.mobile}</span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Role</span>
          <span className="detail-field-value">{user.role}</span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Status</span>
          <span className="detail-field-value">
            <StatusBadge status={user.status} />
          </span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Account Created</span>
          <span className="detail-field-value">{new Date(user.created_date).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
