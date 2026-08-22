import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { loginWithPassword, sendOtp, verifyOtp, getDemoConfig } from "../api/auth";
import PasswordEyeIcon from "../components/PasswordEyeIcon";
import { IconLayers, IconCheckCircle, IconLock, IconBarChart } from "../components/Icons";

// Demo/test-only credentials for this environment. Not a secret -- the
// account itself is a seeded demo account (see backend/seed_subadmin.py).
// The OTP is intentionally NOT hardcoded here -- see the demoOtp state
// below, which is fetched from the backend's own DEMO_OTP setting so the
// two can never drift out of sync.
const DEMO_SUBADMIN = {
  email: "subadmin@strivenest.com",
  password: "Subadmin@12",
};

const FEATURES = [
  { icon: IconLayers, text: "Delegated employee & application oversight" },
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

  // Demo config, fetched from the backend so the OTP shown here is always
  // exactly what services/auth_service.py will actually accept -- never a
  // value hardcoded in this file that could drift out of sync.
  const [demoMode, setDemoMode] = useState(false);
  const [demoOtp, setDemoOtp] = useState(null);
  const [demoMobile, setDemoMobile] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getDemoConfig()
      .then((cfg) => {
        if (cancelled) return;
        setDemoMode(Boolean(cfg.demo_mode));
        setDemoOtp(cfg.demo_otp || null);
        setDemoMobile(cfg.demo_subadmin_mobile || null);
      })
      .catch(() => {
        // Demo box simply doesn't render if this fails (e.g. demo mode is
        // off, or the request failed) -- login itself is unaffected.
        if (!cancelled) {
          setDemoMode(false);
          setDemoOtp(null);
          setDemoMobile(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Fills the fields AND performs the real POST /api/auth/subadmin/login
  // call (same loginWithPassword() the manual Sign In form uses) so this
  // button produces a real JWT from the backend, not a client-only
  // isLoggedIn flag -- clicking it alone is enough to land on /dashboard,
  // matching the manual email/password flow exactly.
  const handleUseDemoLogin = async () => {
    resetMessages();
    setMode("password");
    setEmail(DEMO_SUBADMIN.email);
    setPassword(DEMO_SUBADMIN.password);

    setLoading(true);
    try {
      const result = await loginWithPassword(DEMO_SUBADMIN.email, DEMO_SUBADMIN.password);
      login(result.access_token, result.user);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  const resetMessages = () => {
    setError("");
    setInfo("");
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
      setInfo("OTP sent. Check your mobile for the verification code.");
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

          <h1 className="auth-brand-title">Manage your organization's day-to-day from one dashboard.</h1>
          <p className="auth-brand-desc">
            The Strivenest Technologies ERP Platform gives SubAdmins delegated oversight of
            employees, clients, projects and daily operations.
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
            <p>Sign in to your SubAdmin dashboard.</p>
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
            SubAdmin accounts are provisioned by an administrator from User &amp; Role Management.
          </p>

          {demoMode && (
            <div className="demo-login-section">
              <p className="demo-login-title">Demo Credentials</p>
              <div className="demo-login-card">
                <p className="demo-login-role">Email &amp; Password</p>
                <code className="demo-login-creds">Email: {DEMO_SUBADMIN.email}</code>
                <code className="demo-login-creds">Password: {DEMO_SUBADMIN.password}</code>
                <button
                  type="button"
                  className="btn btn-secondary btn-block btn-small"
                  onClick={handleUseDemoLogin}
                  disabled={loading}
                >
                  {loading ? "Signing in..." : "Use Demo Login"}
                </button>
              </div>
              {demoOtp && (
                <div className="demo-login-card">
                  <p className="demo-login-role">Mobile OTP</p>
                  {demoMobile && (
                    <code className="demo-login-creds">Mobile: {demoMobile}</code>
                  )}
                  <code className="demo-login-creds">Demo OTP: {demoOtp}</code>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
