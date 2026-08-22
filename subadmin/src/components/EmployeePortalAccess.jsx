import React, { useState } from "react";
import {
  getEmployeePortalLoginLink,
  buildWhatsAppShareUrl,
  buildEmailShareUrl,
} from "../utils/employeePortal";

/**
 * "Employee Portal Access" panel shown to SubAdmin in Employee
 * Management. It never renders a login form itself — the Employee Portal
 * is a fully separate app (see `employee/`). This panel only lets
 * SubAdmin copy or share the portal's login link with the employee.
 */
export default function EmployeePortalAccess({ employee }) {
  const [copied, setCopied] = useState(false);
  const loginLink = getEmployeePortalLoginLink();

  const handleCopyLink = async () => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(loginLink);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = loginLink;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setCopied(false);
    }
  };

  return (
    <section className="detail-section portal-access-section" id="portal-access">
      <h2>Employee Portal Access</h2>
      <p className="detail-field-value" style={{ textAlign: "left", fontWeight: 400, marginBottom: 12 }}>
        Share this link so {employee?.full_name || "the employee"} can sign in to their own Employee
        Portal — a separate login, not part of the SubAdmin Dashboard.
      </p>
      <span className="link-code" data-testid="portal-login-link">
        {loginLink}
      </span>
      <div className="table-actions portal-access-actions">
        <button type="button" className="btn btn-secondary" onClick={handleCopyLink}>
          {copied ? "Copied!" : "Copy Login Link"}
        </button>
        <a
          className="btn btn-secondary"
          href={buildWhatsAppShareUrl(employee)}
          target="_blank"
          rel="noreferrer"
        >
          Share on WhatsApp
        </a>
        <a className="btn btn-secondary" href={buildEmailShareUrl(employee)}>
          Share via Email
        </a>
      </div>
    </section>
  );
}
