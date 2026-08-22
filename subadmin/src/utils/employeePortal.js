/**
 * Helpers for the "Employee Portal Access" feature in SubAdmin →
 * Employee Management. The Employee Portal is a separate app (see
 * `employee/`); SubAdmin never embeds its login form — it only shares a
 * link to it. These helpers build that link and the share URLs/text used
 * by the Copy Login Link / WhatsApp / Email actions.
 */

const DEFAULT_PORTAL_URL = "http://localhost:3002";

/** Base URL of the deployed Employee Portal app (no trailing slash). */
export function getEmployeePortalBaseUrl() {
  const raw = import.meta.env.VITE_EMPLOYEE_PORTAL_URL || DEFAULT_PORTAL_URL;
  return raw.replace(/\/+$/, "");
}

/** Full URL to the Employee Portal's separate login page. */
export function getEmployeePortalLoginLink() {
  return `${getEmployeePortalBaseUrl()}/login`;
}

/** Message body shared with the employee, personalized with their name. */
export function buildPortalShareMessage(employee) {
  const name = employee?.full_name || "there";
  const loginLink = getEmployeePortalLoginLink();
  return (
    `Hi ${name}, your Strivenest Technologies employee account is approved. ` +
    `You can log in to the Employee Portal here: ${loginLink} ` +
    `Use your registered email (${employee?.email || ""}) and the password shared with you.`
  );
}

/**
 * WhatsApp share URL. If the employee's mobile looks like a plain 10-digit
 * Indian number, pre-fill the recipient (assumes +91); otherwise falls back
 * to a generic share link where the SubAdmin picks the contact.
 */
export function buildWhatsAppShareUrl(employee) {
  const message = buildPortalShareMessage(employee);
  const mobile = (employee?.mobile || "").replace(/\D/g, "");
  const phone = mobile.length === 10 ? `91${mobile}` : "";
  const base = phone ? `https://wa.me/${phone}` : "https://wa.me/";
  return `${base}?text=${encodeURIComponent(message)}`;
}

/** mailto: URL pre-filled with subject/body for sharing the login link. */
export function buildEmailShareUrl(employee) {
  const subject = "Your Strivenest Technologies Employee Portal access";
  const body = buildPortalShareMessage(employee);
  const to = employee?.email || "";
  return `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
