// Minimal hand-drawn line icons — kept dependency-free rather than pulling in an icon
// library for a handful of glyphs.
import type { SVGProps } from "react";

function base(props: SVGProps<SVGSVGElement>) {
  return {
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    ...props,
  };
}

export function TicketIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4z" />
      <path d="M13 6v2M13 16v2M13 10.5v3" />
    </svg>
  );
}

export function QueueIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <rect x="3" y="4" width="18" height="4" rx="1" />
      <rect x="3" y="10" width="18" height="4" rx="1" />
      <rect x="3" y="16" width="18" height="4" rx="1" />
    </svg>
  );
}

export function ShieldIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function AlertTriangleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 3.5 21.5 20H2.5z" />
      <path d="M12 9.5v4.2" />
      <path d="M12 17.3v.1" />
    </svg>
  );
}

export function LogoutIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5M21 12H9" />
    </svg>
  );
}

export function UsersIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3.5 20c.7-3.2 2.9-5 5.5-5s4.8 1.8 5.5 5" />
      <path d="M16 4.8c1.5.4 2.6 1.7 2.6 3.3 0 1.5-1 2.8-2.4 3.2" />
      <path d="M15 15.3c2.2.4 3.9 2 4.5 4.7" />
    </svg>
  );
}

export function BuildingIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <rect x="5" y="3.5" width="11" height="17" rx="1" />
      <path d="M16 9.5h3.5v11H16" />
      <path d="M8 7.5h.01M11.5 7.5h.01M8 11h.01M11.5 11h.01M8 14.5h.01M11.5 14.5h.01" strokeWidth="2.4" />
    </svg>
  );
}

export function BookIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M4 5.2C4 4.5 4.6 4 5.3 4H11v16H5.3c-.7 0-1.3-.5-1.3-1.2z" />
      <path d="M20 5.2c0-.7-.6-1.2-1.3-1.2H13v16h5.7c.7 0 1.3-.5 1.3-1.2z" />
    </svg>
  );
}

export function ChartIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M4 20V10M11 20V4M18 20v-7" />
      <path d="M2.5 20h19" />
    </svg>
  );
}

export function GearIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <circle cx="12" cy="12" r="3.1" />
      <path d="M12 3.5v2.1M12 18.4v2.1M20.5 12h-2.1M5.6 12H3.5M17.7 6.3l-1.5 1.5M7.8 16.2l-1.5 1.5M17.7 17.7l-1.5-1.5M7.8 7.8 6.3 6.3" />
    </svg>
  );
}

export function TagIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M11.5 3.5H5.8a2.3 2.3 0 0 0-2.3 2.3v5.7c0 .6.24 1.17.66 1.6l8.9 8.9a2.3 2.3 0 0 0 3.25 0l5.04-5.04a2.3 2.3 0 0 0 0-3.25l-8.9-8.9a2.3 2.3 0 0 0-1.6-.66z" />
      <circle cx="8.3" cy="8.3" r="1.1" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function RouteIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <circle cx="5.5" cy="6" r="2" />
      <circle cx="18.5" cy="18" r="2" />
      <path d="M5.5 8v4a4 4 0 0 0 4 4h4" />
      <path d="M16 13.5l2.5 2.5-2.5 2.5" />
    </svg>
  );
}

export function DraftIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M6 3.5h9l4 4V20a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1z" />
      <path d="M14.5 3.5V8h4.5" />
      <path d="M8 12.5h8M8 16h5.5" />
    </svg>
  );
}

export function GaugeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M4 15a8 8 0 1 1 16 0" />
      <path d="M12 15l4.2-5" />
      <path d="M12 15v.01" strokeWidth="2.6" />
    </svg>
  );
}

export function UserCheckIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <circle cx="9.5" cy="8" r="3.2" />
      <path d="M3.5 20c.7-3.2 2.9-5 6-5" />
      <path d="M15.5 15.5l2 2 3.5-3.8" />
    </svg>
  );
}

export function PlusIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function CloseIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M6 6l12 12M18 6 6 18" />
    </svg>
  );
}

export function LogoMark(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="28" height="28" viewBox="0 0 32 32" {...props}>
      <rect width="32" height="32" rx="8" fill="#4f46e5" />
      <path
        d="M9 16.5l4.5 4.5L23 11"
        stroke="#fff"
        strokeWidth="2.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}

export function CheckIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base({ width: 16, height: 16, ...props })}>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

export function XIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base({ width: 16, height: 16, ...props })}>
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  );
}

export function EditIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base({ width: 16, height: 16, ...props })}>
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4z" />
    </svg>
  );
}

export function ArrowUpRightIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base({ width: 16, height: 16, ...props })}>
      <path d="M7 17 17 7M7 7h10v10" />
    </svg>
  );
}

export function InboxIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <polyline points="22 13 16 13 14 16 10 16 8 13 2 13" />
      <path d="M5.45 5.11 2 13v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-7.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  );
}

export function PlusIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base({ width: 16, height: 16, ...props })}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}
