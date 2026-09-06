export default function DashboardLoading() {
  return (
    <div>
      <div className="section-header" style={{ marginBottom: "20px" }}>
        <div>
          <div className="skeleton" style={{ width: "200px", height: "24px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "320px", height: "14px" }} />
        </div>
      </div>

      <div className="metrics-grid">
        {[...Array(7)].map((_, i) => (
          <div key={i} className="metric-card">
            <div className="skeleton" style={{ width: "80px", height: "12px", marginBottom: "12px" }} />
            <div className="skeleton" style={{ width: "60px", height: "30px", marginBottom: "8px" }} />
            <div className="skeleton" style={{ width: "120px", height: "12px" }} />
          </div>
        ))}
      </div>

      <div style={{ marginTop: "32px" }}>
        <div className="skeleton" style={{ width: "180px", height: "20px", marginBottom: "16px" }} />
        <div className="table-container">
          <div style={{ padding: "20px" }}>
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="skeleton"
                style={{ width: "100%", height: "36px", marginBottom: "10px" }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
