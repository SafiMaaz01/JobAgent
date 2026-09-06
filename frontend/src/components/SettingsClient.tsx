"use client";

import React, { useState } from "react";
import { Profile } from "@/lib/types";
import { updateProfile } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import {
  User,
  Target,
  Briefcase,
  GraduationCap,
  Sparkles,
  Save,
  RotateCcw,
  Plus,
  X,
  Link as LinkIcon,
  CheckCircle2,
} from "lucide-react";

interface SettingsClientProps {
  initialProfile: Profile;
}

export default function SettingsClient({ initialProfile }: SettingsClientProps) {
  const [profile, setProfile] = useState<Profile>(initialProfile);
  const [originalProfile, setOriginalProfile] = useState<Profile>(initialProfile);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<"personal" | "roles_skills" | "preferences" | "experience">("personal");
  const { showToast } = useToast();

  const [newSkill, setNewSkill] = useState("");
  const [newTargetRole, setNewTargetRole] = useState("");
  const [newPreferredLocation, setNewPreferredLocation] = useState("");

  const isDirty = JSON.stringify(profile) !== JSON.stringify(originalProfile);

  const handleTextChange = (field: keyof Profile, value: string | number) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const handlePreferencesChange = (field: "okay_with_five_day_office" | "willing_to_relocate", value: boolean) => {
    setProfile((prev) => ({
      ...prev,
      application_preferences: {
        ...(prev.application_preferences || {}),
        [field]: value,
      },
    }));
  };

  const handleAddSkill = () => {
    const trimmed = newSkill.trim();
    if (trimmed && !profile.skills.includes(trimmed)) {
      setProfile((prev) => ({ ...prev, skills: [...prev.skills, trimmed] }));
      setNewSkill("");
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setProfile((prev) => ({
      ...prev,
      skills: prev.skills.filter((s) => s !== skillToRemove),
    }));
  };

  const handleAddTargetRole = () => {
    const trimmed = newTargetRole.trim();
    if (trimmed && !profile.target_roles.includes(trimmed)) {
      setProfile((prev) => ({ ...prev, target_roles: [...prev.target_roles, trimmed] }));
      setNewTargetRole("");
    }
  };

  const handleRemoveTargetRole = (roleToRemove: string) => {
    setProfile((prev) => ({
      ...prev,
      target_roles: prev.target_roles.filter((r) => r !== roleToRemove),
    }));
  };

  const handleAddPreferredLocation = () => {
    const trimmed = newPreferredLocation.trim();
    if (trimmed && !profile.preferred_locations.includes(trimmed)) {
      setProfile((prev) => ({ ...prev, preferred_locations: [...prev.preferred_locations, trimmed] }));
      setNewPreferredLocation("");
    }
  };

  const handleRemovePreferredLocation = (locToRemove: string) => {
    setProfile((prev) => ({
      ...prev,
      preferred_locations: prev.preferred_locations.filter((l) => l !== locToRemove),
    }));
  };

  const handleReset = () => {
    setProfile(originalProfile);
    showToast("Changes Reset", "Reverted candidate profile to last saved state", "info");
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateProfile(profile);
      setProfile(updated);
      setOriginalProfile(updated);
      showToast("Profile Persisted", "Candidate configuration saved to data/profile.json", "success");
    } catch (err: unknown) {
      showToast("Save Failed", err instanceof Error ? err.message : "Failed to save profile", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: "1100px" }}>
      {/* Save Bar */}
      <div
        className="glass-card"
        style={{
          padding: "20px 24px",
          marginBottom: "24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
          position: "sticky",
          top: "80px",
          zIndex: 25,
          background: "linear-gradient(135deg, rgba(19, 27, 46, 0.95) 0%, rgba(26, 36, 61, 0.95) 100%)",
        }}
      >
        <div>
          <div style={{ fontWeight: "800", fontSize: "16px", color: "var(--text-primary)" }}>
            Candidate Profile Control Center
          </div>
          <div className="mono-text" style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "2px" }}>
            Authoritative candidate data stored in data/profile.json
          </div>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          {isDirty && (
            <button type="button" onClick={handleReset} disabled={saving} className="btn-secondary">
              <RotateCcw size={14} />
              <span>Reset</span>
            </button>
          )}

          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !isDirty}
            className="btn-primary"
          >
            <Save size={15} />
            <span>{saving ? "Saving Profile..." : "Save Changes"}</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          marginBottom: "24px",
          borderBottom: "1px solid var(--border-subtle)",
          paddingBottom: "12px",
        }}
      >
        {[
          { id: "personal", label: "Personal Info", icon: User },
          { id: "roles_skills", label: "Roles & Skills", icon: Target },
          { id: "preferences", label: "Job Preferences", icon: Sparkles },
          { id: "experience", label: "Experience & Education", icon: Briefcase },
        ].map((tab) => {
          const IconComp = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={isActive ? "btn-primary" : "btn-secondary"}
              style={{ padding: "8px 16px", fontSize: "12.5px" }}
            >
              <IconComp size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {/* Tab 1: Personal Info */}
        {activeTab === "personal" && (
          <div className="glass-card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
            <h2 className="section-title">Personal Contact Details</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div>
                <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Full Name *</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.name}
                  onChange={(e) => handleTextChange("name", e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Email Address *</label>
                <input
                  type="email"
                  className="input-field"
                  value={profile.email}
                  onChange={(e) => handleTextChange("email", e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Phone Number *</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.phone}
                  onChange={(e) => handleTextChange("phone", e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Location *</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.location}
                  onChange={(e) => handleTextChange("location", e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Professional Summary</label>
              <textarea
                rows={4}
                className="input-field"
                value={profile.summary}
                onChange={(e) => handleTextChange("summary", e.target.value)}
                placeholder="Candidate summary overview for AI match evaluations..."
              />
            </div>
          </div>
        )}

        {/* Tab 2: Target Roles & Technical Skills */}
        {activeTab === "roles_skills" && (
          <div className="glass-card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Target Roles */}
            <div>
              <h2 className="section-title" style={{ marginBottom: "12px" }}>Target Job Roles ({profile.target_roles.length})</h2>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "12px" }}>
                {profile.target_roles.map((role, idx) => (
                  <span key={idx} className="badge-semantic badge-autofilling" style={{ padding: "6px 12px", fontSize: "12px" }}>
                    <span>{role}</span>
                    <button type="button" onClick={() => handleRemoveTargetRole(role)} style={{ background: "none", border: "none", color: "var(--accent-light)", cursor: "pointer", marginLeft: "4px" }}>
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>
              <div style={{ display: "flex", gap: "8px", maxWidth: "420px" }}>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Add target role..."
                  value={newTargetRole}
                  onChange={(e) => setNewTargetRole(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddTargetRole();
                    }
                  }}
                />
                <button type="button" onClick={handleAddTargetRole} className="btn-secondary" style={{ padding: "8px 14px", fontSize: "12px" }}>
                  <Plus size={14} />
                  <span>Add</span>
                </button>
              </div>
            </div>

            {/* Skills */}
            <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "20px" }}>
              <h2 className="section-title" style={{ marginBottom: "12px" }}>Technical Skills ({profile.skills.length})</h2>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "12px" }}>
                {profile.skills.map((skill, idx) => (
                  <span key={idx} className="badge-semantic badge-ready" style={{ padding: "6px 12px", fontSize: "12px" }}>
                    <span>{skill}</span>
                    <button type="button" onClick={() => handleRemoveSkill(skill)} style={{ background: "none", border: "none", color: "var(--success)", cursor: "pointer", marginLeft: "4px" }}>
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>
              <div style={{ display: "flex", gap: "8px", maxWidth: "420px" }}>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Add skill (e.g. Next.js, FastAPI)..."
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddSkill();
                    }
                  }}
                />
                <button type="button" onClick={handleAddSkill} className="btn-secondary" style={{ padding: "8px 14px", fontSize: "12px" }}>
                  <Plus size={14} />
                  <span>Add</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Job Preferences */}
        {activeTab === "preferences" && (
          <div className="glass-card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
            <h2 className="section-title">Job & Location Preferences</h2>

            <div>
              <label className="caption-text" style={{ display: "block", marginBottom: "8px" }}>Preferred Locations ({profile.preferred_locations.length})</label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "12px" }}>
                {profile.preferred_locations.map((loc, idx) => (
                  <span key={idx} className="badge-semantic badge-approved" style={{ padding: "6px 12px", fontSize: "12px" }}>
                    <span>{loc}</span>
                    <button type="button" onClick={() => handleRemovePreferredLocation(loc)} style={{ background: "none", border: "none", color: "var(--cyan-accent)", cursor: "pointer", marginLeft: "4px" }}>
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>
              <div style={{ display: "flex", gap: "8px", maxWidth: "420px" }}>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Add preferred location..."
                  value={newPreferredLocation}
                  onChange={(e) => setNewPreferredLocation(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddPreferredLocation();
                    }
                  }}
                />
                <button type="button" onClick={handleAddPreferredLocation} className="btn-secondary" style={{ padding: "8px 14px", fontSize: "12px" }}>
                  <Plus size={14} />
                  <span>Add</span>
                </button>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div>
                <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Remote Preference</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.remote_preference}
                  onChange={(e) => handleTextChange("remote_preference", e.target.value)}
                />
              </div>

              <div>
                <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Minimum Salary</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.minimum_salary}
                  onChange={(e) => handleTextChange("minimum_salary", e.target.value)}
                />
              </div>

              <div>
                <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Notice Period</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.notice_period}
                  onChange={(e) => handleTextChange("notice_period", e.target.value)}
                />
              </div>

              <div>
                <label className="caption-text" style={{ display: "block", marginBottom: "6px" }}>Work Authorization</label>
                <input
                  type="text"
                  className="input-field"
                  value={profile.work_authorization}
                  onChange={(e) => handleTextChange("work_authorization", e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", borderTop: "1px solid var(--border-subtle)", paddingTop: "16px" }}>
              <label style={{ display: "inline-flex", alignItems: "center", gap: "10px", fontSize: "13px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={profile.application_preferences?.willing_to_relocate ?? true}
                  onChange={(e) => handlePreferencesChange("willing_to_relocate", e.target.checked)}
                  style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }}
                />
                <span>Willing to relocate for position</span>
              </label>

              <label style={{ display: "inline-flex", alignItems: "center", gap: "10px", fontSize: "13px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={profile.application_preferences?.okay_with_five_day_office ?? true}
                  onChange={(e) => handlePreferencesChange("okay_with_five_day_office", e.target.checked)}
                  style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }}
                />
                <span>Open to 5-day on-site work environment</span>
              </label>
            </div>
          </div>
        )}

        {/* Tab 4: Experience & Education */}
        {activeTab === "experience" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
            <div className="glass-card" style={{ padding: "24px" }}>
              <h2 className="section-title" style={{ marginBottom: "16px" }}>Work Experience History</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                {profile.experience.map((exp, idx) => (
                  <div key={idx} style={{ background: "var(--bg-surface-0)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "14px" }}>
                    <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--text-primary)" }}>{exp.role}</div>
                    <div style={{ fontSize: "12.5px", color: "var(--accent-light)", marginTop: "2px" }}>{exp.company}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>{exp.start} to {exp.end || "Present"}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card" style={{ padding: "24px" }}>
              <h2 className="section-title" style={{ marginBottom: "16px" }}>Education History</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                {profile.education.map((edu, idx) => (
                  <div key={idx} style={{ background: "var(--bg-surface-0)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)", padding: "14px" }}>
                    <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--text-primary)" }}>{edu.degree}</div>
                    <div style={{ fontSize: "12.5px", color: "var(--text-secondary)", marginTop: "2px" }}>{edu.institution}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>{edu.start} to {edu.end || edu.graduation || "Graduated"}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
