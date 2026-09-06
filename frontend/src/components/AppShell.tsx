"use client";

import React from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import { useSidebar } from "@/components/SidebarContext";
import { AnimatePresence, motion } from "framer-motion";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { isCollapsed, isMobile, isMobileOpen, closeMobileSidebar } = useSidebar();

  const sidebarWidth = isMobile
    ? "0px"
    : isCollapsed
    ? "var(--sidebar-collapsed-width)"
    : "var(--sidebar-width)";

  return (
    <div className="app-container" style={{ minHeight: "100vh", backgroundColor: "var(--bg-app)" }}>
      {/* Backdrop for Mobile Drawer */}
      <AnimatePresence>
        {isMobile && isMobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={closeMobileSidebar}
            style={{
              position: "fixed",
              inset: 0,
              backgroundColor: "rgba(0, 0, 0, 0.65)",
              backdropFilter: "blur(4px)",
              zIndex: 45,
            }}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      <Sidebar />

      <div
        className="main-content"
        style={{
          marginLeft: sidebarWidth,
          transition: "margin-left 0.28s cubic-bezier(0.16, 1, 0.3, 1), width 0.28s cubic-bezier(0.16, 1, 0.3, 1)",
          width: isMobile ? "100%" : `calc(100% - ${sidebarWidth})`,
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Header />
        <main className="page-body" style={{ flex: 1, padding: "24px", maxWidth: "1600px", margin: "0 auto", width: "100%" }}>
          {children}
        </main>
      </div>
    </div>
  );
}

