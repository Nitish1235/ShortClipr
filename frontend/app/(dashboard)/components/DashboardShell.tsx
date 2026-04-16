"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { Menu, X, Moon, Sun } from "lucide-react";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close mobile menu when route changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  return (
    <div style={{ display: "flex", height: "100vh", background: "var(--dash-bg)", fontFamily: "'Inter', sans-serif", color: "var(--dash-text-main)", overflow: "hidden" }}>
      
      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div 
          onClick={() => setIsMobileMenuOpen(false)}
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 40 }}
        />
      )}

      {/* ─── SIDEBAR ─── */}
      <aside style={{
        width: "240px",
        minWidth: "240px",
        background: "var(--dash-nav-bg)",
        borderRight: "1px solid var(--dash-border)",
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        position: "fixed",
        left: isMobileMenuOpen ? 0 : "-100%",
        top: 0,
        zIndex: 50,
        transition: "left 0.3s ease",
      }} className="md-sidebar-fixed">
        
        {/* Logo */}
        <div style={{ padding: "24px 20px 20px", borderBottom: "1px solid var(--dash-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" }}>
            <div style={{ width: "32px", height: "32px", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <img src="/favicon.svg" alt="ShortClipr Ghost Logo" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
            </div>
            <span style={{ fontSize: "16px", fontWeight: 700, color: "var(--dash-text-main)", letterSpacing: "-0.3px" }}>ShortClipr</span>
          </Link>
          <button className="md-hidden" onClick={() => setIsMobileMenuOpen(false)} style={{ background: "none", border: "none", color: "var(--dash-text-muted)" }}>
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: "16px 12px", display: "flex", flexDirection: "column", gap: "2px" }}>
          <p style={{ fontSize: "11px", fontWeight: 600, color: "var(--dash-text-muted)", textTransform: "uppercase", letterSpacing: "0.8px", padding: "0 8px", marginBottom: "8px" }}>
            Main Menu
          </p>

          <NavItem href="/dashboard" label="Dashboard" active={pathname === "/dashboard"}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="9" rx="1.5"></rect><rect x="14" y="3" width="7" height="5" rx="1.5"></rect>
              <rect x="14" y="12" width="7" height="9" rx="1.5"></rect><rect x="3" y="16" width="7" height="5" rx="1.5"></rect>
            </svg>
          </NavItem>

          <NavItem href="/projects" label="Projects" active={pathname === "/projects"}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
          </NavItem>

          <NavItem href="/library" label="Library" active={pathname === "/library"}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </NavItem>
        </nav>

        {/* Bottom Settings */}
        <div style={{ padding: "12px", borderTop: "1px solid var(--dash-border)" }}>
          <NavItem href="/settings" label="Settings" active={pathname === "/settings"}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
          </NavItem>

          {/* Theme Toggle */}
          {mounted && (
            <button 
              onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
              style={{
                display: "flex", alignItems: "center", gap: "10px", width: "100%",
                padding: "8px 10px", borderRadius: "8px", textDecoration: "none", cursor: "pointer",
                fontSize: "13.5px", fontWeight: 500, border: "none",
                color: "var(--dash-text-muted)", background: "transparent",
              }}
            >
              {resolvedTheme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              {resolvedTheme === "dark" ? "Light Mode" : "Dark Mode"}
            </button>
          )}

          {/* Upgrade CTA */}
          <Link href="/pricing" style={{
            display: "flex", alignItems: "center", gap: "10px",
            padding: "10px 10px", borderRadius: "10px", textDecoration: "none",
            fontSize: "13px", fontWeight: 600, color: "#14B8A6",
            background: "var(--dash-accent)", border: "1px solid rgba(20,184,166,0.2)",
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
              <p style={{ fontSize: "13px", fontWeight: 600, color: "var(--dash-text-main)", lineHeight: 1.2, margin: 0 }}>Nitish</p>
              <p style={{ fontSize: "11px", color: "var(--dash-text-muted)", lineHeight: 1.2, margin: 0 }}>Pro Plan</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ─── MAIN AREA ─── */}
      <div className="md-main-offset" style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: "100vh", overflow: "hidden", background: "var(--dash-bg)" }}>
        
        {/* Top Navbar */}
        <header style={{
          height: "64px",
          background: "var(--dash-nav-bg)",
          borderBottom: "1px solid var(--dash-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          position: "sticky",
          top: 0,
          zIndex: 40,
        }}>
          {/* Menu button for mobile */}
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <button className="md-hidden" onClick={() => setIsMobileMenuOpen(true)} style={{ background: "none", border: "none", color: "var(--dash-text-main)" }}>
              <Menu size={24} />
            </button>
            {/* Search */}
            <div style={{ position: "relative", width: "100%", maxWidth: "360px" }} className="mobile-search-hidden">
              <svg style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)", color: "var(--dash-text-muted)" }} width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <input
                type="text"
                placeholder="Search..."
                style={{
                  width: "100%", height: "38px", background: "var(--dash-input-bg)", border: "1px solid var(--dash-border)", borderRadius: "10px",
                  paddingLeft: "40px", paddingRight: "60px", fontSize: "13px", color: "var(--dash-text-main)", outline: "none",
                }}
              />
            </div>
          </div>

          {/* Right side */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button style={{ position: "relative", width: "38px", height: "38px", background: "var(--dash-input-bg)", border: "1px solid var(--dash-border)", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "var(--dash-text-muted)" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
              <span style={{ position: "absolute", top: "7px", right: "7px", width: "8px", height: "8px", background: "#EF4444", borderRadius: "50%", border: "2px solid var(--dash-card-bg)" }}></span>
            </button>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "4px 8px 4px 4px", background: "var(--dash-input-bg)", border: "1px solid var(--dash-border)", borderRadius: "10px", cursor: "pointer" }}>
              <div style={{ width: "30px", height: "30px", borderRadius: "8px", background: "linear-gradient(135deg, #14B8A6, #0EA5E9)", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: "12px", fontWeight: 700 }}>
                N
              </div>
              <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--dash-text-main)" }} className="mobile-search-hidden">Nitish</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="dashboard-content-scroll" style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
          {children}
        </main>
      </div>
    </div>
  );
}

function NavItem({ href, label, active, children }: { href: string; label: string; active?: boolean; children: React.ReactNode }) {
  return (
    <Link href={href} style={{
      display: "flex", alignItems: "center", gap: "10px",
      padding: "8px 10px", borderRadius: "8px", textDecoration: "none",
      fontSize: "13.5px", fontWeight: active ? 600 : 500,
      color: active ? "#14B8A6" : "var(--dash-text-muted)",
      background: active ? "var(--dash-accent)" : "transparent",
      transition: "all 0.15s",
    }}>
      <span style={{ color: active ? "#14B8A6" : "var(--dash-text-muted)", flexShrink: 0 }}>{children}</span>
      {label}
    </Link>
  );
}
