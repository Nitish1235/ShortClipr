import Image from "next/image";
import Link from "next/link";
import TemplateShowcase from "./components/TemplateShowcase";
import PricingSection from "./components/PricingSection";

export default function LandingPage() {
  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const LOGIN_URL = `${API}/auth/login`;

  return (
    <main>
      {/* ===================== NAVBAR ===================== */}
      <nav className="navbar">
        <a href="/" className="navbar-logo" style={{ display: "flex", alignItems: "center" }}>
          <Image src="/logo-horizontal-light.svg" alt="ShortClipr Logo" width={160} height={46} priority />
        </a>
        <ul className="navbar-links">
          <li><a href="#how-it-works">How It Works</a></li>
          <li><a href="#features">Features</a></li>
          <li><a href="#testimonials">Testimonials</a></li>
          <li><a href="#pricing">Pricing</a></li>
        </ul>
        <div className="navbar-actions">
          <a href={LOGIN_URL} className="btn-ghost">Log in</a>
          <a href={LOGIN_URL} className="btn-primary">Get Started Free</a>
        </div>
      </nav>

      {/* ===================== HERO ===================== */}
      <section className="hero" id="hero">
        <div style={{ marginBottom: "28px" }}>
          <Image src="/logo-horizontal-light.svg" alt="ShortClipr logo" width={140} height={40} priority />
        </div>

        <h1 className="hero-title animate-in">
          One upload. Multiple<br />viral-ready shorts.
        </h1>
        <p className="hero-subtitle animate-in delay-1">
          Smart AI finds the moments worth sharing.
        </p>

        <div className="hero-visual animate-in delay-2">
          {/* Left: Video Player */}
          <div className="video-player-mockup">
            <span className="video-label">Originating</span>
            <span className="video-sound-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" strokeWidth="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              </svg>
            </span>
            <Image
              src="/hero-beach.png"
              alt="Original video preview"
              width={520}
              height={300}
              className="video-thumb"
              priority
            />
            <div className="video-controls">
              <div className="play-btn">
                <svg viewBox="0 0 10 10">
                  <polygon points="2,1 9,5 2,9" />
                </svg>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" />
              </div>
              <div className="video-ctrl-icons">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                </svg>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2">
                  <polyline points="15 3 21 3 21 9" /><polyline points="9 21 3 21 3 15" />
                  <line x1="21" y1="3" x2="14" y2="10" /><line x1="3" y1="21" x2="10" y2="14" />
                </svg>
              </div>
            </div>
          </div>

          {/* Arrow */}
          <div className="hero-arrow">
            <svg viewBox="0 0 140 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M 10 80 C 30 80, 60 20, 90 30 C 110 37, 120 50, 128 58"
                stroke="#00B4A6"
                strokeWidth="3"
                strokeLinecap="round"
                fill="none"
              />
              <path
                d="M 118 52 L 128 58 L 120 66"
                stroke="#00B4A6"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
            </svg>
          </div>

          {/* Right: Shorts Stack */}
          <div className="shorts-stack">
            {/* Phone mockup */}
            <div style={{ position: 'relative', marginBottom: '4px' }}>
              <div className="phone-mockup-inner" style={{ width: '70px', marginLeft: 'auto', marginRight: '20px', marginBottom: '-20px', position: 'relative', zIndex: 5, borderRadius: '18px', border: '3px solid #333', overflow: 'hidden', boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}>
                <Image src="/short-clip-1.png" alt="Phone preview" width={70} height={140} style={{ objectFit: 'cover', width: '100%', height: '140px' }} />
              </div>
            </div>

            {/* Short Card 1 */}
            <div className="short-card">
              <span className="short-card-label">Your viral shorts</span>
              <Image
                src="/short-clip-1.png"
                alt="Viral short 1"
                width={220}
                height={130}
                className="short-thumb"
              />
            </div>

            {/* Short Card 2 */}
            <div className="short-card">
              <span className="short-card-label">Your viral shorts</span>
              <Image
                src="/short-clip-2.png"
                alt="Viral short 2"
                width={220}
                height={130}
                className="short-thumb"
              />
            </div>
          </div>
        </div>

        <a href={LOGIN_URL} className="btn-cta-large animate-in delay-3" id="hero-cta">
          Create My Shorts Now
        </a>
      </section>

      {/* ===================== HOW IT WORKS ===================== */}
      <section className="how-it-works" id="how-it-works">
        <p className="section-eyebrow">How It Works</p>
        <h2 className="section-title">
          From long video to viral<br />shorts in 3 simple steps
        </h2>

        <div className="steps-grid">
          {/* Step 1 */}
          <div className="step-card">
            <span className="step-number">1</span>
            <p className="step-number-main" style={{ color: '#0F1117', fontSize: '52px', fontWeight: '800', letterSpacing: '-2px', marginBottom: '8px' }}>1</p>
            <div className="step-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3D4450" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <h3 className="step-title">Upload your<br />long video</h3>
            <Image
              src="/campfire.png"
              alt="Upload video"
              width={200}
              height={110}
              className="step-thumb"
            />
          </div>

          {/* Step 2 — Highlighted */}
          <div className="step-card step-highlight">
            <p style={{ fontSize: '52px', fontWeight: '800', color: 'rgba(255,255,255,0.4)', letterSpacing: '-2px', marginBottom: '24px', lineHeight: 1 }}>2</p>
            <h3 className="step-title" style={{ color: 'white', fontSize: '20px', marginBottom: '32px' }}>
              AI finds the best<br />moments
            </h3>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <div style={{ width: '90px', height: '90px', position: 'relative' }}>
                <div style={{
                  width: '90px', height: '90px',
                  borderRadius: '50%',
                  border: '3px solid rgba(255,255,255,0.3)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  position: 'relative'
                }}>
                  <div style={{
                    width: '70px', height: '70px',
                    background: 'rgba(255,255,255,0.15)',
                    borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <span style={{ fontSize: '28px' }}>✦</span>
                  </div>
                  {/* Orbit dot */}
                  <div style={{
                    position: 'absolute', top: '-6px', left: '50%', transform: 'translateX(-50%)',
                    width: '12px', height: '12px',
                    background: 'white', borderRadius: '50%',
                    boxShadow: '0 0 12px rgba(255,255,255,0.8)'
                  }} />
                </div>
              </div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="step-card">
            <p style={{ fontSize: '52px', fontWeight: '800', color: '#0F1117', letterSpacing: '-2px', marginBottom: '8px', lineHeight: 1 }}>3</p>
            <h3 className="step-title" style={{ marginBottom: '16px' }}>Get ready-to-post<br />vertical shorts</h3>
            {/* Stacked phones visual */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', alignItems: 'center', marginTop: '8px' }}>
              {[1, 2, 3].map((i) => (
                <div key={i} style={{
                  width: i === 2 ? '60px' : '48px',
                  background: '#222',
                  borderRadius: '10px',
                  border: '2px solid #444',
                  overflow: 'hidden',
                  transform: i === 1 ? 'rotate(-8deg)' : i === 3 ? 'rotate(8deg)' : 'none',
                  boxShadow: '0 8px 20px rgba(0,0,0,0.3)',
                  zIndex: i === 2 ? 3 : 1,
                  position: 'relative'
                }}>
                  <Image
                    src={i % 2 === 0 ? "/short-clip-2.png" : "/short-clip-1.png"}
                    alt={`Short ${i}`} width={60} height={100}
                    style={{ objectFit: 'cover', width: '100%', height: i === 2 ? '100px' : '80px' }}
                  />
                  {i === 2 && (
                    <div style={{ position: 'absolute', top: '6px', left: '6px', width: '8px', height: '8px', background: '#ff5f57', borderRadius: '50%' }} />
                  )}
                  {i === 2 && (
                    <div style={{ position: 'absolute', top: '6px', left: '18px', width: '8px', height: '8px', background: '#febc2e', borderRadius: '50%' }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ===================== DARK / CLIPS SECTION ===================== */}
      <section className="dark-section" id="demo">
        <h2 className="dark-title">
          Turn hours of content into<br />scroll-stopping shorts
        </h2>
        <p className="dark-subtitle">
          AI analyzes speech, emotion, pacing &amp; virality to<br />
          extract your best moments automatically
        </p>

        <div style={{ marginTop: "40px", marginBottom: "40px" }}>
          <TemplateShowcase />
        </div>

        <a href={LOGIN_URL} className="btn-cta-large" id="see-action-cta">
          See It In Action
        </a>
      </section>

      {/* ===================== FEATURES ===================== */}
      <section className="features" id="features">
        <div style={{ marginBottom: "24px" }}>
           <Image src="/favicon.svg" alt="Ghost Logo" width={48} height={48} priority />
        </div>
        <div className="features-badge" id="features-badge">
          Feature highlights &nbsp;›
        </div>
        <h2 className="section-title">Everything you need to go viral</h2>

        <div className="features-grid">
          {/* Card 1 */}
          <div className="feature-card" id="feature-moment-detection">
            <div className="feature-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00B4A6" strokeWidth="2">
                <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            </div>
            <h3 className="feature-title">Smart Moment Detection</h3>
            <p className="feature-desc">
              AI scans your every clip to pinpoint peak engagement moments — laughs, drops, insights — that are proven to go viral.
            </p>
          </div>

          {/* Card 2 */}
          <div className="feature-card" id="feature-captions">
            <div className="feature-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00B4A6" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </div>
            <h3 className="feature-title">Auto Captions &amp; Timing</h3>
            <p className="feature-desc">
              Smart transcription syncs captions perfectly to every word. Styled, animated, and timed for maximum retention.
            </p>
          </div>

          {/* Card 3 */}
          <div className="feature-card" id="feature-reframing">
            <div className="feature-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00B4A6" strokeWidth="2">
                <rect x="5" y="2" width="14" height="20" rx="2" /><line x1="12" y1="18" x2="12" y2="18" />
              </svg>
            </div>
            <h3 className="feature-title">Perfect Vertical Reframing</h3>
            <p className="feature-desc">
              Automatically reframes landscape content to 9:16. Smart face tracking keeps subjects centered every time.
            </p>
          </div>

          {/* Card 4 */}
          <div className="feature-card" id="feature-viral-score">
            <div className="feature-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00B4A6" strokeWidth="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
            </div>
            <h3 className="feature-title">Viral Score Ranking</h3>
            <p className="feature-desc">
              Each clip gets a virality score based on emotion, pacing, and hooks. Focus on winners first, export the best.
            </p>
          </div>

          {/* Card 5 */}
          <div className="feature-card" id="feature-bulk-export">
            <div className="feature-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00B4A6" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </div>
            <h3 className="feature-title">Bulk Export</h3>
            <p className="feature-desc">
              Export dozens of ready-to-post shorts in one click — optimized for TikTok, YouTube Shorts, Instagram Reels, and podcasts.
            </p>
          </div>

          {/* Card 6 */}
          <div className="feature-card feature-special" id="feature-any-content">
            <div className="feature-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00B4A6" strokeWidth="2">
                <rect x="2" y="3" width="20" height="14" rx="2" />
                <line x1="8" y1="21" x2="16" y2="21" />
                <line x1="12" y1="17" x2="12" y2="21" />
              </svg>
            </div>
            <h3 className="feature-title">Works with any content<br />(talking heads, vlogs, podcasts)</h3>
            <p className="feature-desc">
              Interviews, webinars, podcasts, live streams — ShortClipr handles any format with equal precision.
            </p>
            <div className="feature-illustration">
              <svg width="80" height="80" viewBox="0 0 100 100" fill="none">
                <rect x="10" y="20" width="65" height="50" rx="8" fill="#DDE1E6" stroke="#CBD0D6" strokeWidth="2" />
                <rect x="14" y="24" width="57" height="38" rx="5" fill="#C8CDD2" />
                <rect x="25" y="74" width="35" height="6" rx="3" fill="#CBD0D6" />
                <circle cx="78" cy="38" r="15" fill="#00B4A6" opacity="0.15" />
                <circle cx="78" cy="38" r="10" fill="#00B4A6" opacity="0.3" />
                <polygon points="75,34 83,38 75,42" fill="#00B4A6" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* ===================== TESTIMONIALS ===================== */}
      <section className="testimonials" id="testimonials">
        <h2 className="testimonials-title">Creators are loving ShortClipr</h2>

        <div className="testimonials-grid">
          {/* Testimonial 1 */}
          <div className="testimonial-card" id="testimonial-alex">
            <div className="quote-mark">&ldquo;</div>
            <p className="testimonial-text">ShortClipr made my life so much easier!</p>
            <Image
              src="/avatar-alex.png"
              alt="Alex Johnson"
              width={44}
              height={44}
              className="testimonial-avatar"
            />
            <p className="testimonial-name">Alex Johnson</p>
            <p className="testimonial-meta">Generated 87 viral shorts from one 2-hour webinar</p>
          </div>

          {/* Testimonial 2 */}
          <div className="testimonial-card" id="testimonial-sam">
            <div className="quote-mark">&ldquo;</div>
            <p className="testimonial-text">Incredible tool for content creators</p>
            <Image
              src="/avatar-sam.png"
              alt="Sam Lee"
              width={44}
              height={44}
              className="testimonial-avatar"
            />
            <p className="testimonial-name">Sam Lee</p>
            <p className="testimonial-meta">Saved 20+ hours per week</p>
          </div>

          {/* Testimonial 3 */}
          <div className="testimonial-card" id="testimonial-taylor">
            <div className="quote-mark">&ldquo;</div>
            <p className="testimonial-text">Best investment for my channel</p>
            <Image
              src="/avatar-taylor.png"
              alt="Taylor Kim"
              width={44}
              height={44}
              className="testimonial-avatar"
            />
            <p className="testimonial-name">Taylor Kim</p>
            <p className="testimonial-meta">Doubled my engagement in 3 months</p>
          </div>
        </div>

        {/* Trusted by line */}
        <div className="trusted-by">
          <span>Used by creators from</span>
          <div className="trusted-logos">
            <span className="trusted-logo">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="#ff0050"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.34 6.34 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.27 8.27 0 004.84 1.56V6.79a4.85 4.85 0 01-1.07-.1z" /></svg>
              TikTok,
            </span>
            <span className="trusted-logo">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="#ff0000"><path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" /></svg>
              YouTube &amp;
            </span>
            <span className="trusted-logo">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="url(#ig-grad)">
                <defs>
                  <linearGradient id="ig-grad" x1="0%" y1="100%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#f09433" />
                    <stop offset="25%" stopColor="#e6683c" />
                    <stop offset="50%" stopColor="#dc2743" />
                    <stop offset="75%" stopColor="#cc2366" />
                    <stop offset="100%" stopColor="#bc1888" />
                  </linearGradient>
                </defs>
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
              </svg>
              Instagram
            </span>
          </div>
        </div>
      </section>

      {/* ===================== PRICING SECTION ===================== */}
      <PricingSection />

      {/* ===================== FOOTER CTA ===================== */}
      <footer className="footer-cta" id="pricing">
        <h2 className="footer-cta-title">Start creating viral shorts today</h2>
        <p className="footer-cta-sub">No credit card required. 3 free shorts every week.</p>
        <a href={LOGIN_URL} className="btn-cta-large" id="footer-cta-btn">
          Create My Shorts Now — It&apos;s Free
        </a>

        <div className="footer-links">
          <span className="footer-brand" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <img src="/favicon.svg" alt="Ghost" width="24" height="24" />
            © 2025 ShortClipr
          </span>
          <a href="/privacy">Privacy Policy</a>
          <a href="/terms">Terms of Service</a>
          <a href="/contact">Contact</a>
          <a href="/blog">Blog</a>
        </div>
      </footer>
    </main>
  );
}
