import { getProfile } from "@/lib/api";
import SettingsClient from "@/components/SettingsClient";
import { AlertTriangle } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  let profile;
  try {
    profile = await getProfile();
  } catch (error) {
    return (
      <div
        className="glass-card"
        style={{
          padding: "24px",
          borderColor: "var(--danger-border)",
          background: "var(--danger-surface)",
          color: "#fca5a5",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <AlertTriangle size={24} color="var(--danger)" />
          <div>
            <div style={{ fontWeight: "700", fontSize: "15px" }}>Failed to Load Candidate Profile</div>
            <div style={{ fontSize: "13px", marginTop: "2px" }}>
              {error instanceof Error ? error.message : "Could not connect to JobAgent API at http://127.0.0.1:8000"}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return <SettingsClient initialProfile={profile} />;
}
