import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { loginWithPassword, sendOtp, verifyOtp } from "../api/auth";
import PasswordEyeIcon from "../components/PasswordEyeIcon";
import { IconLayers, IconCheckCircle, IconLock, IconBarChart } from "../components/Icons";

// Demo/test-only credentials for this environment. Not a secret — the
// account itself is a seeded demo account (see backend/seed_superadmin.py).
const DEMO_SUPERADMIN = {
  email: "superadmin@strivenest.com",
  password: "SuperAdmin@123",
};

const FEATURES = [
  { icon: IconLayers, text: "Centralized employee & application management" },
  { icon: IconCheckCircle, text: "Real-time approvals & role-based access" },
  { icon: IconLock, text: "Secure, enterprise-grade authentication" },
  { icon: IconBarChart, text: "Actionable reports & analytics" },
];

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [mode, setMode] = useState("password"); // "password" | "otp"

  // Email/password state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // OTP state
  const [mobile, setMobile] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const resetMessages = () => {
    setError("");
    setInfo("");
  };

  const handleUseDemoLogin = () => {
    resetMessages();
    setMode("password");
    setEmail(DEMO_SUPERADMIN.email);
    setPassword(DEMO_SUPERADMIN.password);
  };

  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    resetMessages();

    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }

    setLoading(true);
    try {
      const result = await loginWithPassword(email, password);
      login(result.access_token, result.user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  const handleSendOtp = async (e) => {
    e.preventDefault();
    resetMessages();

    if (!/^[6-9]\d{9}$/.test(mobile)) {
      setError("Please enter a valid 10-digit mobile number.");
      return;
    }

    setLoading(true);
    try {
      await sendOtp(mobile);
      setOtpSent(true);
      setInfo("Demo OTP sent. Use 123456 in this development environment.");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not send OTP.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    resetMessages();

    if (!/^\d{6}$/.test(otp)) {
      setError("Please enter the 6-digit OTP.");
      return;
    }

    setLoading(true);
    try {
      const result = await verifyOtp(mobile, otp);
      login(result.access_token, result.user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Incorrect OTP.");
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

          <h1 className="auth-brand-title">Run your organization from one command center.</h1>
          <p className="auth-brand-desc">
            NTAXCO ERP is the unified platform powering workforce operations, approvals, and
            organization-wide oversight for SuperAdmins.
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
            <p>Sign in to your SuperAdmin dashboard.</p>
          </div>

          <div className="login-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={mode === "password"}
              className={"login-tab" + (mode === "password" ? " login-tab-active" : "")}
              onClick={() => {
                setMode("password");
                resetMessages();
              }}
            >
              Email &amp; Password
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === "otp"}
              className={"login-tab" + (mode === "otp" ? " login-tab-active" : "")}
              onClick={() => {
                setMode("otp");
                resetMessages();
              }}
            >
              Mobile OTP
            </button>
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {info && <div className="alert alert-info">{info}</div>}

          <div className="auth-tab-panel" key={mode}>
            {mode === "password" ? (
              <form onSubmit={handlePasswordLogin} className="login-form" noValidate>
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
                  {loading ? "Signing in..." : "Sign In"}
                </button>
              </form>
            ) : (
              <form onSubmit={otpSent ? handleVerifyOtp : handleSendOtp} className="login-form" noValidate>
                <div className="form-group">
                  <label htmlFor="mobile">Mobile Number</label>
                  <input
                    id="mobile"
                    type="tel"
                    value={mobile}
                    onChange={(e) => {
                      setMobile(e.target.value.replace(/\D/g, "").slice(0, 10));
                      setOtpSent(false);
                    }}
                    placeholder="10-digit mobile number"
                    maxLength={10}
                    required
                  />
                </div>

                {otpSent && (
                  <div className="form-group">
                    <label htmlFor="otp">OTP</label>
                    <input
                      id="otp"
                      type="text"
                      inputMode="numeric"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      placeholder="6-digit OTP"
                      maxLength={6}
                      required
                    />
                  </div>
                )}

                {!otpSent ? (
                  <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                    {loading ? "Sending..." : "Send OTP"}
                  </button>
                ) : (
                  <>
                    <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                      {loading ? "Verifying..." : "Verify OTP"}
                    </button>
                    <button
                      type="button"
                      className="btn btn-link btn-block"
                      onClick={handleSendOtp}
                      disabled={loading}
                    >
                      Resend OTP
                    </button>
                  </>
                )}
              </form>
            )}
          </div>

          <p className="login-demo-note">
            Development/demo authentication only. Demo OTP: <strong>123456</strong>
          </p>

          <div className="demo-login-section">
            <p className="demo-login-title">Demo Login</p>
            <div className="demo-login-card">
              <p className="demo-login-role">SuperAdmin</p>
              <code className="demo-login-creds">Email: {DEMO_SUPERADMIN.email}</code>
              <code className="demo-login-creds">Password: {DEMO_SUPERADMIN.password}</code>
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
