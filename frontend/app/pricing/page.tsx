"use client";

import Link from "next/link";
import PricingSection from "../components/PricingSection";

export default function PricingPage() {
  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0A0F1C 0%, #0F172A 50%, #0A0F1C 100%)",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      color: "#F8FAFC",
    }}>
      {/* Nav */}
      <nav style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "20px 48px", borderBottom: "1px solid rgba(255,255,255,0.06)",
        position: "sticky", top: 0, zIndex: 50,
        background: "rgba(10,15,28,0.85)", backdropFilter: "blur(16px)",
      }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", textDecoration: "none" }}>
          <img src="/logo-horizontal-dark.svg" alt="ShortClipr Logo" style={{ width: "140px", height: "40px" }} />
        </Link>
        <div style={{ display: "flex", gap: "8px" }}>
          <Link href="/dashboard" style={{ padding: "8px 20px", borderRadius: "8px", fontSize: "14px", fontWeight: 600, color: "#94A3B8", textDecoration: "none" }}>Dashboard</Link>
        </div>
      </nav>

      {/* Pricing Extracted Section */}
      <div style={{ paddingTop: "72px", paddingBottom: "100px" }}>
        <PricingSection />
      </div>

      {/* FAQ strip */}
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", padding: "64px 24px 80px", maxWidth: "720px", margin: "0 auto" }}>
        <h2 style={{ fontSize: "22px", fontWeight: 700, textAlign: "center", marginBottom: "40px", letterSpacing: "-0.5px" }}>Common questions</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {[
            { q: "What counts as one 'short'?", a: "Each clip generated from your long-form video counts as one short. A 60-minute video could produce 3–10 clips depending on your settings." },
            { q: "Do unused credits roll over?", a: "Credits reset at the beginning of each monthly billing cycle. Unused credits do not carry over." },
            { q: "Can I change my plan mid-month?", a: "Yes, you can upgrade anytime. Your new credit limit applies immediately and the billing difference is prorated." },
            { q: "What payment methods are accepted?", a: "All major cards (Visa, MasterCard, Amex) are accepted via Dodo Payments. Apple Pay and Google Pay are also supported." },
          ].map(({ q, a }) => (
            <div key={q} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "24px" }}>
              <p style={{ fontSize: "15px", fontWeight: 600, color: "#F1F5F9", margin: "0 0 8px" }}>{q}</p>
              <p style={{ fontSize: "14px", color: "#64748B", margin: 0, lineHeight: 1.6 }}>{a}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Slider thumb global style */}
      <style>{`
        #shorts-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 22px; height: 22px;
          border-radius: 50%;
          background: linear-gradient(135deg, #14B8A6, #0EA5E9);
          cursor: pointer;
          border: 3px solid #0A0F1C;
          box-shadow: 0 0 0 2px rgba(20,184,166,0.4);
          transition: box-shadow 0.15s;
        }
        #shorts-slider::-webkit-slider-thumb:hover {
          box-shadow: 0 0 0 6px rgba(20,184,166,0.25);
        }
        #shorts-slider::-moz-range-thumb {
          width: 22px; height: 22px;
          border-radius: 50%;
          background: linear-gradient(135deg, #14B8A6, #0EA5E9);
          cursor: pointer;
          border: 3px solid #0A0F1C;
        }
      `}</style>
    </div>
  );
}
