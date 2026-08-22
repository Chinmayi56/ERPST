import React, { useState } from "react";

/**
 * Generic confirmation modal.
 * If `requireReason` is true, a textarea is shown and its value passed to onConfirm.
 */
export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  requireReason = false,
  danger = false,
  loading = false,
  onConfirm,
  onCancel,
}) {
  const [reason, setReason] = useState("");
  const [touched, setTouched] = useState(false);

  if (!open) return null;

  const reasonInvalid = requireReason && reason.trim().length < 3;

  const handleConfirm = () => {
    if (requireReason) {
      setTouched(true);
      if (reasonInvalid) return;
      onConfirm(reason.trim());
    } else {
      onConfirm();
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
      <div className="modal-box">
        <h3 id="confirm-dialog-title" className="modal-title">
          {title}
        </h3>
        {message && <p className="modal-message">{message}</p>}

        {requireReason && (
          <div className="form-group">
            <label htmlFor="reason-textarea">Reason (required)</label>
            <textarea
              id="reason-textarea"
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this application is being rejected..."
            />
            {touched && reasonInvalid && (
              <span className="field-error">Please provide a reason (minimum 3 characters).</span>
            )}
          </div>
        )}

        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>
            {cancelLabel}
          </button>
          <button
            type="button"
            className={danger ? "btn btn-danger" : "btn btn-primary"}
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? "Please wait..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
