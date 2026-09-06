"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  CheckSquare,
  Briefcase,
  FileText,
  Settings,
  Bot,
  PanelLeftClose,
  PanelLeftOpen,
  Zap,
} from "lucide-react";
import { getDashboardStats } from "@/lib/api";
import { DashboardStats } from "@/lib/types";
import { useSidebar } from "@/components/SidebarContext";

export default function Sidebar() {
  const pathname = usePathname();
  const { isCollapsed, toggleSidebar, isMobile, isMobileOpen, closeMobileSidebar } = useSidebar();
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadStats() {
      try {
        const data = await getDashboardStats();
        if (isMounted) setStats(data);
      } catch {
        // Keep stats null if backend unavailable
      }
    }
    loadStats();
    const interval = setInterval(loadStats, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    {
      name: "Review Queue",
      href: "/review",
      icon: CheckSquare,
      badge: stats && stats.pending_review > 0 ? stats.pending_review : undefined,
      badgeColor: "var(--warning)",
    },
    { name: "Jobs Directory", href: "/jobs", icon: Briefcase },
    {
      name: "Applications",
      href: "/applications",
      icon: FileText,
      badge: stats && stats.ready_applications > 0 ? stats.ready_applications : undefined,
      badgeColor: "var(--success)",
    },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  // Compute effective width and visibility state
  const effectiveCollapsed = isMobile ? false : isCollapsed;
  const currentWidth = isMobile
    ? "280px"
    : isCollapsed
    ? "var(--sidebar-collapsed-width)"
    : "var(--sidebar-width)";

  const transformStyle = isMobile
    ? isMobileOpen
      ? "translateX(0)"
      : "translateX(-100%)"
    : "none";

  return (
    <aside
      aria-label="Main Navigation"
      style={{
        width: currentWidth,
        backgroundColor: "var(--bg-surface-0)",
        borderRight: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        position: "fixed",
        top: 0,
        bottom: 0,
        left: 0,
        zIndex: 50,
        transform: transformStyle,
        transition: isMobile
          ? "transform 0.28s cubic-bezier(0.16, 1, 0.3, 1)"
          : "width 0.28s cubic-bezier(0.16, 1, 0.3, 1), transform 0.28s cubic-bezier(0.16, 1, 0.3, 1)",
        overflowX: "hidden",
        boxShadow: isMobile && isMobileOpen ? "4px 0 24px rgba(0,0,0,0.5)" : "none",
      }}
    >
      {/* Brand Header & Toggle */}
      <div
        style={{
          height: "var(--header-height)",
          display: "flex",
          alignItems: "center",
          justifyContent: effectiveCollapsed ? "center" : "space-between",
          padding: effectiveCollapsed ? "0" : "0 16px",
          borderBottom: "1px solid var(--border-subtle)",
          flexShrink: 0,
        }}
      >
        {effectiveCollapsed ? (
          /* Collapsed Logo Toggle Button - ChatGPT Style */
          <button
            type="button"
            onClick={toggleSidebar}
            aria-label="Expand sidebar"
            aria-expanded={false}
            title="Click JobAgent logo to expand sidebar"
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, var(--accent-primary) 0%, #4f46e5 100%)",
              border: "1px solid var(--border-glow)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              boxShadow: "0 0 14px rgba(99, 102, 241, 0.4)",
              cursor: "pointer",
              transition: "transform 0.15s ease, box-shadow 0.15s ease",
              outline: "none",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "scale(1.08)";
              e.currentTarget.style.boxShadow = "0 0 20px rgba(99, 102, 241, 0.6)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "scale(1)";
              e.currentTarget.style.boxShadow = "0 0 14px rgba(99, 102, 241, 0.4)";
            }}
          >
            <Bot size={22} />
          </button>
        ) : (
          <>
            <Link
              href="/"
              onClick={isMobile ? closeMobileSidebar : undefined}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                overflow: "hidden",
                textDecoration: "none",
              }}
              aria-label="JobAgent Home"
            >
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "var(--radius-md)",
                  background: "linear-gradient(135deg, var(--accent-primary) 0%, #4f46e5 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#ffffff",
                  boxShadow: "0 0 14px rgba(99, 102, 241, 0.35)",
                  flexShrink: 0,
                }}
              >
                <Bot size={20} />
              </div>

              <motion.div
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -6 }}
                transition={{ duration: 0.18 }}
                style={{ overflow: "hidden", whiteSpace: "nowrap" }}
              >
                <div
                  style={{
                    fontWeight: "800",
                    fontSize: "15px",
                    letterSpacing: "-0.02em",
                    color: "var(--text-primary)",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  JobAgent
                  <span
                    style={{
                      fontSize: "9px",
                      fontWeight: "700",
                      background: "var(--accent-surface)",
                      color: "var(--accent-light)",
                      padding: "1px 5px",
                      borderRadius: "4px",
                      border: "1px solid var(--border-glow)",
                    }}
                  >
                    V2
                  </span>
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                  AI Application Copilot
                </div>
              </motion.div>
            </Link>

            <button
              type="button"
              onClick={toggleSidebar}
              aria-label="Collapse sidebar"
              aria-expanded={true}
              style={{
                background: "var(--bg-surface-1)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                color: "var(--text-secondary)",
                cursor: "pointer",
                padding: "6px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "all 0.15s ease",
                outline: "none",
                flexShrink: 0,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "var(--text-primary)";
                e.currentTarget.style.borderColor = "var(--accent-primary)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "var(--text-secondary)";
                e.currentTarget.style.borderColor = "var(--border-subtle)";
              }}
              title="Collapse Sidebar"
            >
              <PanelLeftClose size={18} />
            </button>
          </>
        )}
      </div>

      {/* Navigation List */}
      <nav
        style={{
          padding: effectiveCollapsed ? "16px 8px" : "16px 12px",
          display: "flex",
          flexDirection: "column",
          gap: "6px",
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
        }}
      >
        {!effectiveCollapsed && (
          <div
            style={{
              padding: "0 10px 8px 10px",
              fontSize: "10.5px",
              fontWeight: "700",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "var(--text-dim)",
              whiteSpace: "nowrap",
            }}
          >
            Navigation
          </div>
        )}

        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const IconComponent = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={isMobile ? closeMobileSidebar : undefined}
              title={effectiveCollapsed ? item.name : undefined}
              aria-label={item.name}
              aria-current={isActive ? "page" : undefined}
              style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: effectiveCollapsed ? "10px 0" : "10px 14px",
                borderRadius: "var(--radius-md)",
                fontSize: "13.5px",
                fontWeight: isActive ? "600" : "500",
                color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                transition: "color 0.15s ease, background-color 0.15s ease",
                justifyContent: effectiveCollapsed ? "center" : "flex-start",
                textDecoration: "none",
                outline: "none",
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)";
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.backgroundColor = "transparent";
              }}
              onFocus={(e) => {
                e.currentTarget.style.boxShadow = "0 0 0 2px var(--accent-glow)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              {isActive && (
                <motion.div
                  layoutId="activeNavBackground"
                  style={{
                    position: "absolute",
                    inset: 0,
                    borderRadius: "var(--radius-md)",
                    backgroundColor: "var(--bg-surface-1)",
                    border: "1px solid var(--border-medium)",
                    zIndex: 0,
                  }}
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}

              <div
                style={{
                  position: "relative",
                  zIndex: 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: effectiveCollapsed ? "center" : "flex-start",
                  width: effectiveCollapsed ? "100%" : "auto",
                  gap: "12px",
                }}
              >
                <IconComponent
                  size={20}
                  color={isActive ? "var(--accent-light)" : "var(--text-muted)"}
                  strokeWidth={isActive ? 2.2 : 1.8}
                  style={{ flexShrink: 0 }}
                />

                {!effectiveCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -6 }}
                    transition={{ duration: 0.15 }}
                    style={{ whiteSpace: "nowrap", overflow: "hidden" }}
                  >
                    {item.name}
                  </motion.span>
                )}
              </div>

              {!effectiveCollapsed && item.badge !== undefined && (
                <motion.span
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  style={{
                    marginLeft: "auto",
                    position: "relative",
                    zIndex: 1,
                    background: "var(--bg-surface-2)",
                    color: item.badgeColor || "var(--text-primary)",
                    border: `1px solid ${item.badgeColor || "var(--border-subtle)"}`,
                    fontSize: "10.5px",
                    fontWeight: "700",
                    padding: "1px 7px",
                    borderRadius: "var(--radius-full)",
                    fontFamily: "ui-monospace, monospace",
                    whiteSpace: "nowrap",
                  }}
                >
                  {item.badge}
                </motion.span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Sidebar Footer & Expand Control */}
      <div
        style={{
          padding: effectiveCollapsed ? "12px 8px" : "16px 14px",
          borderTop: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          flexShrink: 0,
        }}
      >
        {effectiveCollapsed ? (
          <button
            type="button"
            onClick={toggleSidebar}
            aria-label="Expand sidebar"
            aria-expanded={false}
            style={{
              width: "100%",
              height: "38px",
              background: "var(--bg-surface-1)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              color: "var(--text-secondary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              transition: "all 0.15s ease",
              outline: "none",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--text-primary)";
              e.currentTarget.style.borderColor = "var(--accent-primary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--text-secondary)";
              e.currentTarget.style.borderColor = "var(--border-subtle)";
            }}
            title="Expand Sidebar"
          >
            <PanelLeftOpen size={18} />
          </button>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.18 }}
            style={{
              padding: "12px 14px",
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(6, 182, 212, 0.08) 100%)",
              border: "1px solid var(--border-subtle)",
              display: "flex",
              alignItems: "center",
              gap: "12px",
              overflow: "hidden",
            }}
          >
            <Zap size={18} color="var(--accent-light)" style={{ flexShrink: 0 }} />
            <div style={{ overflow: "hidden", whiteSpace: "nowrap" }}>
              <div style={{ fontSize: "11.5px", fontWeight: "700", color: "var(--text-primary)" }}>
                Autonomous Engine
              </div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                Local Ollama & Playwright
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </aside>
  );
}
