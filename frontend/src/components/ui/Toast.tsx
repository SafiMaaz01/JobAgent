"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from "lucide-react";

export type ToastType = "success" | "error" | "info" | "warning";

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (title: string, description?: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((title: string, description?: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, description, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          pointerEvents: "none",
          maxWidth: "380px",
          width: "100%",
        }}
      >
        <AnimatePresence>
          {toasts.map((toast) => {
            let bg = "rgba(19, 27, 46, 0.95)";
            let border = "var(--border-medium)";
            let icon = <Info size={18} color="var(--accent-light)" />;

            if (toast.type === "success") {
              border = "rgba(16, 185, 129, 0.4)";
              icon = <CheckCircle size={18} color="#34d399" />;
            } else if (toast.type === "error") {
              border = "rgba(239, 68, 68, 0.4)";
              icon = <AlertCircle size={18} color="#f87171" />;
            } else if (toast.type === "warning") {
              border = "rgba(245, 158, 11, 0.4)";
              icon = <AlertTriangle size={18} color="#fbbf24" />;
            }

            return (
              <motion.div
                key={toast.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: 50, scale: 0.9 }}
                transition={{ duration: 0.2 }}
                style={{
                  pointerEvents: "auto",
                  background: bg,
                  backdropFilter: "blur(16px)",
                  WebkitBackdropFilter: "blur(16px)",
                  border: `1px solid ${border}`,
                  borderRadius: "var(--radius-md)",
                  padding: "14px 16px",
                  boxShadow: "0 10px 30px rgba(0, 0, 0, 0.5)",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "12px",
                }}
              >
                <div style={{ marginTop: "2px" }}>{icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: "700", fontSize: "13px", color: "var(--text-primary)" }}>
                    {toast.title}
                  </div>
                  {toast.description && (
                    <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
                      {toast.description}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => removeToast(toast.id)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    padding: "2px",
                  }}
                >
                  <X size={14} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
