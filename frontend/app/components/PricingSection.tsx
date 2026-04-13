"use client";

import React, { useState } from "react";
import Link from "next/link";

// ─── Plan ladder: the 5 snap points on the slider ────────────────────────────
const PRO_TIERS = [
  { value: 0,  shorts: 50,  price: 10,  tier: "pro_50"  },
  { value: 1,  shorts: 100, price: 19,  tier: "pro_100" },
  { value: 2,  shorts: 200, price: 30,  tier: "pro_200" },
  { value: 3,  shorts: 400, price: 49,  tier: "pro_400" },
  { value: 4,  shorts: 500, price: 57,  tier: "pro_500" },
];

const TICK_LABELS = ["50", "100", "200", "400", "500"];

function getAuthToken() {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp('(^| )access_token=([^;]+)'));
  return match ? match[2] : null;
}

async function startCheckout(tier: string): Promise<void> {
  // Try dynamic env, fallback to localhost. 
  // In a client component, NEXT_PUBLIC_API_URL is injected by Webpack.
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const headers: HeadersInit = { "Content-Type": "application/json" };
    const token = getAuthToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_URL}/payments/checkout`, {
      method: "POST",
      headers,
      // Important to use include to send cookies to the cross-origin API
      credentials: "include",
      body: JSON.stringify({
        tier,
        success_url: `${window.location.origin}/dashboard?payment=success`,
        cancel_url:  `${window.location.origin}?payment=cancelled`,
      }),
    });
    
    if (!res.ok) {
      if (res.status === 401) {
        // Not logged in, send to OAuth endpoint
        window.location.href = `${API_URL}/auth/google`;
        return;
      }
      throw new Error("Checkout failed");
    }
    const data = await res.json();
    window.location.href = data.checkout_url;
  } catch (e) {
    alert("Could not start checkout. Please try again.");
  }
}

export default function PricingSection() {
  const [sliderIdx, setSliderIdx] = useState(0);
  const [loading, setLoading] = useState(false);

  const activeTier = PRO_TIERS[sliderIdx];
  const pricePer = (activeTier.price / activeTier.shorts).toFixed(2);

  const handleCheckout = async () => {
    setLoading(true);
    await startCheckout(activeTier.tier);
    setLoading(false);
  };

  const loginUrl = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/auth/google` : "http://localhost:8000/auth/google";

  return (
    <div style={{ width: "100%", maxWidth: "1200px", margin: "0 auto", padding: "0 24px" }} id="pricing">
      
      <div style={{ textAlign: "center", marginBottom: "56px" }}>
        <h2 style={{ fontSize: "clamp(32px, 5vw, 48px)", fontWeight: 800, margin: "0 0 16px", letterSpacing: "-1px", lineHeight: 1.1 }}>
          Simple, transparent pricing
        </h2>
        <p style={{ fontSize: "18px", color: "rgba(255,255,255,0.6)", maxWidth: "480px", margin: "0 auto", lineHeight: 1.6 }}>
          Start free. Scale when you&apos;re ready. Cancel anytime.
        </p>
      </div>

      <div style={{
        display: "flex", gap: "24px", justifyContent: "center", alignItems: "stretch",
        flexWrap: "wrap", margin: "0 auto",
      }}>

        {/* ── FREE CARD ─────────────────────────────────────────────────────── */}
        <div style={{
          flex: "1", minWidth: "300px", maxWidth: "420px",
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "24px", padding: "36px 32px",
          display: "flex", flexDirection: "column",
          transition: "transform 0.2s",
        }}>
          {/* Badge */}
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(255,255,255,0.07)", borderRadius: "8px", padding: "4px 12px", marginBottom: "24px", width: "fit-content" }}>
            <span style={{ fontSize: "12px", fontWeight: 700, color: "#94A3B8", letterSpacing: "0.5px", textTransform: "uppercase" }}>Free</span>
          </div>

          {/* Price */}
          <div style={{ marginBottom: "8px" }}>
            <span style={{ fontSize: "52px", fontWeight: 800, letterSpacing: "-2px", color: "#F8FAFC" }}>$0</span>
            <span style={{ fontSize: "16px", color: "#64748B", marginLeft: "6px" }}>/month</span>
          </div>
          <p style={{ fontSize: "14px", color: "#64748B", margin: "0 0 32px", lineHeight: 1.5 }}>
            Try ShortClipr risk-free. No card needed.
          </p>

          <div style={{ height: "1px", background: "rgba(255,255,255,0.06)", marginBottom: "28px" }} />

          {/* Features */}
          <ul style={{ listStyle: "none", margin: "0 0 36px", padding: 0, display: "flex", flexDirection: "column", gap: "14px" }}>
            {[
              "3 shorts per month",
              "All 20 viral templates",
              "AI-powered 9:16 reframing",
              "Auto captions (word-level)",
              "720p export quality",
            ].map((f) => (
              <li key={f} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "14px", color: "#CBD5E1" }}>
                <span style={{ width: "18px", height: "18px", borderRadius: "50%", background: "rgba(20,184,166,0.15)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#14B8A6" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                </span>
                {f}
              </li>
            ))}
            <li style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "14px", color: "#475569" }}>
              <span style={{ width: "18px", height: "18px", borderRadius: "50%", background: "rgba(255,255,255,0.04)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </span>
              Full HD 1080p export
            </li>
          </ul>

          <div style={{ marginTop: "auto" }}>
            <a href={loginUrl} style={{
              display: "block", textAlign: "center", padding: "14px",
              borderRadius: "12px", fontSize: "15px", fontWeight: 600,
              color: "#94A3B8", background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.1)", textDecoration: "none",
              transition: "all 0.15s",
            }}>
              Start for free
            </a>
          </div>
        </div>

        {/* ── PRO CARD ──────────────────────────────────────────────────────── */}
        <div style={{
          flex: "1", minWidth: "300px", maxWidth: "420px",
          background: "linear-gradient(160deg, rgba(20,184,166,0.12) 0%, rgba(14,165,233,0.08) 100%)",
          border: "1px solid rgba(20,184,166,0.3)",
          borderRadius: "24px", padding: "36px 32px",
          display: "flex", flexDirection: "column", position: "relative", overflow: "hidden",
          boxShadow: "0 0 60px rgba(20,184,166,0.12)",
        }}>
          {/* Glow decoration */}
          <div style={{ position: "absolute", top: "-60px", right: "-60px", width: "200px", height: "200px", background: "radial-gradient(circle,rgba(20,184,166,0.2),transparent 70%)", pointerEvents: "none" }} />

          {/* Popular badge */}
          <div style={{ position: "absolute", top: "24px", right: "24px", background: "linear-gradient(135deg,#14B8A6,#0EA5E9)", borderRadius: "8px", padding: "4px 12px" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "white", letterSpacing: "0.5px", textTransform: "uppercase" }}>Most Popular</span>
          </div>

          {/* Badge */}
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(20,184,166,0.15)", border: "1px solid rgba(20,184,166,0.3)", borderRadius: "8px", padding: "4px 12px", marginBottom: "24px", width: "fit-content" }}>
            <span style={{ fontSize: "12px", fontWeight: 700, color: "#14B8A6", letterSpacing: "0.5px", textTransform: "uppercase" }}>Pro</span>
          </div>

          {/* Dynamic price */}
          <div style={{ marginBottom: "6px" }}>
            <span style={{ fontSize: "52px", fontWeight: 800, letterSpacing: "-2px", color: "#F8FAFC", transition: "all 0.2s" }}>
              ${activeTier.price}
            </span>
            <span style={{ fontSize: "16px", color: "#64748B", marginLeft: "6px" }}>/month</span>
          </div>
          <p style={{ fontSize: "13px", color: "#64748B", margin: "0 0 6px" }}>
            {activeTier.shorts} shorts · ${pricePer} per short
          </p>
          <p style={{ fontSize: "14px", color: "#94A3B8", margin: "0 0 28px", lineHeight: 1.5 }}>
            Full power. Ship viral content at scale.
          </p>

          {/* ── SLIDER ──────────────────────────────────────────────────────── */}
          <div style={{ background: "rgba(0,0,0,0.25)", borderRadius: "16px", padding: "20px 20px 16px", marginBottom: "28px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "14px" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#64748B", letterSpacing: "0.5px", textTransform: "uppercase" }}>Shorts per month</span>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#14B8A6" }}>{activeTier.shorts} shorts</span>
            </div>

            {/* Custom range input */}
            <div style={{ position: "relative", padding: "0 4px" }}>
              <input
                type="range"
                min={0}
                max={4}
                step={1}
                value={sliderIdx}
                onChange={(e) => setSliderIdx(Number(e.target.value))}
                style={{
                  width: "100%",
                  height: "6px",
                  appearance: "none",
                  WebkitAppearance: "none",
                  background: `linear-gradient(to right, #14B8A6 ${sliderIdx * 25}%, rgba(255,255,255,0.1) ${sliderIdx * 25}%)`,
                  borderRadius: "4px",
                  cursor: "pointer",
                  outline: "none",
                }}
              />
              <style>{`
                input[type=range]::-webkit-slider-thumb {
                  -webkit-appearance: none;
                  width: 22px; height: 22px;
                  border-radius: 50%;
                  background: linear-gradient(135deg, #14B8A6, #0EA5E9);
                  cursor: pointer;
                  border: 3px solid #0A0F1C;
                  box-shadow: 0 0 0 2px rgba(20,184,166,0.4);
                }
              `}</style>
              {/* Tick marks */}
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: "10px", padding: "0 2px" }}>
                {TICK_LABELS.map((label, i) => (
                  <button
                    key={label}
                    onClick={() => setSliderIdx(i)}
                    style={{
                      background: "none", border: "none", cursor: "pointer",
                      display: "flex", flexDirection: "column", alignItems: "center", gap: "4px", padding: 0,
                    }}
                  >
                    <div style={{ width: "2px", height: "6px", background: i <= sliderIdx ? "#14B8A6" : "rgba(255,255,255,0.15)", borderRadius: "1px" }} />
                    <span style={{ fontSize: "11px", fontWeight: i === sliderIdx ? 700 : 400, color: i === sliderIdx ? "#14B8A6" : "#475569", transition: "color 0.15s" }}>
                      {label}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Price breakdown */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px", paddingTop: "14px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
              <span style={{ fontSize: "12px", color: "#64748B" }}>Billed monthly</span>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "14px", fontWeight: 700, color: "#F8FAFC" }}>${activeTier.price}/mo</span>
                {activeTier.shorts >= 200 && (
                  <span style={{ fontSize: "10px", fontWeight: 700, background: "linear-gradient(135deg,#14B8A6,#0EA5E9)", padding: "2px 8px", borderRadius: "4px", color: "white" }}>
                    BEST VALUE
                  </span>
                )}
              </div>
            </div>
          </div>

          <div style={{ height: "1px", background: "rgba(255,255,255,0.06)", marginBottom: "24px" }} />

          {/* Features */}
          <ul style={{ listStyle: "none", margin: "0 0 36px", padding: 0, display: "flex", flexDirection: "column", gap: "14px" }}>
            {[
              `${activeTier.shorts} viral shorts per month`,
              "All 20 viral style templates",
              "GPT-4o content analysis",
              "AI face-tracking reframe (9:16)",
              "Word-level karaoke captions",
              "Full HD 1080p export",
              "Priority processing queue",
            ].map((f) => (
              <li key={f} style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "14px", color: "#CBD5E1" }}>
                <span style={{ width: "18px", height: "18px", borderRadius: "50%", background: "rgba(20,184,166,0.15)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#14B8A6" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                </span>
                {f}
              </li>
            ))}
          </ul>

          <div style={{ marginTop: "auto" }}>
            <button
              onClick={handleCheckout}
              disabled={loading}
              style={{
                width: "100%", padding: "16px",
                borderRadius: "12px", fontSize: "15px", fontWeight: 700,
                color: "white",
                background: loading ? "rgba(20,184,166,0.5)" : "linear-gradient(135deg,#14B8A6,#0EA5E9)",
                border: "none", cursor: loading ? "not-allowed" : "pointer",
                boxShadow: loading ? "none" : "0 6px 24px rgba(20,184,166,0.35)",
                transition: "all 0.2s", letterSpacing: "-0.2px",
              }}
            >
              {loading ? "Redirecting…" : `Get ${activeTier.shorts} Shorts — $${activeTier.price}/mo`}
            </button>
            <p style={{ textAlign: "center", fontSize: "12px", color: "#475569", margin: "10px 0 0" }}>
              Secure checkout · Cancel anytime · No hidden fees
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
