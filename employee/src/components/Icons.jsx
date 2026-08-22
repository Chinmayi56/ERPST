import React from "react";

/**
 * Shared stroke-style icon set for the Employee Portal UI.
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

export function IconCalendarCheck(props) {
  return (
    <Svg {...props}>
      <rect x="3.5" y="5" width="17" height="15.5" rx="2" />
      <path d="M3.5 9.5h17M8 3v4M16 3v4" />
      <path d="m8.5 14.5 2.2 2.2 4.3-4.4" />
    </Svg>
  );
}

export function IconFileCheck(props) {
  return (
    <Svg {...props}>
      <path d="M14 3H7a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V8l-4-5Z" />
      <path d="M14 3v5h4" />
      <path d="m9.3 14.7 1.8 1.8 3.6-3.7" />
    </Svg>
  );
}

export function IconBriefcase(props) {
  return (
    <Svg {...props}>
      <rect x="2.5" y="7.5" width="19" height="12" rx="2" />
      <path d="M8 7.5V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1.5" />
      <path d="M2.5 12.5h19" />
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

export function IconMail(props) {
  return (
    <Svg {...props}>
      <rect x="3" y="5.5" width="18" height="13" rx="2" />
      <path d="m3.5 6.5 8.5 6.5 8.5-6.5" />
    </Svg>
  );
}
