"use client";

import React from "react";
import Image from "next/image";

export default function TemplateShowcase() {
  return (
    <div className="clips-grid" style={{ marginBottom: "60px", marginTop: "20px" }}>
      {/* ── FAR LEFT ───────────────────────────────── */}
      <div className="clip-card clip-far">
        <div className="clip-bars">
          <div className="bar" /><div className="bar" /><div className="bar" />
        </div>
        <Image 
          src="/templates/meme_style_native_1776018901233.png" 
          alt="Meme Style Template" 
          width={110} 
          height={195} 
          className="clip-img" 
          style={{ objectFit: 'cover' }}
        />
      </div>

      {/* ── SIDE LEFT ──────────────────────────────── */}
      <div className="clip-card clip-side">
        <div className="clip-bars">
          <div className="bar" /><div className="bar" /><div className="bar" />
        </div>
        <Image 
          src="/templates/luxury_shock_native_1776018883781.png" 
          alt="Luxury Shock Template" 
          width={140} 
          height={249} 
          className="clip-img" 
          style={{ objectFit: 'cover' }}
        />
        <div className="clip-play-overlay">
          <div className="clip-play-btn">
            <svg viewBox="0 0 10 10"><polygon points="2,1 9,5 2,9" /></svg>
          </div>
        </div>
      </div>

      {/* ── CENTER / ACTIVE ────────────────────────── */}
      <div className="clip-card clip-active">
        <div className="clip-bars">
          <div className="bar" /><div className="bar" /><div className="bar" />
        </div>
        <Image 
          src="/templates/viral_hook_native_1776018863829.png" 
          alt="Viral Hook Template" 
          width={180} 
          height={320} 
          className="clip-img" 
          style={{ objectFit: 'cover' }}
        />
        <div className="clip-play-overlay">
          <div className="clip-play-btn">
            <svg viewBox="0 0 10 10"><polygon points="2,1 9,5 2,9" /></svg>
          </div>
        </div>
      </div>

      {/* ── SIDE RIGHT ─────────────────────────────── */}
      <div className="clip-card clip-side">
        <div className="clip-bars">
          <div className="bar" /><div className="bar" /><div className="bar" />
        </div>
        <Image 
          src="/templates/epic_pov_native_1776018846496.png" 
          alt="Epic POV Template" 
          width={140} 
          height={249} 
          className="clip-img" 
          style={{ objectFit: 'cover' }} 
        />
        <div className="clip-play-overlay">
          <div className="clip-play-btn">
            <svg viewBox="0 0 10 10"><polygon points="2,1 9,5 2,9" /></svg>
          </div>
        </div>
      </div>

      {/* ── FAR RIGHT ──────────────────────────────── */}
      <div className="clip-card clip-far">
        <div className="clip-bars">
          <div className="bar" /><div className="bar" /><div className="bar" />
        </div>
        <Image 
          src="/templates/satisfying_reveal_native_1776018924616.png" 
          alt="Satisfying Reveal Template" 
          width={110} 
          height={195} 
          className="clip-img" 
          style={{ objectFit: 'cover' }}
        />
      </div>
    </div>
  );
}
