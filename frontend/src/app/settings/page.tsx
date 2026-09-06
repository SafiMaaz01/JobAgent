export default function SettingsPage() {
  return (
    <div>
      <div className="section-header">
        <div>
          <h1 className="page-title">Settings & Configuration</h1>
          <p className="page-subtitle">
            Configure profile, Greenhouse job sources, and question answers
          </p>
        </div>
      </div>
      <div className="table-container">
        <div className="empty-state">
          <div className="empty-state-title">Phase 7 Implementation</div>
          <div className="empty-state-desc">
            Profile editing and sources configuration will be enabled in Phase 7.
          </div>
        </div>
      </div>
    </div>
  );
}
