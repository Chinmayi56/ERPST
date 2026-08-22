import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { employeeLogin } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import PasswordEyeIcon from "../components/PasswordEyeIcon";
import { IconCalendarCheck, IconFileCheck, IconBriefcase, IconBell } from "../components/Icons";

// Demo/test-only credentials for this environment. Not a secret — the
// account itself is a seeded demo account, approved end-to-end through the
// normal application flow (see backend/seed_demo_employee.py).
const DEMO_EMPLOYEE = {
  email: "nithin@strivenest.com",
  password: "Nithin@12",
};

const FEATURES = [
  { icon: IconCalendarCheck, text: "Mark attendance & apply for leave in seconds" },
  { icon: IconFileCheck, text: "Access payslips & documents securely" },
  { icon: IconBriefcase, text: "Track your tasks, projects & clients" },
  { icon: IconBell, text: "Real-time notifications, always in sync" },
];

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUseDemoLogin = () => {
    setError("");
    setEmail(DEMO_EMPLOYEE.email);
    setPassword(DEMO_EMPLOYEE.password);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await employeeLogin(email, password);
      login(result.access_token, result.user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not log in. If your application hasn't been approved by a SuperAdmin yet, you won't be able to sign in."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      {/* Left brand panel */}
      <div className="auth-panel-brand">
        <div className="auth-decor" aria-hidden="true">
          <div className="auth-decor-grid" />
        </div>

        <div className="auth-brand-inner">
          <div className="auth-logo-mark">
  <img
    src="/logo.png"
    alt="Strivenest Technologies"
    className="auth-company-logo"
  />

  <div className="auth-logo-word">
    <strong>Strivenest Technologies</strong>
    <span>ERP PLATFORM</span>
  </div>
</div>

          <h1 className="auth-brand-title">Your work day, all in one place.</h1>
          <p className="auth-brand-desc">
            NTAXCO ERP gives every employee a single, secure home for attendance, leave, payslips,
            and daily work — anywhere, anytime.
          </p>

          <ul className="auth-feature-list">
            {FEATURES.map((f, idx) => {
              const FeatureIcon = f.icon;
              return (
                <li className="auth-feature-item" key={idx}>
                  <span className="auth-feature-icon" aria-hidden="true">
                    <FeatureIcon size={17} />
                  </span>
                  <span className="auth-feature-text">{f.text}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      {/* Right form panel */}
      <div className="auth-panel-form">
        <div className="auth-form-wrap">
          <div className="auth-form-header">
            <h1>Welcome Back</h1>
            <p>Available only after your application has been approved by a SuperAdmin.</p>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="input-with-action">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
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
            </div>
            <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
              {loading ? "Logging in..." : "Log In"}
            </button>
          </form>

          <p className="auth-form-footer">
            Haven't applied yet? <Link to="/register">Register here</Link>.
          </p>

          <div className="demo-login-section">
            <p className="demo-login-title">Demo Login</p>
            <div className="demo-login-card">
              <p className="demo-login-role">Employee</p>
              <code className="demo-login-creds">Email: {DEMO_EMPLOYEE.email}</code>
              <code className="demo-login-creds">Password: {DEMO_EMPLOYEE.password}</code>
              <button
                type="button"
                className="btn btn-secondary btn-block btn-small"
                onClick={handleUseDemoLogin}
              >
                Use Demo Login
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
