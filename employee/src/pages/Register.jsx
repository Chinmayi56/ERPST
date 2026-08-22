import React, { useState, useEffect, useRef } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { submitApplication, uploadDocument } from "../api/applications";
import { getApplicationStatus } from "../api/auth";
import PasswordEyeIcon from "../components/PasswordEyeIcon";

const STATUS_POLL_INTERVAL_MS = 12000; // 12s -- within the 10-15s window

const DEPARTMENTS = [
  "Engineering",
  "Human Resources",
  "Sales",
  "Marketing",
  "Finance",
  "Operations",
  "Customer Support",
  "Design",
];

const initialForm = {
  full_name: "",
  email: "",
  password: "",
  confirm_password: "",
  mobile: "",
  dob: "",
  gender: "",
  address: "",
  department: "",
  designation: "",
  qualification: "",
  experience: "",
};

function validate(form) {
  const errors = {};
  if (!form.full_name.trim() || form.full_name.trim().length < 2) errors.full_name = "Enter your full name.";
  if (!/^\S+@\S+\.\S+$/.test(form.email)) errors.email = "Enter a valid email address.";
  if (!form.password || form.password.length < 8) errors.password = "Password must be at least 8 characters.";
  if (form.confirm_password !== form.password) errors.confirm_password = "Passwords do not match.";
  if (!/^[6-9]\d{9}$/.test(form.mobile.trim())) errors.mobile = "Enter a valid 10-digit mobile number.";
  if (!form.dob) errors.dob = "Date of birth is required.";
  if (!form.gender) errors.gender = "Select a gender.";
  if (!form.address.trim() || form.address.trim().length < 5) errors.address = "Enter your full address.";
  if (!form.department) errors.department = "Select a department.";
  if (!form.designation.trim()) errors.designation = "Enter the designation you're applying for.";
  if (!form.qualification.trim()) errors.qualification = "Enter your highest qualification.";
  if (!form.experience.trim()) errors.experience = "Enter your experience (e.g. '2 years' or 'Fresher').";
  return errors;
}

function Field({ label, error, required, children }) {
  return (
    <div className="form-group">
      <label>
        {label} {required && <span style={{ color: "var(--color-danger)" }}>*</span>}
      </label>
      {children}
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}

export default function Register() {
  const [searchParams] = useSearchParams();
  const registrationToken = searchParams.get("token") || null;
  const navigate = useNavigate();

  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [resumeFile, setResumeFile] = useState(null);
  const [idProofFile, setIdProofFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [result, setResult] = useState(null);

  // Live application status, polled from the backend after submission so the
  // "pending" screen automatically flips to "approved"/"rejected" without a
  // manual refresh -- the status always comes from MongoDB via the API,
  // never set locally.
  const [liveStatus, setLiveStatus] = useState(null);
  const [liveMessage, setLiveMessage] = useState("");
  const pollTimerRef = useRef(null);

  useEffect(() => {
    if (!result) return undefined;

    setLiveStatus(result.status);

    const checkStatus = async () => {
      try {
        const data = await getApplicationStatus(result.email || form.email);
        setLiveStatus(data.status);
        setLiveMessage(data.message);
        if (data.status === "APPROVED" || data.status === "REJECTED") {
          if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
        }
      } catch {
        // Transient network/API errors during polling are not shown to the
        // applicant -- the next scheduled check will simply try again.
      }
    };

    checkStatus();
    pollTimerRef.current = setInterval(checkStatus, STATUS_POLL_INTERVAL_MS);

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate(form);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setSubmitting(true);
    setSubmitError("");
    try {
      let resume_url;
      let id_proof_url;

      if (resumeFile) {
        const uploaded = await uploadDocument(resumeFile);
        resume_url = uploaded.url;
      }
      if (idProofFile) {
        const uploaded = await uploadDocument(idProofFile);
        id_proof_url = uploaded.url;
      }

      const payload = { ...form, resume_url, id_proof_url };
      if (registrationToken) payload.registration_token = registrationToken;

      const application = await submitApplication(payload);
      setResult(application);
    } catch (err) {
      setSubmitError(
        err.response?.data?.detail || "Could not submit your application. Please check your details and try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    const status = liveStatus || result.status;

    return (
      <div className="register-page">
        <div className="register-card">
          <img src="/logo.png" alt="Strivenest Technologies" className="register-logo" />

          {status === "APPROVED" ? (
            <div className="alert alert-success" style={{ marginTop: 16 }}>
              <strong>🎉 Your application has been approved!</strong>
              <br />
              You can now login using your registered email and password.
            </div>
          ) : status === "REJECTED" ? (
            <div className="alert alert-error" style={{ marginTop: 16 }}>
              <strong>Your application has been rejected.</strong>
              <br />
              Please contact the administrator for more information.
            </div>
          ) : (
            <div className="alert alert-info" style={{ marginTop: 16 }}>
              <strong>Application submitted successfully.</strong>
              <br />
              Your application has been submitted to the SuperAdmin for approval.
              <br />
              You will be able to login after your application is approved.
            </div>
          )}

          <div className="detail-grid" style={{ marginTop: 8 }}>
            <div className="detail-field">
              <span className="detail-field-label">Application ID</span>
              <span className="detail-field-value">{result.application_id}</span>
            </div>
            <div className="detail-field">
              <span className="detail-field-label">Status</span>
              <span className="detail-field-value">{status}</span>
            </div>
          </div>

          {status === "APPROVED" ? (
            <button
              type="button"
              className="btn btn-primary btn-block"
              style={{ marginTop: 16 }}
              onClick={() => navigate("/login")}
            >
              Login Now
            </button>
          ) : status === "REJECTED" ? (
            <p className="page-subtitle" style={{ marginTop: 16 }}>
              {liveMessage || "Your application was rejected. Please contact the administrator for more information."}
            </p>
          ) : (
            <>
              <div className="loader-inline" style={{ marginTop: 16 }}>
                <div className="spinner" aria-label="Checking application status" role="status" />
                <span className="loader-label">Checking application status...</span>
              </div>
              <p className="page-subtitle" style={{ marginTop: 12 }}>
                Please keep your Application ID for reference. This page will update automatically once a
                SuperAdmin reviews your application — no need to refresh.
              </p>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="register-page">
      <div className="register-card">
        <img src="/logo.png" alt="Strivenest Technologies" className="register-logo" />
        <h1>Employee Registration</h1>
        <p className="page-subtitle">
          Fill in your details below to apply. Your application will be reviewed by a SuperAdmin before an
          employee account is created.
        </p>

        {submitError && <div className="alert alert-error">{submitError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <h2>Personal Information</h2>
          <Field label="Full Name" required error={errors.full_name}>
            <input type="text" value={form.full_name} onChange={update("full_name")} />
          </Field>
          <Field label="Date of Birth" required error={errors.dob}>
            <input type="date" value={form.dob} onChange={update("dob")} />
          </Field>
          <Field label="Gender" required error={errors.gender}>
            <select value={form.gender} onChange={update("gender")}>
              <option value="">Select gender</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </Field>
          <Field label="Address" required error={errors.address}>
            <textarea rows={3} value={form.address} onChange={update("address")} />
          </Field>

          <h2>Contact Information</h2>
          <Field label="Email" required error={errors.email}>
            <input type="email" value={form.email} onChange={update("email")} />
          </Field>
          <Field label="Password" required error={errors.password}>
            <div className="input-with-action">
              <input
                type={showPassword ? "text" : "password"}
                value={form.password}
                onChange={update("password")}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="input-action-btn input-eye-btn"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                <PasswordEyeIcon visible={showPassword} />
              </button>
            </div>
          </Field>
          <Field label="Verify Password" required error={errors.confirm_password}>
            <div className="input-with-action">
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={form.confirm_password}
                onChange={update("confirm_password")}
                autoComplete="new-password"
              />
              <button
                type="button"
                className="input-action-btn input-eye-btn"
                onClick={() => setShowConfirmPassword((v) => !v)}
                aria-label={showConfirmPassword ? "Hide password" : "Show password"}
              >
                <PasswordEyeIcon visible={showConfirmPassword} />
              </button>
            </div>
          </Field>
          <Field label="Mobile Number" required error={errors.mobile}>
            <input type="tel" maxLength={10} value={form.mobile} onChange={update("mobile")} />
          </Field>

          <h2>Professional Information</h2>
          <Field label="Department" required error={errors.department}>
            <select value={form.department} onChange={update("department")}>
              <option value="">Select department</option>
              {DEPARTMENTS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Designation" required error={errors.designation}>
            <input
              type="text"
              placeholder="e.g. Software Engineer"
              value={form.designation}
              onChange={update("designation")}
            />
          </Field>
          <Field label="Qualification" required error={errors.qualification}>
            <input
              type="text"
              placeholder="e.g. B.Tech Computer Science"
              value={form.qualification}
              onChange={update("qualification")}
            />
          </Field>
          <Field label="Experience" required error={errors.experience}>
            <input
              type="text"
              placeholder="e.g. 2 years or Fresher"
              value={form.experience}
              onChange={update("experience")}
            />
          </Field>

          <h2>Documents</h2>
          <Field label="Resume">
            <input type="file" accept=".pdf,.doc,.docx" onChange={(e) => setResumeFile(e.target.files[0])} />
          </Field>
          <Field label="ID Proof">
            <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setIdProofFile(e.target.files[0])} />
          </Field>

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit Application"}
          </button>
        </form>

        <p className="page-subtitle" style={{ marginTop: 16, textAlign: "center" }}>
          Already approved? <Link to="/login">Log in here</Link>.
        </p>
      </div>
    </div>
  );
}
