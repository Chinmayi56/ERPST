import React from "react";

/**
 * Shared stroke-style icon set for the SubAdmin UI.
 * Presentational only — no logic, no data. Each icon accepts a `size`
 * (default 20) so call sites can control dimensions per context.
 */
const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

function Svg({ size = 20, children, ...rest }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" {...base} {...rest}>
      {children}
    </svg>
  );
}

export function IconHome(props) {
  return (
    <Svg {...props}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9" />
    </Svg>
  );
}

export function IconLayers(props) {
  return (
    <Svg {...props}>
      <path d="m12 3 8.5 4.5L12 12 3.5 7.5 12 3Z" />
      <path d="m3.5 12 8.5 4.5 8.5-4.5" />
      <path d="m3.5 16.5 8.5 4.5 8.5-4.5" />
    </Svg>
  );
}

export function IconFileText(props) {
  return (
    <Svg {...props}>
      <path d="M14 3H7a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V8l-4-5Z" />
      <path d="M14 3v5h4" />
      <path d="M9 13h6M9 17h6" />
    </Svg>
  );
}

export function IconUsers(props) {
  return (
    <Svg {...props}>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M2.8 20c.7-3.3 3.2-5.2 6.2-5.2s5.5 1.9 6.2 5.2" />
      <path d="M16.2 5.4a3.2 3.2 0 0 1 0 6.2" />
      <path d="M15.7 14.9c2.6.4 4.5 2.2 5.1 5.1" />
    </Svg>
  );
}

export function IconLink(props) {
  return (
    <Svg {...props}>
      <path d="M9.5 14.5 14.5 9.5" />
      <path d="M11 6.5 13 4.6a3.6 3.6 0 0 1 5.1 5.1L16.2 11.6" />
      <path d="M13 17.5 11 19.4a3.6 3.6 0 0 1-5.1-5.1l1.9-1.9" />
    </Svg>
  );
}

export function IconBell(props) {
  return (
    <Svg {...props}>
      <path d="M6 10a6 6 0 1 1 12 0c0 4 1.5 5.5 1.5 5.5H4.5S6 14 6 10Z" />
      <path d="M10 19a2 2 0 0 0 4 0" />
    </Svg>
  );
}

export function IconBarChart(props) {
  return (
    <Svg {...props}>
      <path d="M4 20V10M11 20V4M18 20v-7" />
      <path d="M2.5 20.5h19" />
    </Svg>
  );
}

export function IconUser(props) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="8" r="3.6" />
      <path d="M4.5 20c.9-3.8 3.7-5.9 7.5-5.9s6.6 2.1 7.5 5.9" />
    </Svg>
  );
}

export function IconSettings(props) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 13.5a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.9 2.9l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V20a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.9-2.9l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H4a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.9-2.9l.1.1a1.7 1.7 0 0 0 1.9.3H10a1.7 1.7 0 0 0 1-1.6V4a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.9 2.9l-.1.1a1.7 1.7 0 0 0-.3 1.9V10a1.7 1.7 0 0 0 1.6 1H20a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.6 1Z" />
    </Svg>
  );
}

export function IconMenu(props) {
  return (
    <Svg {...props}>
      <path d="M3.5 6.5h17M3.5 12h17M3.5 17.5h17" />
    </Svg>
  );
}

export function IconLogOut(props) {
  return (
    <Svg {...props}>
      <path d="M9 20H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h4" />
      <path d="M16 16.5 21 12l-5-4.5" />
      <path d="M21 12H9" />
    </Svg>
  );
}

export function IconInbox(props) {
  return (
    <Svg {...props}>
      <path d="M3.5 12.5h5l1.5 3h4l1.5-3h5" />
      <path d="M6 5h12l2.5 7.5V18a1.5 1.5 0 0 1-1.5 1.5h-14A1.5 1.5 0 0 1 3.5 18v-5.5L6 5Z" />
    </Svg>
  );
}

export function IconClock(props) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </Svg>
  );
}

export function IconCheckCircle(props) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="m8.3 12.3 2.6 2.6 4.8-5.4" />
    </Svg>
  );
}

export function IconXCircle(props) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="m9.2 9.2 5.6 5.6M14.8 9.2l-5.6 5.6" />
    </Svg>
  );
}

export function IconUserCheck(props) {
  return (
    <Svg {...props}>
      <circle cx="9.5" cy="8" r="3.2" />
      <path d="M3.3 20c.7-3.3 3.1-5.2 6.2-5.2s5.4 1.9 6.1 5.2" />
      <path d="m16 11 1.8 1.8L21.5 9" />
    </Svg>
  );
}

export function IconLock(props) {
  return (
    <Svg {...props}>
      <rect x="5.5" y="11" width="13" height="9" rx="1.6" />
      <path d="M8.5 11V7.5a3.5 3.5 0 0 1 7 0V11" />
    </Svg>
  );
}

export function IconMobile(props) {
  return (
    <Svg {...props}>
      <rect x="6.5" y="2.5" width="11" height="19" rx="2" />
      <path d="M11 18.5h2" />
    </Svg>
  );
}

export function IconMail(props) {
  return (
    <Svg {...props}>
      <rect x="3" y="5.5" width="18" height="13" rx="2" />
      <path d="m3.5 6.5 8.5 6.5 8.5-6.5" />
    </Svg>
  );
}

export function IconBriefcase(props) {
  return (
    <Svg {...props}>
      <rect x="3" y="7.5" width="18" height="12" rx="1.8" />
      <path d="M8.5 7.5V5.8a1.8 1.8 0 0 1 1.8-1.8h3.4a1.8 1.8 0 0 1 1.8 1.8V7.5" />
      <path d="M3 12.5h18" />
    </Svg>
  );
}

export function IconFolder(props) {
  return (
    <Svg {...props}>
      <path d="M3.5 6.5a1.2 1.2 0 0 1 1.2-1.2h4.6l2 2.2h8a1.2 1.2 0 0 1 1.2 1.2v9.1a1.2 1.2 0 0 1-1.2 1.2H4.7a1.2 1.2 0 0 1-1.2-1.2Z" />
    </Svg>
  );
}

export function IconCheckSquare(props) {
  return (
    <Svg {...props}>
      <rect x="3.5" y="3.5" width="17" height="17" rx="2.2" />
      <path d="m7.5 12 3 3 6-6.5" />
    </Svg>
  );
}

export function IconCalendar(props) {
  return (
    <Svg {...props}>
      <rect x="3.5" y="5" width="17" height="15.5" rx="2" />
      <path d="M3.5 9.5h17M8 3v4M16 3v4" />
    </Svg>
  );
}

export function IconClipboard(props) {
  return (
    <Svg {...props}>
      <rect x="5.5" y="4.5" width="13" height="16" rx="1.8" />
      <rect x="9" y="3" width="6" height="3.2" rx="1" />
      <path d="M8.5 12h7M8.5 15.5h7" />
    </Svg>
  );
}

export function IconShield(props) {
  return (
    <Svg {...props}>
      <path d="M12 3.5 19 6v6c0 4.7-3.1 7.9-7 8.5-3.9-.6-7-3.8-7-8.5V6l7-2.5Z" />
      <path d="m9 12 2.2 2.2L15.5 10" />
    </Svg>
  );
}
