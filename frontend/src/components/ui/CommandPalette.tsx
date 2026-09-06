"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  LayoutDashboard,
  Briefcase,
  CheckSquare,
  FileText,
  Settings,
  ArrowRight,
  X,
} from "lucide-react";

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      } else if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  const navigate = (path: string) => {
    router.push(path);
    setIsOpen(false);
    setQuery("");
  };

  const commands = [
    {
      id: "dashboard",
      title: "Go to Dashboard",
      subtitle: "System overview, KPI metrics & analytics",
      icon: LayoutDashboard,
      action: () => navigate("/"),
    },
    {
      id: "jobs",
      title: "Go to Jobs Intelligence",
      subtitle: "Browse all ingested & matched opportunities",
      icon: Briefcase,
      action: () => navigate("/jobs"),
    },
    {
      id: "review",
      title: "Go to Review Queue",
      subtitle: "Human review & approval workflow",
      icon: CheckSquare,
      action: () => navigate("/review"),
    },
    {
      id: "applications",
      title: "Go to Applications Hub",
      subtitle: "Track packages and browser automation runner",
      icon: FileText,
      action: () => navigate("/applications"),
    },
    {
      id: "settings",
      title: "Go to Settings & Profile",
      subtitle: "Manage target roles, skills, and preferences",
      icon: Settings,
      action: () => navigate("/settings"),
    },
  ];

  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.title.toLowerCase().includes(query.toLowerCase()) ||
      cmd.subtitle.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(8px)",
            WebkitBackdropFilter: "blur(8px)",
            zIndex: 99999,
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "center",
            paddingTop: "10vh",
          }}
          onClick={() => setIsOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "100%",
              maxWidth: "600px",
              background: "rgba(13, 18, 29, 0.95)",
              border: "1px solid var(--border-medium)",
              borderRadius: "var(--radius-lg)",
              boxShadow: "0 20px 50px rgba(0, 0, 0, 0.7)",
              overflow: "hidden",
            }}
          >
            {/* Input Bar */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "16px 20px",
                borderBottom: "1px solid var(--border-subtle)",
              }}
            >
              <Search size={20} color="var(--text-secondary)" />
              <input
                type="text"
                autoFocus
                placeholder="Type a command or navigate..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: "var(--text-primary)",
                  fontSize: "15px",
                  fontWeight: "500",
                }}
              />
              <button
                onClick={() => setIsOpen(false)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  padding: "4px",
                }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Command List */}
            <div style={{ maxHeight: "360px", overflowY: "auto", padding: "8px" }}>
              {filteredCommands.length > 0 ? (
                filteredCommands.map((cmd) => {
                  const IconComponent = cmd.icon;
                  return (
                    <div
                      key={cmd.id}
                      onClick={cmd.action}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "12px 16px",
                        borderRadius: "var(--radius-md)",
                        cursor: "pointer",
                        transition: "background-color 0.15s ease",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = "transparent";
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                        <div
                          style={{
                            width: "36px",
                            height: "36px",
                            borderRadius: "var(--radius-sm)",
                            background: "var(--bg-surface-1)",
                            border: "1px solid var(--border-subtle)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "var(--accent-light)",
                          }}
                        >
                          <IconComponent size={18} />
                        </div>
                        <div>
                          <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-primary)" }}>
                            {cmd.title}
                          </div>
                          <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                            {cmd.subtitle}
                          </div>
                        </div>
                      </div>
                      <ArrowRight size={16} color="var(--text-muted)" />
                    </div>
                  );
                })
              ) : (
                <div style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
                  No matching commands found.
                </div>
              )}
            </div>

            {/* Footer */}
            <div
              style={{
                padding: "10px 20px",
                background: "var(--bg-surface-0)",
                borderTop: "1px solid var(--border-subtle)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                fontSize: "11px",
                color: "var(--text-muted)",
              }}
            >
              <span>Navigation Shortcut</span>
              <span className="mono-text" style={{ background: "var(--bg-surface-1)", padding: "2px 6px", borderRadius: "4px" }}>
                ESC to close
              </span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
