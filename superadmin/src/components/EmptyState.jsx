import React from "react";
import { IconInbox } from "./Icons";

export default function EmptyState({ title = "Nothing here yet.", subtitle }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">
        <IconInbox size={22} />
      </div>
      <p className="empty-state-title">{title}</p>
      {subtitle && <p className="empty-state-subtitle">{subtitle}</p>}
    </div>
  );
}
