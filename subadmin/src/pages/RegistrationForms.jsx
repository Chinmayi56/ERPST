import React, { useEffect, useState } from "react";
import {
  listRegistrationLinks,
  createRegistrationLink,
  disableRegistrationLink,
} from "../api/registrationLinks";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";

export default function RegistrationForms() {
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [copiedId, setCopiedId] = useState(null);
  const [disableTarget, setDisableTarget] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [expiresInDays, setExpiresInDays] = useState(7);
  const [note, setNote] = useState("");
  const [newlyCreatedUrl, setNewlyCreatedUrl] = useState(null);
  const [bannerCopyState, setBannerCopyState] = useState("idle"); // idle | copied | error

  const load = () => {
    setLoading(true);
    listRegistrationLinks()
      .then(setLinks)
      .catch(() => setError("Could not load registration links."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setCreating(true);
    setCreateError("");
    try {
      const result = await createRegistrationLink(Number(expiresInDays), note || undefined);
      setNewlyCreatedUrl(result.url);
      setBannerCopyState("idle");
      setNote("");
      load();
    } catch (err) {
      setCreateError(err.response?.data?.detail || "Could not generate link.");
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = async (url, linkId) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopiedId(linkId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      // Clipboard may be unavailable; fail silently, user can select text manually.
    }
  };

  // Copies the just-generated link shown in the "Link created" banner. Uses
  // the same Clipboard API + execCommand fallback already used for the
  // Employee Portal Access copy button, so behavior is consistent across the
  // app on older/insecure-context browsers. Never touches link generation,
  // token creation, or the backend URL itself -- it only copies the exact
  // URL the backend already returned.
  const handleCopyGeneratedLink = async () => {
    if (!newlyCreatedUrl) return;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(newlyCreatedUrl);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = newlyCreatedUrl;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setBannerCopyState("copied");
      setTimeout(() => setBannerCopyState("idle"), 2000);
    } catch (err) {
      setBannerCopyState("error");
    }
  };

  const handleEmailShare = (url) => {
    const subject = encodeURIComponent("Strivenest Technologies — Employee Registration Link");
    const body = encodeURIComponent(
      `You have been invited to complete your employee registration.\n\nPlease use the following link:\n${url}`
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  const handleWhatsappShare = (url) => {
    const text = encodeURIComponent(
      `Strivenest Technologies — Complete your employee registration here: ${url}`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank", "noopener,noreferrer");
  };

  const handleDisable = async () => {
    setActionLoading(true);
    try {
      await disableRegistrationLink(disableTarget.link_id);
      setDisableTarget(null);
      load();
    } catch (err) {
      setCreateError(err.response?.data?.detail || "Could not disable link.");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Registration Forms</h1>
        <p className="page-subtitle">Generate and manage secure links to the Employee Registration Form.</p>
      </div>

      <div className="detail-section" style={{ marginBottom: 24 }}>
        <h2>Generate New Link</h2>
        {createError && <div className="alert alert-error">{createError}</div>}
        {newlyCreatedUrl && (
          <div className="alert alert-info">
            <p style={{ margin: "0 0 8px" }}>Link created:</p>
            <div className="generated-link-row">
              <code className="link-code">{newlyCreatedUrl}</code>
              <button
                type="button"
                className="btn btn-secondary btn-small"
                title="Copy registration link"
                aria-label="Copy registration link"
                onClick={handleCopyGeneratedLink}
              >
                {bannerCopyState === "copied" ? "✓ Copied!" : "📋 Copy Link"}
              </button>
            </div>
            {bannerCopyState === "error" && (
              <p className="field-error" style={{ marginTop: 6, marginBottom: 0 }}>
                Unable to copy link. Please copy it manually.
              </p>
            )}
          </div>
        )}
        <form onSubmit={handleGenerate} className="inline-form">
          <div className="form-group">
            <label htmlFor="expires">Expires in (days)</label>
            <input
              id="expires"
              type="number"
              min={1}
              max={90}
              value={expiresInDays}
              onChange={(e) => setExpiresInDays(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="note">Note (optional)</label>
            <input
              id="note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Batch hiring - August 2026"
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={creating}>
            {creating ? "Generating..." : "Generate Registration Link"}
          </button>
        </form>
      </div>

      {loading ? (
        <Loader label="Loading links..." />
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : links.length === 0 ? (
        <EmptyState title="No registration links created yet." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Link ID</th>
                <th>Note</th>
                <th>Status</th>
                <th>Created Date</th>
                <th>Expiry Date</th>
                <th>Used Count</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {links.map((link) => (
                <tr key={link.link_id}>
                  <td>{link.link_id}</td>
                  <td>{link.note || "—"}</td>
                  <td>
                    <StatusBadge status={link.status} />
                  </td>
                  <td>{new Date(link.created_date).toLocaleDateString()}</td>
                  <td>{new Date(link.expiry_date).toLocaleDateString()}</td>
                  <td>{link.used_count}</td>
                  <td>
                    <div className="table-actions">
                      {link.url && (
                        <>
                          <button
                            type="button"
                            className="btn btn-small btn-secondary"
                            onClick={() => handleCopy(link.url, link.link_id)}
                          >
                            {copiedId === link.link_id ? "Copied!" : "Copy"}
                          </button>
                          <button
                            type="button"
                            className="btn btn-small btn-secondary"
                            onClick={() => handleEmailShare(link.url)}
                          >
                            Email
                          </button>
                          <button
                            type="button"
                            className="btn btn-small btn-secondary"
                            onClick={() => handleWhatsappShare(link.url)}
                          >
                            WhatsApp
                          </button>
                        </>
                      )}
                      {link.status === "ACTIVE" && (
                        <button
                          type="button"
                          className="btn btn-small btn-danger"
                          onClick={() => setDisableTarget(link)}
                        >
                          Disable
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="table-note">
            Note: for security, the full shareable URL is only shown once when a link is created.
            Existing links can still be disabled from this table.
          </p>
        </div>
      )}

      <ConfirmDialog
        open={!!disableTarget}
        title="Disable Registration Link"
        message={disableTarget ? `Disable registration link ${disableTarget.link_id}? It can no longer be used.` : ""}
        confirmLabel="Disable"
        danger
        loading={actionLoading}
        onConfirm={handleDisable}
        onCancel={() => setDisableTarget(null)}
      />
    </div>
  );
}
