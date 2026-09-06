"use client";

/**
 * Main application sidebar navigation component.
 * 
 * Provides persistent navigation between Dashboard, Review Queue,
 * Jobs Directory, Applications Hub, and Settings with active link highlighting.
 */
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  name: string;
  href: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: "Dashboard", href: "/", icon: "📊" },
  { name: "Review Queue", href: "/review", icon: "✓" },
  { name: "Jobs Directory", href: "/jobs", icon: "💼" },
  { name: "Applications", href: "/applications", icon: "📝" },
  { name: "Settings", href: "/settings", icon: "⚙" },
];


export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div
        style={{
          height: "var(--header-height)",
          display: "flex",
          alignItems: "center",
          padding: "0 20px",
          borderBottom: "1px solid var(--border-color)",
          gap: "10px",
        }}
      >
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: "28px",
            height: "28px",
            borderRadius: "6px",
            background: "var(--brand)",
            color: "#fff",
            fontWeight: "700",
            fontSize: "13px",
          }}
        >
          JA
        </span>
        <div>
          <div style={{ fontWeight: "700", fontSize: "14px", letterSpacing: "-0.01em" }}>
            JobAgent
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
            Local Dashboard
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav style={{ padding: "16px 12px", display: "flex", flexDirection: "column", gap: "4px" }}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "8px 12px",
                borderRadius: "var(--radius-md)",
                fontSize: "13px",
                fontWeight: isActive ? "600" : "500",
                color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                backgroundColor: isActive ? "var(--bg-subtle)" : "transparent",
                borderLeft: isActive ? "3px solid var(--brand)" : "3px solid transparent",
                transition: "all 0.12s ease",
              }}
            >
              <span style={{ fontSize: "14px" }}>{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div
        style={{
          marginTop: "auto",
          padding: "16px 20px",
          borderTop: "1px solid var(--border-color)",
          fontSize: "11px",
          color: "var(--text-muted)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: "var(--success)",
              display: "inline-block",
            }}
          />
          <span>FastAPI Connected</span>
        </div>
        <div>Port 8000 (Local)</div>
      </div>
    </aside>
  );
}
