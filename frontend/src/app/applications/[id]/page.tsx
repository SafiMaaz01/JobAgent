import Link from "next/link";
import { notFound } from "next/navigation";
import { getApplicationDetail } from "@/lib/api";
import { ApplicationDetail } from "@/lib/types";
import { MatchScoreBadge, RecommendationBadge, ReviewStatusBadge } from "@/components/StatusBadge";

export const dynamic = "force-dynamic";

interface ApplicationDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function ApplicationDetailPage({
  params,
}: ApplicationDetailPageProps) {
  const resolvedParams = await params;
  const jobId = parseInt(resolvedParams.id, 10);

  if (isNaN(jobId)) {
    notFound();
  }

  let app: ApplicationDetail;
  try {
    app = await getApplicationDetail(jobId);
  } catch {
    notFound();
  }

  const candidate = app.candidate || {};
  const personal = (candidate.personal as Record<string, string>) || {};
  const links = (candidate.links as Record<string, string>) || {};
  const education = (candidate.education as Record<string, string>) || {};
  const experience = (candidate.experience as Record<string, unknown>) || {};
  const preferences = (candidate.preferences as Record<string, string>) || {};
  const skills = Array.isArray(candidate.skills) ? (candidate.skills as string[]) : [];
  const match = app.match_details;

  const isApplied = app.application_status === "applied";

  return (
    <div style={{ maxWidth: "1100px" }}>
      {/* Back Link */}
      <div style={{ marginBottom: "16px" }}>
        <Link
          href="/applications"
          style={{
            fontSize: "13px",
            color: "var(--brand-light)",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            fontWeight: "500",
          }}
        >
          ← Back to Applications Hub
        </Link>
      </div>

      {/* Header Banner */}
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-color)",
          borderRadius: "var(--radius-lg)",
          padding: "24px",
          marginBottom: "24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
              Job ID #{app.job_id}
            </span>
            {app.review_status && <ReviewStatusBadge status={app.review_status} />}
            <span
              className="badge"
              style={{
                backgroundColor: isApplied ? "var(--purple-surface)" : "var(--success-surface)",
                color: isApplied ? "var(--purple)" : "var(--success)",
                border: isApplied ? "1px solid rgba(139, 92, 246, 0.3)" : "1px solid rgba(16, 185, 129, 0.3)",
              }}
            >
              {isApplied ? "Submitted / Applied" : "Package Ready for Review"}
            </span>
          </div>

          <h1 style={{ fontSize: "22px", fontWeight: "700", color: "var(--text-primary)" }}>
            {app.role}
          </h1>
          <div style={{ fontSize: "14px", color: "var(--text-secondary)", marginTop: "4px" }}>
            <strong style={{ color: "var(--text-primary)" }}>{app.company}</strong> •{" "}
            {app.location || "Remote / Not specified"}
          </div>

          <div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "16px", fontSize: "12px" }}>
            <a
              href={app.job_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: "var(--brand-light)",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                fontWeight: "500",
              }}
            >
              Open Original Job Posting ↗
            </a>
            {app.created_at && (
              <span style={{ color: "var(--text-muted)" }}>
                Package Created: {app.created_at.replace("T", " ")}
              </span>
            )}
            {app.applied_at && (
              <span style={{ color: "var(--purple)" }}>
                Applied At: {app.applied_at.replace("T", " ")}
              </span>
            )}

          </div>
        </div>

        {/* Score & Recommendation Pill */}
        <div style={{ display: "flex", gap: "16px" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>
              Match Score
            </div>
            <MatchScoreBadge score={app.match_score} />
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>
              Recommendation
            </div>
            <RecommendationBadge recommendation={app.recommendation} />
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "24px" }}>
        {/* Left Column: Candidate & Application Data */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Section: Candidate Profile Transmitted */}
          <div className="table-container" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "14px", color: "var(--text-primary)" }}>
              Candidate Information in Package
            </h3>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "13px", marginBottom: "16px" }}>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Full Name:</span>{" "}
                <strong style={{ color: "var(--text-primary)" }}>{personal.full_name || "—"}</strong>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Email:</span>{" "}
                <span style={{ color: "var(--text-primary)" }}>{personal.email || "—"}</span>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Phone:</span>{" "}
                <span style={{ color: "var(--text-primary)" }}>{personal.phone || "—"}</span>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Location:</span>{" "}
                <span style={{ color: "var(--text-primary)" }}>{personal.location || "—"}</span>
              </div>
            </div>

            {/* Links */}
            {(links.github || links.linkedin) && (
              <div style={{ display: "flex", gap: "16px", padding: "10px 0", borderTop: "1px solid var(--border-color)", borderBottom: "1px solid var(--border-color)", fontSize: "12px", marginBottom: "16px" }}>
                {links.github && (
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>GitHub:</span>{" "}
                    <a href={links.github} target="_blank" rel="noopener noreferrer" style={{ color: "var(--brand-light)" }}>
                      {links.github}
                    </a>
                  </div>
                )}
                {links.linkedin && (
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>LinkedIn:</span>{" "}
                    <a href={links.linkedin} target="_blank" rel="noopener noreferrer" style={{ color: "var(--brand-light)" }}>
                      {links.linkedin}
                    </a>
                  </div>
                )}
              </div>
            )}

            {/* Education & Experience */}
            <div style={{ fontSize: "13px", display: "flex", flexDirection: "column", gap: "10px" }}>
              <div>
                <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "3px" }}>
                  Education
                </div>
                <div style={{ color: "var(--text-primary)", fontWeight: "500" }}>{education.degree || "—"}</div>
                <div style={{ color: "var(--text-secondary)", fontSize: "12px" }}>
                  {education.institution} • Graduated {education.graduation}
                </div>
                {education.additional_education && (
                  <div style={{ color: "var(--text-muted)", fontSize: "12px", marginTop: "2px" }}>
                    {education.additional_education}
                  </div>
                )}
              </div>

              <div style={{ marginTop: "6px" }}>
                <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "3px" }}>
                  Latest Experience
                </div>
                <div style={{ color: "var(--text-primary)", fontWeight: "500" }}>
                  {String(experience.current_or_latest_role || "—")} at {String(experience.latest_company || "")}
                </div>
                <div style={{ color: "var(--text-secondary)", fontSize: "12px" }}>
                  {String(experience.latest_start || "")} – {String(experience.latest_end || "")} ({String(experience.professional_years || 0)} years exp)
                </div>
              </div>
            </div>

            {/* Skills */}
            {skills.length > 0 && (
              <div style={{ marginTop: "16px" }}>
                <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
                  Target Skills
                </div>
                <div className="tag-list">
                  {skills.slice(0, 15).map((skill, idx) => (
                    <span key={idx} className="tag-item" style={{ fontSize: "11px" }}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section: Application Answers & Questionnaire */}
          <div className="table-container" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "12px", color: "var(--text-primary)" }}>
              Application Question Answers
            </h3>

            {/* Application Preferences */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px", backgroundColor: "var(--bg-subtle)", padding: "12px", borderRadius: "var(--radius-md)", marginBottom: "16px" }}>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Notice Period:</span>{" "}
                <span style={{ color: "var(--text-primary)", fontWeight: "500" }}>{preferences.notice_period || "Immediate"}</span>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Work Authorization:</span>{" "}
                <span style={{ color: "var(--text-primary)", fontWeight: "500" }}>{preferences.work_authorization || "India"}</span>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Salary Expectation:</span>{" "}
                <span style={{ color: "var(--text-primary)", fontWeight: "500" }}>{preferences.minimum_salary || "—"}</span>
              </div>
              <div>
                <span style={{ color: "var(--text-muted)" }}>Remote Preference:</span>{" "}
                <span style={{ color: "var(--text-primary)", fontWeight: "500" }}>{preferences.remote_preference || "—"}</span>
              </div>
            </div>

            {/* Specific Answer Mapping if any */}
            {app.resolved_answers && Object.keys(app.resolved_answers).length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {Object.entries(app.resolved_answers).map(([question, answer], idx) => {
                  if (typeof answer === "object") return null;
                  return (
                    <div
                      key={idx}
                      style={{
                        padding: "10px 12px",
                        border: "1px solid var(--border-color)",
                        borderRadius: "var(--radius-sm)",
                        background: "var(--bg-primary)",
                      }}
                    >
                      <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" }}>
                        Q: {question}
                      </div>
                      <div style={{ fontSize: "13px", color: "var(--text-primary)", fontWeight: "500" }}>
                        A: {String(answer)}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Standard candidate profile answers configured. Form questions will be matched against saved answers during automation.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Status & Artifacts */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Resume & Documents */}
          <div className="table-container" style={{ padding: "18px" }}>
            <h4 style={{ fontSize: "13px", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-secondary)", marginBottom: "12px" }}>
              Attached Resume
            </h4>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "12px",
                background: "var(--bg-subtle)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-color)",
              }}
            >
              <span style={{ fontSize: "20px" }}>📄</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  resume.pdf
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                  {app.resume_path || "data/resume/resume.pdf"}
                </div>
              </div>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "600",
                  color: app.resume_exists ? "var(--success)" : "var(--danger)",
                }}
              >
                {app.resume_exists ? "✓ Found" : "✕ Missing"}
              </span>
            </div>

            <div style={{ marginTop: "12px", fontSize: "11px", color: "var(--text-muted)", lineHeight: 1.4 }}>
              Note: Cover letters are intentionally omitted. This package transmits candidate profile, resume, and resolved question answers.
            </div>
          </div>

          {/* Match Assessment Summary */}
          {match && (
            <div className="table-container" style={{ padding: "18px" }}>
              <h4 style={{ fontSize: "13px", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-secondary)", marginBottom: "12px" }}>
                Evaluation Summary
              </h4>

              {match.reason && (
                <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: "12px" }}>
                  {match.reason}
                </p>
              )}

              {match.strong_matches && match.strong_matches.length > 0 && (
                <div style={{ marginBottom: "10px" }}>
                  <div style={{ fontSize: "11px", color: "var(--success)", fontWeight: "600", marginBottom: "4px" }}>
                    ✓ Strong Matches ({match.strong_matches.length})
                  </div>
                  <div className="tag-list">
                    {match.strong_matches.map((item, idx) => (
                      <span key={idx} className="tag-item tag-item-strong" style={{ fontSize: "11px" }}>
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Automation & Submission Status */}
          <div className="table-container" style={{ padding: "18px" }}>
            <h4 style={{ fontSize: "13px", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-secondary)", marginBottom: "12px" }}>
              Automation Pipeline State
            </h4>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Preparation:</span>
                <span style={{ color: "var(--success)", fontWeight: "600" }}>✓ Complete</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Autofill Automation:</span>
                <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>
                  {isApplied ? "Completed" : "Ready (Phase 6)"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Browser Verification:</span>
                <span style={{ color: "var(--text-secondary)", fontWeight: "500" }}>
                  {isApplied ? "Passed" : "Pending execution"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)" }}>Submission State:</span>
                <span style={{ color: isApplied ? "var(--purple)" : "var(--warning)", fontWeight: "600" }}>
                  {isApplied ? "Submitted" : "Pending Confirmation"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
