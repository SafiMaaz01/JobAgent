"use client";

import { useState } from "react";
import { Profile } from "@/lib/types";
import { updateProfile } from "@/lib/api";

interface SettingsClientProps {
  initialProfile: Profile;
}

export default function SettingsClient({ initialProfile }: SettingsClientProps) {
  const [profile, setProfile] = useState<Profile>(initialProfile);
  const [originalProfile, setOriginalProfile] = useState<Profile>(initialProfile);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Quick inputs for tags
  const [newSkill, setNewSkill] = useState("");
  const [newTargetRole, setNewTargetRole] = useState("");
  const [newPreferredLocation, setNewPreferredLocation] = useState("");

  const isDirty = JSON.stringify(profile) !== JSON.stringify(originalProfile);

  // Field change helpers
  const handleTextChange = (field: keyof Profile, value: string) => {
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

  // Skill tag management
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

  // Target roles tag management
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

  // Preferred locations tag management
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

  // Reset/Cancel
  const handleReset = () => {
    setProfile(originalProfile);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  // Save
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const updated = await updateProfile(profile);
      setProfile(updated);
      setOriginalProfile(updated);
      setSuccessMessage("Profile updated and persisted to data/profile.json successfully.");
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to update profile."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: "1000px" }}>
      {/* Top Header & Sticky Save Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "24px",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <h1 className="page-title">Candidate Profile & Settings</h1>
          <p className="page-subtitle">
            Authoritative candidate profile and job-matching configuration stored in{" "}
            <code style={{ fontSize: "12px", color: "var(--brand-light)" }}>data/profile.json</code>
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          {isDirty && (
            <button
              type="button"
              onClick={handleReset}
              disabled={saving}
              style={{
                background: "transparent",
                border: "1px solid var(--border-color)",
                color: "var(--text-secondary)",
                borderRadius: "var(--radius-sm)",
                padding: "8px 16px",
                fontSize: "13px",
                fontWeight: "500",
                cursor: "pointer",
              }}
            >
              Cancel / Reset
            </button>
          )}

          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !isDirty}
            style={{
              background: isDirty ? "var(--brand)" : "var(--bg-subtle)",
              border: "none",
              color: isDirty ? "#ffffff" : "var(--text-muted)",
              borderRadius: "var(--radius-sm)",
              padding: "8px 20px",
              fontSize: "13px",
              fontWeight: "600",
              cursor: isDirty && !saving ? "pointer" : "default",
              boxShadow: isDirty ? "0 2px 8px rgba(59, 130, 246, 0.3)" : "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div
          style={{
            background: "var(--success-surface)",
            border: "1px solid rgba(16, 185, 129, 0.4)",
            color: "#6ee7b7",
            padding: "12px 16px",
            borderRadius: "var(--radius-lg)",
            marginBottom: "24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>✓ {successMessage}</span>
          <button
            onClick={() => setSuccessMessage(null)}
            style={{
              background: "transparent",
              border: "none",
              color: "#6ee7b7",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            ✕
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="error-banner" style={{ marginBottom: "24px" }}>
          <div className="error-title">Validation Error</div>
          <div>{errorMessage}</div>
        </div>
      )}

      {isDirty && !successMessage && (
        <div
          style={{
            background: "rgba(59, 130, 246, 0.1)",
            border: "1px solid rgba(59, 130, 246, 0.3)",
            color: "var(--brand-light)",
            padding: "10px 16px",
            borderRadius: "var(--radius-md)",
            marginBottom: "24px",
            fontSize: "13px",
          }}
        >
          ● You have unsaved profile changes. Click <strong>Save Changes</strong> above to persist them.
        </div>
      )}

      <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
        {/* Section 1: Personal Details */}
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-color)",
            borderRadius: "var(--radius-lg)",
            padding: "24px",
          }}
        >
          <h2 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>
            1. Personal Information
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Full Name *
              </label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => handleTextChange("name", e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Email Address *
              </label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => handleTextChange("email", e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Phone Number *
              </label>
              <input
                type="text"
                value={profile.phone}
                onChange={(e) => handleTextChange("phone", e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Location *
              </label>
              <input
                type="text"
                value={profile.location}
                onChange={(e) => handleTextChange("location", e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
            </div>
          </div>
        </div>

        {/* Section 2: Job Preferences */}
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-color)",
            borderRadius: "var(--radius-lg)",
            padding: "24px",
          }}
        >
          <h2 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>
            2. Job Preferences & Availability
          </h2>

          {/* Target Roles */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "8px" }}>
              Target Job Roles ({profile.target_roles.length})
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "10px" }}>
              {profile.target_roles.map((role, idx) => (
                <span
                  key={idx}
                  style={{
                    background: "var(--brand-surface)",
                    border: "1px solid rgba(59, 130, 246, 0.4)",
                    color: "var(--brand-light)",
                    borderRadius: "var(--radius-sm)",
                    padding: "4px 10px",
                    fontSize: "12px",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  {role}
                  <button
                    type="button"
                    onClick={() => handleRemoveTargetRole(role)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "var(--brand-light)",
                      cursor: "pointer",
                      fontSize: "12px",
                      padding: "0 2px",
                    }}
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <input
                type="text"
                placeholder="Add another target role..."
                value={newTargetRole}
                onChange={(e) => setNewTargetRole(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTargetRole();
                  }
                }}
                style={{
                  maxWidth: "320px",
                  padding: "8px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                }}
              />
              <button
                type="button"
                onClick={handleAddTargetRole}
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-primary)",
                  borderRadius: "var(--radius-sm)",
                  padding: "8px 14px",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                + Add Role
              </button>
            </div>
          </div>

          {/* Preferred Locations */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "8px" }}>
              Preferred Locations ({profile.preferred_locations.length})
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "10px" }}>
              {profile.preferred_locations.map((loc, idx) => (
                <span
                  key={idx}
                  style={{
                    background: "var(--purple-surface)",
                    border: "1px solid rgba(139, 92, 246, 0.4)",
                    color: "var(--purple)",
                    borderRadius: "var(--radius-sm)",
                    padding: "4px 10px",
                    fontSize: "12px",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  {loc}
                  <button
                    type="button"
                    onClick={() => handleRemovePreferredLocation(loc)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "var(--purple)",
                      cursor: "pointer",
                      fontSize: "12px",
                      padding: "0 2px",
                    }}
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <input
                type="text"
                placeholder="Add location (e.g. Remote, Bengaluru)..."
                value={newPreferredLocation}
                onChange={(e) => setNewPreferredLocation(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddPreferredLocation();
                  }
                }}
                style={{
                  maxWidth: "320px",
                  padding: "8px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                }}
              />
              <button
                type="button"
                onClick={handleAddPreferredLocation}
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-primary)",
                  borderRadius: "var(--radius-sm)",
                  padding: "8px 14px",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                + Add Location
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Remote Preference
              </label>
              <input
                type="text"
                value={profile.remote_preference}
                onChange={(e) => handleTextChange("remote_preference", e.target.value)}
                placeholder="e.g. Prefer remote or hybrid"
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Minimum Salary Requirement
              </label>
              <input
                type="text"
                value={profile.minimum_salary}
                onChange={(e) => handleTextChange("minimum_salary", e.target.value)}
                placeholder="e.g. 4 LPA"
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Notice Period
              </label>
              <input
                type="text"
                value={profile.notice_period}
                onChange={(e) => handleTextChange("notice_period", e.target.value)}
                placeholder="e.g. Immediate"
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Work Authorization
              </label>
              <input
                type="text"
                value={profile.work_authorization}
                onChange={(e) => handleTextChange("work_authorization", e.target.value)}
                placeholder="e.g. India"
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
            </div>
          </div>

          {/* Relocation & Office Checkboxes */}
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", borderTop: "1px solid var(--border-color)", paddingTop: "16px" }}>
            <label style={{ display: "inline-flex", alignItems: "center", gap: "10px", fontSize: "13px", color: "var(--text-primary)", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={profile.application_preferences?.willing_to_relocate ?? true}
                onChange={(e) => handlePreferencesChange("willing_to_relocate", e.target.checked)}
                style={{ accentColor: "var(--brand)", width: "16px", height: "16px" }}
              />
              Willing to relocate for the right opportunity
            </label>

            <label style={{ display: "inline-flex", alignItems: "center", gap: "10px", fontSize: "13px", color: "var(--text-primary)", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={profile.application_preferences?.okay_with_five_day_office ?? true}
                onChange={(e) => handlePreferencesChange("okay_with_five_day_office", e.target.checked)}
                style={{ accentColor: "var(--brand)", width: "16px", height: "16px" }}
              />
              Comfortable with a 5-day on-site office work week
            </label>
          </div>
        </div>

        {/* Section 3: Professional Summary */}
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-color)",
            borderRadius: "var(--radius-lg)",
            padding: "24px",
          }}
        >
          <h2 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>
            3. Professional Summary
          </h2>

          <textarea
            rows={4}
            value={profile.summary}
            onChange={(e) => handleTextChange("summary", e.target.value)}
            placeholder="Write a concise overview of your technical background, core frameworks, and architecture experience..."
            style={{
              width: "100%",
              padding: "12px",
              background: "var(--bg-input)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-sm)",
              color: "var(--text-primary)",
              fontSize: "13px",
              lineHeight: "1.6",
              fontFamily: "inherit",
              resize: "vertical",
            }}
          />
        </div>

        {/* Section 4: Skills */}
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-color)",
            borderRadius: "var(--radius-lg)",
            padding: "24px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: "600", color: "var(--text-primary)" }}>
              4. Technical Skills
            </h2>
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              {profile.skills.length} skills listed
            </span>
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "16px" }}>
            {profile.skills.map((skill, idx) => (
              <span
                key={idx}
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-primary)",
                  borderRadius: "var(--radius-sm)",
                  padding: "5px 12px",
                  fontSize: "12px",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                {skill}
                <button
                  type="button"
                  onClick={() => handleRemoveSkill(skill)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    fontSize: "12px",
                    padding: "0 2px",
                  }}
                >
                  ✕
                </button>
              </span>
            ))}
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <input
              type="text"
              placeholder="Add skill (e.g. Next.js, Redux, PostgreSQL)..."
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddSkill();
                }
              }}
              style={{
                maxWidth: "360px",
                padding: "8px 12px",
                background: "var(--bg-input)",
                border: "1px solid var(--border-color)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-primary)",
                fontSize: "13px",
              }}
            />
            <button
              type="button"
              onClick={handleAddSkill}
              style={{
                background: "var(--bg-subtle)",
                border: "1px solid var(--border-color)",
                color: "var(--text-primary)",
                borderRadius: "var(--radius-sm)",
                padding: "8px 14px",
                fontSize: "12px",
                fontWeight: "500",
                cursor: "pointer",
              }}
            >
              + Add Skill
            </button>
          </div>
        </div>

        {/* Section 5: Education & Experience (Overview) */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
          {/* Education */}
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-lg)",
              padding: "24px",
            }}
          >
            <h2 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>
              5. Education Entries
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {profile.education.map((edu, idx) => (
                <div
                  key={idx}
                  style={{
                    background: "var(--bg-subtle)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "var(--radius-md)",
                    padding: "12px 14px",
                  }}
                >
                  <div style={{ fontWeight: "600", fontSize: "13px", color: "var(--text-primary)" }}>
                    {edu.degree}
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
                    {edu.institution}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                    {edu.start || "—"} to {edu.end || edu.graduation || "—"}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Experience */}
          <div
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-lg)",
              padding: "24px",
            }}
          >
            <h2 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>
              6. Professional Experience
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {profile.experience.map((exp, idx) => (
                <div
                  key={idx}
                  style={{
                    background: "var(--bg-subtle)",
                    border: "1px solid var(--border-color)",
                    borderRadius: "var(--radius-md)",
                    padding: "12px 14px",
                  }}
                >
                  <div style={{ fontWeight: "600", fontSize: "13px", color: "var(--text-primary)" }}>
                    {exp.role}
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--brand-light)", marginTop: "2px" }}>
                    {exp.company}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                    {exp.start || "—"} to {exp.end || "Present"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Section 7: Online Profiles & Links */}
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-color)",
            borderRadius: "var(--radius-lg)",
            padding: "24px",
          }}
        >
          <h2 style={{ fontSize: "16px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>
            7. Candidate Online Profiles
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                GitHub Profile URL
              </label>
              <input
                type="url"
                value={profile.github || ""}
                onChange={(e) => handleTextChange("github", e.target.value)}
                placeholder="https://github.com/..."
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                LinkedIn Profile URL
              </label>
              <input
                type="url"
                value={profile.linkedin || ""}
                onChange={(e) => handleTextChange("linkedin", e.target.value)}
                placeholder="https://www.linkedin.com/in/..."
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "12px", fontWeight: "500", color: "var(--text-secondary)", marginBottom: "6px" }}>
                Portfolio Website URL
              </label>
              <input
                type="url"
                value={profile.portfolio || ""}
                onChange={(e) => handleTextChange("portfolio", e.target.value)}
                placeholder="https://..."
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                }}
              />
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
