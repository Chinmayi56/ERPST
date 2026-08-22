import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { getApplication, approveApplication, rejectApplication } from "../api/applications";
import Loader from "../components/Loader";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";

function Field({ label, value }) {
  return (
    <div className="detail-field">
      <span className="detail-field-label">{label}</span>
      <span className="detail-field-value">{value || value === 0 ? value : "—"}</span>
    </div>
  );
}

export default function ApplicationDetail() {
  const { applicationId } = useParams();
  const navigate = useNavigate();

  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [approveOpen, setApproveOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [approvalCredentials, setApprovalCredentials] = useState(null);

  const load = () => {
    setLoading(true);
    getApplication(applicationId)
      .then(setApplication)
      .catch(() => setError("Could not load this application."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [applicationId]);

  const handleApprove = async () => {
    setActionLoading(true);
    setActionError("");
    try {
      const approved = await approveApplication(applicationId);
      setApproveOpen(false);
      if (approved.temporary_password) {
        setApprovalCredentials({
          employee_id: approved.employee_id,
          email: approved.employee_login_email,
          temporary_password: approved.temporary_password,
        });
      }
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not approve application.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (reason) => {
    setActionLoading(true);
    setActionError("");
    try {
      await rejectApplication(applicationId, reason);
      setRejectOpen(false);
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not reject application.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <Loader fullPage label="Loading application..." />;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!application) return null;

  const a = application;

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/employee-applications" className="back-link">
            ← Back to Applications
          </Link>
          <h1>{a.full_name}</h1>
          <p className="page-subtitle">
            Application {a.application_id} · <StatusBadge status={a.status} />
          </p>
        </div>
        {a.status === "PENDING" && (
          <div className="table-actions">
            <button type="button" className="btn btn-primary" onClick={() => setApproveOpen(true)}>
              Approve
            </button>
            <button type="button" className="btn btn-danger" onClick={() => setRejectOpen(true)}>
              Reject
            </button>
          </div>
        )}
      </div>

      {actionError && <div className="alert alert-error">{actionError}</div>}
      {approvalCredentials && (
        <div className="alert alert-info">
          <strong>Employee account created — share these credentials once.</strong>
          <br />
          Employee ID: {approvalCredentials.employee_id}
          <br />
          Login Email: {approvalCredentials.email}
          <br />
          Temporary Password: {approvalCredentials.temporary_password}
          <br />
          <Link to={`/employees/${approvalCredentials.employee_id}#portal-access`}>
            Open Employee Portal Access →
          </Link>
        </div>
      )}
      {a.status === "REJECTED" && a.rejection_reason && (
        <div className="alert alert-error">Rejection reason: {a.rejection_reason}</div>
      )}

      <div className="detail-grid">
        <section className="detail-section">
          <h2>Personal Information</h2>
          <Field label="Full Name" value={a.full_name} />
          <Field label="Date of Birth" value={a.dob} />
          <Field label="Gender" value={a.gender} />
          <Field label="Profile Photo" value={a.profile_photo_url ? "Uploaded" : "Not provided"} />
        </section>

        <section className="detail-section">
          <h2>Contact Information</h2>
          <Field label="Email" value={a.email} />
          <Field label="Mobile" value={a.mobile} />
          <Field label="Alternate Mobile" value={a.alternate_mobile} />
          <Field label="Address" value={a.address} />
          <Field label="City" value={a.city} />
          <Field label="State" value={a.state} />
          <Field label="Pincode" value={a.pincode} />
        </section>

        <section className="detail-section">
          <h2>Professional Information</h2>
          <Field label="Applied Position" value={a.applied_position} />
          <Field label="Department" value={a.department} />
          <Field label="Qualification" value={a.qualification} />
          <Field label="Experience Level" value={a.experience_level} />
          <Field label="Total Experience" value={a.total_experience} />
          <Field label="Previous Company" value={a.previous_company} />
          <Field label="Previous Designation" value={a.previous_designation} />
          <Field label="Skills" value={a.skills?.length ? a.skills.join(", ") : null} />
        </section>

        <section className="detail-section">
          <h2>Joining Details</h2>
          <Field label="Expected Joining Date" value={a.expected_joining_date} />
          <Field label="Employment Type" value={a.employment_type} />
        </section>

        <section className="detail-section">
          <h2>Emergency Contact</h2>
          <Field label="Contact Name" value={a.emergency_contact_name} />
          <Field label="Relationship" value={a.emergency_relationship} />
          <Field label="Contact Number" value={a.emergency_contact_number} />
        </section>

        <section className="detail-section">
          <h2>Documents</h2>
          <Field
            label="Resume"
            value={
              a.resume_url ? (
                <a href={a.resume_url} target="_blank" rel="noreferrer">
                  View resume
                </a>
              ) : (
                "Not provided"
              )
            }
          />
          <Field
            label="ID Proof"
            value={
              a.id_proof_url ? (
                <a href={a.id_proof_url} target="_blank" rel="noreferrer">
                  View ID proof
                </a>
              ) : (
                "Not provided"
              )
            }
          />
        </section>

        <section className="detail-section">
          <h2>Declaration</h2>
          <Field label="Declaration Text" value={a.declaration_text} />
          <Field label="Accepted" value={a.declaration_accepted ? "Yes" : "No"} />
        </section>

        <section className="detail-section">
          <h2>Application Meta</h2>
          <Field label="Application ID" value={a.application_id} />
          <Field label="Status" value={a.status} />
          <Field label="Submitted Date" value={new Date(a.submitted_date).toLocaleString()} />
          <Field label="Reviewed Date" value={a.reviewed_date ? new Date(a.reviewed_date).toLocaleString() : null} />
          <Field label="Reviewed By" value={a.reviewed_by} />
        </section>
      </div>

      <ConfirmDialog
        open={approveOpen}
        title="Approve Application"
        message={`Approve the application from ${a.full_name}? An employee record will be created.`}
        confirmLabel="Approve"
        loading={actionLoading}
        onConfirm={handleApprove}
        onCancel={() => setApproveOpen(false)}
      />

      <ConfirmDialog
        open={rejectOpen}
        title="Reject Application"
        message={`Reject the application from ${a.full_name}?`}
        confirmLabel="Reject"
        danger
        requireReason
        loading={actionLoading}
        onConfirm={handleReject}
        onCancel={() => setRejectOpen(false)}
      />
    </div>
  );
}
