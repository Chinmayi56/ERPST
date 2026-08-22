import React from "react";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="not-found-page">
      <h1>404</h1>
      <p>The page you're looking for doesn't exist.</p>
      <Link to="/dashboard" className="btn btn-primary">
        Go to Dashboard
      </Link>
    </div>
  );
}
