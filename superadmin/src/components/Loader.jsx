import React from "react";

export default function Loader({ fullPage = false, label = "Loading..." }) {
  return (
    <div className={fullPage ? "loader-fullpage" : "loader-inline"}>
      <div className="spinner" aria-label={label} role="status" />
      <span className="loader-label">{label}</span>
    </div>
  );
}
