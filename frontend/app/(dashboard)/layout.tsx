import Link from "next/link";
import { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: "flex", height: "100vh", background: "#F7F8FA", fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif", color: "#111827", overflow: "hidden" }}>
      
      {/* ─── SIDEBAR ─── */}
      <aside style={{
        width: "240px",
        minWidth: "240px",
        background: "#FFFFFF",
        borderRight: "1px solid #E5E7EB",
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        position: "fixed",
        left: 0,
        top: 0,
        zIndex: 50,
      }}>
        {/* Logo */}
        <div style={{ padding: "24px 20px 20px", borderBottom: "1px solid #F3F4F6" }}>
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" }}>
            <div style={{ width: "32px", height: "32px", background: "#14B8A6", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
              </svg>
            </div>
            <span style={{ fontSize: "16px", fontWeight: 700, color: "#111827", letterSpacing: "-0.3px" }}>ShortClipr</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: "16px 12px", display: "flex", flexDirection: "column", gap: "2px" }}>
          <p style={{ fontSize: "11px", fontWeight: 600, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: "0.8px", padding: "0 8px", marginBottom: "8px" }}>
            Main Menu
          </p>

          <NavItem href="/dashboard" label="Dashboard" active>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="9" rx="1.5"></rect><rect x="14" y="3" width="7" height="5" rx="1.5"></rect>
              <rect x="14" y="12" width="7" height="9" rx="1.5"></rect><rect x="3" y="16" width="7" height="5" rx="1.5"></rect>
            </svg>
          </NavItem>

          <NavItem href="/projects" label="Projects">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
          </NavItem>

          <NavItem href="/library" label="Library">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </NavItem>

        </nav>

        {/* Bottom Settings */}
        <div style={{ padding: "12px", borderTop: "1px solid #F3F4F6" }}>
          <NavItem href="/settings" label="Settings">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </NavItem>

          {/* Upgrade CTA */}
          <Link href="/pricing" style={{
            display: "flex", alignItems: "center", gap: "10px",
            padding: "10px 10px", borderRadius: "10px", textDecoration: "none",
            fontSize: "13px", fontWeight: 600, color: "#14B8A6",
            background: "linear-gradient(135deg,rgba(20,184,166,0.08),rgba(14,165,233,0.06))",
            border: "1px solid rgba(20,184,166,0.2)",
            marginTop: "10px",
          }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
            </svg>
            Upgrade Plan
          </Link>

          {/* User Profile */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "10px 8px", marginTop: "8px", borderRadius: "8px", cursor: "pointer" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "linear-gradient(135deg, #14B8A6, #0EA5E9)", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: "13px", fontWeight: 700, flexShrink: 0 }}>
              N
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ fontSize: "13px", fontWeight: 600, color: "#111827", lineHeight: 1.2, margin: 0 }}>Nitish</p>
              <p style={{ fontSize: "11px", color: "#9CA3AF", lineHeight: 1.2, margin: 0 }}>Pro Plan</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ─── MAIN AREA ─── */}
      <div style={{ marginLeft: "240px", flex: 1, display: "flex", flexDirection: "column", minHeight: "100vh", overflow: "hidden" }}>
        
        {/* Top Navbar */}
        <header style={{
          height: "64px",
          background: "rgba(255,255,255,0.9)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid #E5E7EB",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 32px",
          position: "sticky",
          top: 0,
          zIndex: 40,
        }}>
          {/* Search */}
          <div style={{ position: "relative", width: "360px" }}>
            <svg style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)", color: "#9CA3AF" }} width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input
              type="text"
              placeholder="Search projects..."
              style={{
                width: "100%", height: "38px", background: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: "10px",
                paddingLeft: "40px", paddingRight: "60px", fontSize: "13px", color: "#374151", outline: "none",
                transition: "all 0.15s"
              }}
            />
            <div style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", display: "flex", gap: "3px" }}>
              <kbd style={{ fontSize: "11px", color: "#9CA3AF", background: "#F3F4F6", border: "1px solid #E5E7EB", borderRadius: "4px", padding: "1px 5px", fontFamily: "inherit" }}>⌘</kbd>
              <kbd style={{ fontSize: "11px", color: "#9CA3AF", background: "#F3F4F6", border: "1px solid #E5E7EB", borderRadius: "4px", padding: "1px 5px", fontFamily: "inherit" }}>K</kbd>
            </div>
          </div>

          {/* Right side */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {/* Notification bell */}
            <button style={{ position: "relative", width: "38px", height: "38px", background: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "#6B7280" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
              <span style={{ position: "absolute", top: "7px", right: "7px", width: "8px", height: "8px", background: "#EF4444", borderRadius: "50%", border: "2px solid white" }}></span>
            </button>

            {/* User */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "4px 8px 4px 4px", background: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: "10px", cursor: "pointer" }}>
              <div style={{ width: "30px", height: "30px", borderRadius: "8px", background: "linear-gradient(135deg, #14B8A6, #0EA5E9)", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: "12px", fontWeight: 700 }}>
                N
              </div>
              <span style={{ fontSize: "13px", fontWeight: 600, color: "#374151" }}>Nitish</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main style={{ flex: 1, overflowY: "auto", padding: "40px 40px 60px" }}>
          {children}
        </main>
      </div>
    </div>
  );
}

/* ─── NAV ITEM COMPONENT ─── */
function NavItem({ href, label, active, children }: { href: string; label: string; active?: boolean; children: ReactNode }) {
  return (
    <Link href={href} style={{
      display: "flex", alignItems: "center", gap: "10px",
      padding: "8px 10px", borderRadius: "8px", textDecoration: "none",
      fontSize: "13.5px", fontWeight: active ? 600 : 500,
      color: active ? "#14B8A6" : "#6B7280",
      background: active ? "#F0FDFA" : "transparent",
      transition: "all 0.15s",
    }}>
      <span style={{ color: active ? "#14B8A6" : "#9CA3AF", flexShrink: 0 }}>{children}</span>
      {label}
    </Link>
  );
}
