import React, { useEffect, useState } from "react";
import { getMyProfile } from "../api/portal";
import Loader from "../components/Loader";
import StatusBadge from "../components/StatusBadge";

function fmtDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString();
}

export default function Profile() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMyProfile()
      .then(setData)
      .catch(() => setError("Could not load your profile."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader fullPage label="Loading your profile..." />;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!data) return null;

  const personal = data.personal_details || {};
  const professional = data.professional_details || {};

  return (
    <div>
      <div className="page-header">
        <h1>My Profile</h1>
        <p className="page-subtitle">
          Application {data.application_id || "—"} · <StatusBadge status={data.current_status} />
        </p>
      </div>

      <div className="detail-grid">
        <section className="detail-section">
          <h2>Personal Details</h2>
          <div className="detail-field">
            <span className="detail-field-label">Full Name</span>
            <span className="detail-field-value">{personal.full_name || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Email</span>
            <span className="detail-field-value">{personal.email || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Mobile</span>
            <span className="detail-field-value">{personal.mobile || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Date of Birth</span>
            <span className="detail-field-value">{personal.dob || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Gender</span>
            <span className="detail-field-value">{personal.gender || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Address</span>
            <span className="detail-field-value">{personal.address || "—"}</span>
          </div>
        </section>

        <section className="detail-section">
          <h2>Professional Details</h2>
          <div className="detail-field">
            <span className="detail-field-label">Employee ID</span>
            <span className="detail-field-value">{professional.employee_id || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Department</span>
            <span className="detail-field-value">{professional.department || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Designation</span>
            <span className="detail-field-value">{professional.designation || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Joining Date</span>
            <span className="detail-field-value">{professional.joining_date || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Qualification</span>
            <span className="detail-field-value">{professional.qualification || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Experience</span>
            <span className="detail-field-value">{professional.experience || "—"}</span>
          </div>
        </section>

        <section className="detail-section">
          <h2>Application &amp; Approval</h2>
          <div className="detail-field">
            <span className="detail-field-label">Application ID</span>
            <span className="detail-field-value">{data.application_id || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Submitted Date</span>
            <span className="detail-field-value">{fmtDate(data.submitted_date)}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Approval Date</span>
            <span className="detail-field-value">{fmtDate(data.approval_date)}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Approved By</span>
            <span className="detail-field-value">{data.approved_by || "—"}</span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Current Status</span>
            <span className="detail-field-value">
              <StatusBadge status={data.current_status} />
            </span>
          </div>
          <div className="detail-field">
            <span className="detail-field-label">Last Login</span>
            <span className="detail-field-value">{fmtDate(data.last_login)}</span>
          </div>
        </section>
      </div>
    </div>
  );
}
