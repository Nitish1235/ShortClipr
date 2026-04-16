export default function SettingsPage() {
  return (
    <div style={{ maxWidth: "800px" }}>
      <h1 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 8px" }}>Settings</h1>
      <p style={{ fontSize: "14px", color: "#6B7280", margin: "0 0 32px" }}>Manage your account, billing, and system preferences.</p>
      
      <div style={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: "16px", padding: "32px", textAlign: "center" }}>
        <p style={{ fontSize: "16px", fontWeight: 600, color: "#374151" }}>Settings Configuration</p>
        <p style={{ fontSize: "14px", color: "#9CA3AF", marginTop: "8px" }}>Account settings are currently available via the billing portal. Advanced UI is coming soon.</p>
      </div>
    </div>
  );
}
