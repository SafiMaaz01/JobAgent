"use client";

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Search, Server, User, ChevronRight, PanelLeftClose, PanelLeftOpen, Sun, Moon } from "lucide-react";
import { getDashboardStats } from "@/lib/api";
import { useSidebar } from "@/components/SidebarContext";
import { useTheme } from "@/components/ThemeContext";

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const [isApiConnected, setIsApiConnected] = useState<boolean>(true);
  const { isCollapsed, toggleSidebar, isMobile, isMobileOpen, toggleMobileSidebar } = useSidebar();
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        await getDashboardStats();
        if (isMounted) setIsApiConnected(true);
      } catch {
        if (isMounted) setIsApiConnected(false);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const getBreadcrumbs = () => {
    if (pathname === "/") return [{ label: "Dashboard", href: "/" }];
    if (pathname.startsWith("/jobs")) return [{ label: "Dashboard", href: "/" }, { label: "Jobs Directory", href: "/jobs" }];
    if (pathname.startsWith("/review")) return [{ label: "Dashboard", href: "/" }, { label: "Review Queue", href: "/review" }];
    if (pathname.startsWith("/applications")) {
      const parts = [{ label: "Dashboard", href: "/" }, { label: "Applications Hub", href: "/applications" }];
      if (pathname !== "/applications") {
        parts.push({ label: "Application Control Room", href: pathname });
      }
      return parts;
    }
    if (pathname.startsWith("/settings")) return [{ label: "Dashboard", href: "/" }, { label: "Settings & Profile", href: "/settings" }];
    return [{ label: "JobAgent", href: "/" }];
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header
      className="app-header"
      style={{
        height: "var(--header-height)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        position: "sticky",
        top: 0,
        zIndex: 30,
        background: "var(--bg-header)",
        borderBottom: "1px solid var(--border-medium)",
      }}
    >
      {/* Breadcrumbs Navigation */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px", fontSize: "13px" }}>
        {/* Mobile-only Menu Toggle Button */}
        {isMobile && (
          <button
            type="button"
            onClick={toggleMobileSidebar}
            aria-label={isMobileOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={isMobileOpen}
            style={{
              background: "var(--bg-surface-0)",
              border: "1px solid var(--border-medium)",
              borderRadius: "var(--radius-md)",
              padding: "6px 8px",
              color: "var(--text-secondary)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.15s ease",
              outline: "none",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent-primary)")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-medium)")}
            title={isMobileOpen ? "Close Menu" : "Open Menu"}
          >
            {isMobileOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>
        )}

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={crumb.href + idx}>
              {idx > 0 && <ChevronRight size={14} color="var(--text-muted)" />}
              <span
                onClick={() => router.push(crumb.href)}
                style={{
                  color: idx === breadcrumbs.length - 1 ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: idx === breadcrumbs.length - 1 ? "600" : "400",
                  cursor: "pointer",
                }}
              >
                {crumb.label}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Right Header Actions */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        {/* Command Palette Trigger */}
        <button
          onClick={() => {
            const event = new KeyboardEvent("keydown", {
              key: "k",
              ctrlKey: true,
              bubbles: true,
            });
            window.dispatchEvent(event);
          }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "10px",
            background: "var(--bg-surface-0)",
            border: "1px solid var(--border-medium)",
            borderRadius: "var(--radius-md)",
            padding: "6px 14px",
            color: "var(--text-secondary)",
            fontSize: "12px",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent-primary)")}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-medium)")}
        >
          <Search size={14} color="var(--text-muted)" />
          <span>Search or Command...</span>
          <kbd
            className="mono-text"
            style={{
              background: "var(--bg-surface-1)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "4px",
              padding: "2px 6px",
              fontSize: "10px",
              color: "var(--text-muted)",
            }}
          >
            Ctrl + K
          </kbd>
        </button>

        {/* Backend System Status */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "6px 12px",
            borderRadius: "var(--radius-md)",
            background: "var(--bg-surface-0)",
            border: "1px solid var(--border-subtle)",
            fontSize: "12px",
            color: "var(--text-secondary)",
          }}
        >
          <Server size={14} color={isApiConnected ? "var(--success)" : "var(--danger)"} />
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: isApiConnected ? "var(--success)" : "var(--danger)",
              boxShadow: isApiConnected ? "0 0 8px rgba(16, 185, 129, 0.4)" : "0 0 8px rgba(239, 68, 68, 0.4)",
            }}
          />
          <span className="mono-text" style={{ fontSize: "11px" }}>
            FastAPI {isApiConnected ? "Online" : "Offline"}
          </span>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "var(--radius-md)",
            background: "var(--bg-surface-0)",
            border: "1px solid var(--border-medium)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-primary)",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
          title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          aria-label="Toggle Theme"
        >
          {theme === "dark" ? <Sun size={18} color="var(--warning)" /> : <Moon size={18} color="var(--accent-primary)" />}
        </button>

        {/* Profile Button */}
        <button
          onClick={() => router.push("/settings")}
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "var(--radius-md)",
            background: "var(--bg-surface-1)",
            border: "1px solid var(--border-medium)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-primary)",
            cursor: "pointer",
          }}
          title="Profile & Settings"
        >
          <User size={18} />
        </button>
      </div>
    </header>
  );
}
