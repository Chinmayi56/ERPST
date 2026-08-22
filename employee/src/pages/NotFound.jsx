import React from "react";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="register-page">
      <div className="register-card" style={{ textAlign: "center" }}>
        <h1>Page not found</h1>
        <p className="page-subtitle">
          <Link to="/register">Go to Employee Registration</Link>
        </p>
      </div>
    </div>
  );
}
