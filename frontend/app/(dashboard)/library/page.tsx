import Link from "next/link";

export default function LibraryPage() {
  return (
    <div style={{ maxWidth: "800px" }}>
      <h1 style={{ fontSize: "24px", fontWeight: 800, color: "#111827", margin: "0 0 8px" }}>Your Library</h1>
      <p style={{ fontSize: "14px", color: "#6B7280", margin: "0 0 32px" }}>View all your generated video assets.</p>
      
      <div style={{ background: "#fff", border: "1px solid #E5E7EB", borderRadius: "16px", padding: "40px", textAlign: "center" }}>
        <p style={{ fontSize: "16px", fontWeight: 600, color: "#374151", margin: "0 0 12px" }}>Your Library has moved!</p>
        <p style={{ fontSize: "14px", color: "#9CA3AF", marginBottom: "24px" }}>
          You can now find all your generated clips directly in the unified Dashboard under the "My Clips" tab.
        </p>
        <Link href="/dashboard" style={{ background: "#14B8A6", color: "white", textDecoration: "none", padding: "10px 24px", borderRadius: "10px", fontWeight: 600, fontSize: "14px" }}>
          Go to Dashboard
        </Link>
      </div>
    </div>
  );
}
