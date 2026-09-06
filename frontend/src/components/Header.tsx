export default function Header() {
  return (
    <header className="header">
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <span style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: "500" }}>
          Workspace:
        </span>
        <span
          style={{
            fontSize: "12px",
            color: "var(--text-secondary)",
            background: "var(--bg-subtle)",
            padding: "3px 8px",
            borderRadius: "var(--radius-sm)",
            fontFamily: "ui-monospace, monospace",
          }}
        >
          JobAgent Core
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "12px",
            color: "var(--text-secondary)",
          }}
        >
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: "var(--success)",
              boxShadow: "0 0 8px rgba(16, 185, 129, 0.4)",
            }}
          />
          <span>API 127.0.0.1:8000</span>
        </div>
      </div>
    </header>
  );
}
