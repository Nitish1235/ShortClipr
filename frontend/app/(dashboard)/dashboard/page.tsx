"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";

// ─── Types ────────────────────────────────────────────────────────────────────
type ShortsCount = "auto" | 1 | 3 | 5;
type ClipResult = {
  clip_id:       string;
  clip_url:      string;
  thumbnail_url: string;
  duration:      number;
  top_title:     string;
  bottom_tag:    string;
  template_id:   string;
  viral_score:   number;
};
type Job = {
  job_id:       string;
  status:       string;
  progress:     number;
  current_step: string;
  clip_count:   number;
  clips:        ClipResult[];
  created_at:   string;
  options:      Record<string, unknown>;
};
type UserStats = {
  shorts_generated:  number;
  shorts_limit:      number;
  shorts_remaining:  number;
  subscription_tier: string;
  jobs_total?:       number;
  jobs_completed?:   number;
  clips_generated?:  number;
};

// ─── Template catalog ─────────────────────────────────────────────────────────
const TEMPLATES = [
  { id: "none",                name: "Standard AI",         emoji: "🤖", desc: "Basic editing algorithm" },
  { id: "viral-hook",          name: "Viral Hook",          emoji: "🔥", desc: "Big hook + zoom-in", image: "/templates/viral-hook.jpg" },
  { id: "satisfying-reveal",   name: "Satisfying Reveal",   emoji: "🏆", desc: "Cinema reveal", image: "/templates/satisfying-reveal.jpg" },
  { id: "luxury-shock",        name: "Luxury Shock",        emoji: "✨", desc: "Glow + luxury", image: "/templates/luxury-shock.jpg" },
  { id: "epic-pov",            name: "Epic POV",            emoji: "⛰️", desc: "POV letterbox", image: "/templates/epic-pov.jpg" },
  { id: "life-changing",       name: "Life Changing",       emoji: "🌟", desc: "Soft vignette", image: "/templates/life-changing.jpg" },
  { id: "peak-satisfaction",   name: "Peak Satisfaction",   emoji: "🔝", desc: "Cinema-crisp", image: "/templates/peak-satisfaction.jpg" },
  { id: "plot-twist-reaction", name: "Plot Twist Reaction", emoji: "😱", desc: "Strong face glow", image: "/templates/plot-twist-reaction.jpg" },
  { id: "luxury-reveal",       name: "Luxury Reveal",       emoji: "💎", desc: "High-gloss shine", image: "/templates/luxury-reveal.jpg" },
  { id: "cinematic-focus",     name: "Cinematic Focus",     emoji: "🎬", desc: "Letterbox focus", image: "/templates/cinematic-focus.jpg" },
  { id: "satisfying-asmr",     name: "Satisfying ASMR",     emoji: "🎧", desc: "Soft warmth", image: "/templates/satisfying-asmr.jpg" },
  { id: "plot-twist",          name: "Plot Twist",          emoji: "😲", desc: "Warm face glow", image: "/templates/plot-twist.jpg" },
  { id: "dreamy-transition",   name: "Dreamy Transition",   emoji: "🌙", desc: "Dream blur", image: "/templates/dreamy-transition.jpg" },
  { id: "flex-mode",           name: "Flex Mode",           emoji: "💰", desc: "High contrast", image: "/templates/flex-mode.jpg" },
  { id: "emotional-hit",       name: "Emotional Hit",       emoji: "💔", desc: "Muted blur", image: "/templates/emotional-hit.jpg" },
  { id: "trend-jack",          name: "Trend Jack",          emoji: "🚀", desc: "Snap zoom", image: "/templates/trend-jack.jpg" },
  { id: "full-stack",          name: "Full Stack",          emoji: "🎯", desc: "Full cinematic", image: "/templates/full-stack.jpg" },
  { id: "minimal-clean",       name: "Minimal Clean",       emoji: "⬜", desc: "Pure minimal", image: "/templates/minimal-clean.jpg" },
  { id: "max-energy",          name: "Max Energy",          emoji: "⚡", desc: "Glow + zoom", image: "/templates/max-energy.jpg" },
];

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getAuthToken() {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp('(^| )access_token=([^;]+)'));
  return match ? match[2] : null;
}

async function apiFetch(path: string, opts?: RequestInit) {
  const headers = new Headers(opts?.headers || {});
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  
  const token = getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    ...opts,
    headers,
  });
  
  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      window.location.href = `${API}/auth/google`; // auto-redirect to login
    }
    throw new Error(`${res.status}: ${await res.text()}`);
  }
  return res.json();
}

// ─── Colour helpers ───────────────────────────────────────────────────────────
const STATUS_COLOR: Record<string, string> = {
  pending:    "#F59E0B",
  queued:     "#6366F1",
  processing: "#14B8A6",
  completed:  "#10B981",
  failed:     "#EF4444",
  cancelled:  "var(--dash-text-muted)",
};
const STATUS_BG: Record<string, string> = {
  pending:    "#FFFBEB",
  queued:     "#EEF2FF",
  processing: "#F0FDFA",
  completed:  "#ECFDF5",
  failed:     "#FEF2F2",
  cancelled:  "var(--dash-input-bg)",
};

// ─────────────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  // ── Input state ───────────────────────────────────────────────────────────
  const [youtubeUrl,       setYoutubeUrl]       = useState("");
  const [dragActive,       setDragActive]        = useState(false);
  const [uploadFile,       setUploadFile]        = useState<File | null>(null);

  // ── Generator options ─────────────────────────────────────────────────────
  const [shortsCount,      setShortsCount]       = useState<ShortsCount>("auto");
  const [selectedTemplate, setSelectedTemplate]  = useState("none");
  const [autoCaptions,     setAutoCaptions]      = useState(true);
  const [verticalFormat,   setVerticalFormat]    = useState(true);
  const [viralFilter,      setViralFilter]       = useState(false);
  const [clipMinSec,       setClipMinSec]        = useState(15);
  const [clipMaxSec,       setClipMaxSec]        = useState(60);
  const [language,         setLanguage]          = useState("en");

  // ── UI state ──────────────────────────────────────────────────────────────
  const [activeTab,        setActiveTab]         = useState<"create"|"jobs"|"clips">("create");
  const [isSubmitting,     setIsSubmitting]      = useState(false);
  const [error,            setError]             = useState<string|null>(null);
  const [successJobId,     setSuccessJobId]      = useState<string|null>(null);

  // ── Data state ────────────────────────────────────────────────────────────
  const [jobs,             setJobs]              = useState<Job[]>([]);
  const [stats,            setStats]             = useState<UserStats|null>(null);
  const [loadingJobs,      setLoadingJobs]       = useState(false);
  const [expandedJob,      setExpandedJob]       = useState<string|null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef      = useRef<NodeJS.Timeout|null>(null);

  // ── Load user stats on mount ──────────────────────────────────────────────
  useEffect(() => {
    apiFetch("/users/me/stats")
      .then(setStats)
      .catch(() => null);
  }, []);

  // ── Load jobs when Jobs tab active ────────────────────────────────────────
  const loadJobs = useCallback(async () => {
    setLoadingJobs(true);
    try {
      const data = await apiFetch("/jobs?limit=20");
      setJobs(Array.isArray(data) ? data : []);
    } catch {
      /* silent */
    } finally {
      setLoadingJobs(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "jobs") {
      loadJobs();
      pollRef.current = setInterval(loadJobs, 6000);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [activeTab, loadJobs]);

  // ── Drag/drop ─────────────────────────────────────────────────────────────
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith("video/")) setUploadFile(file);
  };

  // ── Submit job ────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    if (!youtubeUrl.trim() && !uploadFile) return;
    setIsSubmitting(true);
    setError(null);
    setSuccessJobId(null);

    try {
      let videoUrl: string | null = null;

      // If file upload, upload to GCS first via /videos/upload
      if (uploadFile) {
        const form = new FormData();
        form.append("file", uploadFile);
        const headers = new Headers();
        const token = getAuthToken();
        if (token) headers.set("Authorization", `Bearer ${token}`);

        const uploadRes = await fetch(`${API}/videos/upload`, {
          method: "POST", credentials: "include", body: form, headers
        });
        if (!uploadRes.ok) throw new Error("Upload failed");
        const { url } = await uploadRes.json();
        videoUrl = url;
      }

      const payload = {
        youtube_url:  youtubeUrl.trim() || null,
        video_url:    videoUrl,
        template_id:  selectedTemplate === "none" ? null : selectedTemplate,
        options: {
          shorts_count:   shortsCount,
          auto_captions:  autoCaptions,
          vertical:       verticalFormat,
          viral_filter:   viralFilter,
          clip_min_sec:   clipMinSec,
          clip_max_sec:   clipMaxSec,
          language,
        },
      };

      const job = await apiFetch("/jobs", { method: "POST", body: JSON.stringify(payload) });
      setSuccessJobId(job.job_id);
      setYoutubeUrl("");
      setUploadFile(null);

      // Refresh stats
      apiFetch("/users/me/stats").then(setStats).catch(() => null);

      // Switch to Jobs tab
      setTimeout(() => { setActiveTab("jobs"); loadJobs(); }, 1200);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Something went wrong";
      if (msg.includes("402")) setError("Credit limit reached. Please upgrade your plan.");
      else setError(msg.slice(0, 120));
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeTempl = TEMPLATES.find(t => t.id === selectedTemplate)!;
  const credPct     = stats ? Math.round((stats.shorts_generated / stats.shorts_limit) * 100) : 0;

  return (
    <div style={{ maxWidth: "1240px", margin: "0 auto", padding: "0 4px" }}>

      {/* ── TOP HEADER ───────────────────────────────────────────────── */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: "28px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "26px", fontWeight: 800, color: "var(--dash-text-main)", margin: 0, letterSpacing: "-0.5px" }}>
            Dashboard
          </h1>
          <p style={{ fontSize: "14px", color: "var(--dash-text-muted)", margin: "4px 0 0" }}>
            Turn long videos into viral shorts with AI
          </p>
        </div>

        {/* Shorts bar */}
        {stats && (
          <div style={{ background: "var(--dash-card-bg)", border: "1px solid #E5E7EB", borderRadius: "12px", padding: "12px 18px", display: "flex", alignItems: "center", gap: "16px" }}>
            {/* Numbers */}
            <div>
              <p style={{ fontSize: "11px", color: "var(--dash-text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.6px", margin: "0 0 3px" }}>Shorts</p>
              <p style={{ fontSize: "15px", fontWeight: 800, color: "var(--dash-text-main)", margin: 0, lineHeight: 1 }}>
                {stats.shorts_generated}
                <span style={{ color: "var(--dash-text-muted)", fontWeight: 400, fontSize: "13px" }}> / {stats.shorts_limit}</span>
              </p>
            </div>

            {/* Progress bar */}
            <div style={{ width: "88px" }}>
              {(() => {
                const pct = Math.min(100, Math.round((stats.shorts_generated / stats.shorts_limit) * 100));
                const barColor = pct >= 90 ? "#EF4444" : pct >= 70 ? "#F59E0B" : "#14B8A6";
                return (
                  <>
                    <div style={{ height: "6px", background: "var(--dash-hover)", borderRadius: "4px", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${pct}%`, background: barColor, borderRadius: "4px", transition: "width 0.4s" }} />
                    </div>
                    <p style={{ fontSize: "10px", color: barColor, margin: "3px 0 0", textAlign: "right", fontWeight: 600 }}>
                      {stats.shorts_remaining} left
                    </p>
                  </>
                );
              })()}
            </div>

            {/* Upgrade CTA */}
            {stats.subscription_tier === "free" && (
              <Link href="/pricing" style={{ background: "linear-gradient(135deg,#14B8A6,#0EA5E9)", color: "white", padding: "7px 14px", borderRadius: "8px", fontSize: "12px", fontWeight: 700, textDecoration: "none", whiteSpace: "nowrap", boxShadow: "0 3px 10px rgba(20,184,166,0.3)" }}>
                Get More ↑
              </Link>
            )}
          </div>
        )}
      </div>

      {/* ── TABS ─────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: "4px", background: "var(--dash-hover)", borderRadius: "12px", padding: "4px", marginBottom: "28px", width: "fit-content" }}>
        {(["create","jobs","clips"] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: "8px 22px", borderRadius: "9px", border: "none", cursor: "pointer",
            fontSize: "13px", fontWeight: 600, transition: "all 0.15s",
            background: activeTab === tab ? "var(--dash-card-bg)" : "transparent",
            color: activeTab === tab ? "var(--dash-text-main)" : "var(--dash-text-muted)",
            boxShadow: activeTab === tab ? "0 1px 6px rgba(0,0,0,0.08)" : "none",
          }}>
            {tab === "create" ? "✦ Create" : tab === "jobs" ? "⚙ Jobs" : "▶ My Clips"}
          </button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════════════════════
          TAB: CREATE
      ════════════════════════════════════════════════════════════════ */}
      {activeTab === "create" && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "20px", alignItems: "start" }}>

          {/* ── LEFT: Options panel ─────────────────────────────────── */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", flex: "1 1 300px", maxWidth: "360px" }}>

            {/* Generator Settings */}
            <Panel title="Generator Settings">
              {/* Output count */}
              <OptionGroup label="Number of Shorts">
                <div style={{ display: "flex", background: "var(--dash-hover)", borderRadius: "10px", padding: "3px", gap: "3px" }}>
                  {(["auto", 1, 3, 5] as const).map(v => (
                    <button key={v} onClick={() => setShortsCount(v)} style={{ flex: 1, padding: "7px 4px", borderRadius: "7px", border: "none", fontSize: "12px", fontWeight: 600, cursor: "pointer", transition: "all 0.15s", background: shortsCount === v ? "#14B8A6" : "transparent", color: shortsCount === v ? "white" : "var(--dash-text-muted)" }}>
                      {v === "auto" ? "Auto" : v}
                    </button>
                  ))}
                </div>
              </OptionGroup>

              {/* Clip duration range */}
              <OptionGroup label={`Clip Duration: ${clipMinSec}s – ${clipMaxSec}s`}>
                <div style={{ display: "flex", gap: "8px" }}>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: "10px", color: "var(--dash-text-muted)", margin: "0 0 4px", fontWeight: 600 }}>MIN</p>
                    <input type="range" min={10} max={30} step={5} value={clipMinSec}
                      onChange={e => setClipMinSec(Number(e.target.value))}
                      style={{ width: "100%", accentColor: "#14B8A6" }}
                    />
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: "10px", color: "var(--dash-text-muted)", margin: "0 0 4px", fontWeight: 600 }}>MAX</p>
                    <input type="range" min={30} max={90} step={10} value={clipMaxSec}
                      onChange={e => setClipMaxSec(Number(e.target.value))}
                      style={{ width: "100%", accentColor: "#14B8A6" }}
                    />
                  </div>
                </div>
              </OptionGroup>

              {/* Language */}
              <OptionGroup label="Video Language">
                <select value={language} onChange={e => setLanguage(e.target.value)}
                  style={{ width: "100%", padding: "8px 10px", background: "var(--dash-input-bg)", border: "1px solid #E5E7EB", borderRadius: "8px", fontSize: "13px", color: "var(--dash-text-main)", outline: "none", fontFamily: "inherit", cursor: "pointer" }}>
                  <option value="en">🇬🇧 English</option>
                  <option value="es">🇪🇸 Spanish</option>
                  <option value="fr">🇫🇷 French</option>
                  <option value="de">🇩🇪 German</option>
                  <option value="hi">🇮🇳 Hindi</option>
                  <option value="pt">🇧🇷 Portuguese</option>
                  <option value="ja">🇯🇵 Japanese</option>
                  <option value="zh">🇨🇳 Chinese</option>
                </select>
              </OptionGroup>
            </Panel>

            {/* Processing Options */}
            <Panel title="Processing Options">
              <Toggle label="Auto Captions"      hint="Word-level teal karaoke"  value={autoCaptions}  onChange={setAutoCaptions} />
              <Toggle label="Vertical 9:16"      hint="AI face-tracked reframe"  value={verticalFormat} onChange={setVerticalFormat} />
              <Toggle label="Viral Score Filter" hint="Keep highest-impact clips" value={viralFilter}   onChange={setViralFilter} />
            </Panel>

            {/* Active Template */}
            <div style={{ background: "linear-gradient(135deg,rgba(20,184,166,0.08),rgba(14,165,233,0.05))", border: "1px solid rgba(20,184,166,0.2)", borderRadius: "14px", padding: "16px" }}>
              <p style={{ fontSize: "11px", fontWeight: 700, color: "var(--dash-text-muted)", textTransform: "uppercase", letterSpacing: "0.6px", margin: "0 0 10px" }}>Active Template</p>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div style={{ width: "42px", height: "42px", borderRadius: "10px", background: "rgba(20,184,166,0.15)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "22px", flexShrink: 0 }}>
                  {activeTempl.emoji}
                </div>
                <div>
                  <p style={{ fontSize: "14px", fontWeight: 700, color: "#0F766E", margin: 0 }}>{activeTempl.name}</p>
                  <p style={{ fontSize: "11px", color: "var(--dash-text-muted)", margin: "2px 0 0" }}>{activeTempl.desc}</p>
                </div>
              </div>
            </div>
          </div>

          {/* ── RIGHT: Input + Template Grid ────────────────────────── */}
          <div style={{ display: "flex", flexDirection: "column", gap: "18px", flex: "2 1 400px", minWidth: 0 }}>

            {/* Drop Zone */}
            <div
              onDragEnter={handleDrag} onDragLeave={handleDrag}
              onDragOver={handleDrag} onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{ background: dragActive ? "#F0FDFA" : uploadFile ? "#F0FDFA" : "var(--dash-card-bg)", borderRadius: "18px", border: `2px dashed ${dragActive || uploadFile ? "#14B8A6" : "#D1D5DB"}`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "40px", transition: "all 0.2s", cursor: "pointer", textAlign: "center" }}
            >
              <input ref={fileInputRef} type="file" accept="video/*" style={{ display: "none" }}
                onChange={e => { const f = e.target.files?.[0]; if (f) setUploadFile(f); e.target.value = ""; }}
              />
              {uploadFile ? (
                <>
                  <div style={{ width: "52px", height: "52px", background: "#CCFBF1", borderRadius: "14px", display: "flex", alignItems: "center", justifyContent: "center", color: "#14B8A6", marginBottom: "14px" }}>
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                  </div>
                  <p style={{ fontSize: "15px", fontWeight: 700, color: "#0F766E", margin: "0 0 4px" }}>{uploadFile.name}</p>
                  <p style={{ fontSize: "12px", color: "var(--dash-text-muted)", margin: "0 0 12px" }}>{(uploadFile.size / 1024 / 1024).toFixed(1)} MB</p>
                  <button onClick={e => { e.stopPropagation(); setUploadFile(null); }} style={{ fontSize: "12px", color: "#EF4444", background: "none", border: "1px solid #FECACA", borderRadius: "6px", padding: "4px 12px", cursor: "pointer" }}>
                    Remove
                  </button>
                </>
              ) : (
                <>
                  <div style={{ width: "52px", height: "52px", background: dragActive ? "#CCFBF1" : "#F0FDFA", borderRadius: "14px", display: "flex", alignItems: "center", justifyContent: "center", color: "#14B8A6", marginBottom: "14px", transition: "all 0.2s" }}>
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
                      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
                    </svg>
                  </div>
                  <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--dash-text-main)", margin: "0 0 6px" }}>Drop your video here</h3>
                  <p style={{ fontSize: "13px", color: "var(--dash-text-muted)", margin: "0 0 4px" }}>or <span style={{ color: "#14B8A6", fontWeight: 600, textDecoration: "underline", textUnderlineOffset: "3px" }}>click to upload</span></p>
                  <p style={{ fontSize: "12px", color: "var(--dash-text-muted)", margin: 0 }}>mp4 · mov · avi · mkv · max 150 min</p>
                </>
              )}
            </div>

            {/* URL input */}
            <div style={{ background: "var(--dash-card-bg)", border: "1px solid #E5E7EB", borderRadius: "14px", padding: "20px" }}>
              <p style={{ fontSize: "12px", fontWeight: 700, color: "var(--dash-text-muted)", textTransform: "uppercase", letterSpacing: "0.6px", margin: "0 0 12px" }}>Or paste a YouTube / Loom / Vimeo link</p>
              <div style={{ display: "flex", gap: "10px" }}>
                <div style={{ flex: 1, position: "relative" }}>
                  <div style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--dash-text-muted)" }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                  </div>
                  <input
                    id="youtube-url-input"
                    type="text"
                    placeholder="https://youtube.com/watch?v=..."
                    value={youtubeUrl}
                    onChange={e => setYoutubeUrl(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleSubmit()}
                    style={{ width: "100%", height: "46px", background: "var(--dash-input-bg)", border: "1px solid #E5E7EB", borderRadius: "10px", paddingLeft: "38px", paddingRight: "14px", fontSize: "13px", color: "var(--dash-text-main)", outline: "none", fontFamily: "inherit", boxSizing: "border-box" }}
                  />
                </div>
              </div>
            </div>

            {/* Error / success banners */}
            {error && (
              <div style={{ background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: "10px", padding: "12px 16px", fontSize: "13px", color: "#DC2626", fontWeight: 500, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                ⚠ {error}
                <button onClick={() => setError(null)} style={{ background: "none", border: "none", cursor: "pointer", color: "#DC2626", fontSize: "16px" }}>×</button>
              </div>
            )}
            {successJobId && (
              <div style={{ background: "#ECFDF5", border: "1px solid #A7F3D0", borderRadius: "10px", padding: "12px 16px", fontSize: "13px", color: "#059669", fontWeight: 600 }}>
                ✓ Job queued! Switching to Jobs tab…
              </div>
            )}

            {/* Generate button */}
            <button
              id="generate-btn"
              onClick={handleSubmit}
              disabled={isSubmitting || (!youtubeUrl.trim() && !uploadFile)}
              style={{ width: "100%", padding: "16px", borderRadius: "13px", border: "none", fontSize: "15px", fontWeight: 700, cursor: isSubmitting || (!youtubeUrl.trim() && !uploadFile) ? "not-allowed" : "pointer", background: isSubmitting || (!youtubeUrl.trim() && !uploadFile) ? "var(--dash-border)" : "linear-gradient(135deg,#14B8A6,#0EA5E9)", color: isSubmitting || (!youtubeUrl.trim() && !uploadFile) ? "var(--dash-text-muted)" : "white", boxShadow: isSubmitting || (!youtubeUrl.trim() && !uploadFile) ? "none" : "0 6px 20px rgba(20,184,166,0.35)", transition: "all 0.2s", letterSpacing: "-0.2px" }}>
              {isSubmitting ? "Queuing job…" : `⚡ Generate Shorts with ${activeTempl.emoji} ${activeTempl.name}`}
            </button>

            {/* Template selector */}
            <div style={{ background: "var(--dash-card-bg)", border: "1px solid var(--dash-border)", borderRadius: "16px", padding: "20px", display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <p style={{ fontSize: "13px", fontWeight: 700, color: "var(--dash-text-main)", margin: 0 }}>Viral Style Template</p>
                  <span style={{ fontSize: "11px", color: "#7C3AED", background: "#F5F3FF", border: "1px solid #DDD6FE", borderRadius: "6px", padding: "2px 8px", fontWeight: 600 }}>{TEMPLATES.length} Templates</span>
                </div>
              </div>
              
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))", gap: "10px", overflowY: "auto", maxHeight: "480px", paddingRight: "4px", paddingBottom: "4px", scrollbarWidth: "thin", scrollbarColor: "var(--dash-border) transparent" }} className="dashboard-content-scroll">
                {TEMPLATES.map(t => {
                  const sel = t.id === selectedTemplate;
                  return (
                    <button key={t.id} onClick={() => setSelectedTemplate(t.id)}
                      title={t.desc}
                      style={{ 
                        position: "relative",
                        background: sel ? "linear-gradient(135deg,rgba(20,184,166,0.12),rgba(14,165,233,0.08))" : "var(--dash-input-bg)", 
                        border: `2px solid ${sel ? "#14B8A6" : "transparent"}`, 
                        borderRadius: "12px", 
                        padding: "8px", 
                        cursor: "pointer", 
                        transition: "all 0.15s", 
                        boxShadow: sel ? "0 0 0 3px rgba(20,184,166,0.15)" : "none", 
                        textAlign: "center",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center"
                      }}>
                      
                      {/* Image Thumbnail */}
                      <div style={{ width: "100%", aspectRatio: "9/16", borderRadius: "6px", overflow: "hidden", marginBottom: "8px", background: "#1E293B", position: "relative" }}>
                        {t.image ? (
                          <img 
                            src={t.image} 
                            alt={t.name}
                            style={{ width: "100%", height: "100%", objectFit: "cover" }}
                          />
                        ) : (
                          <div style={{ width: "100%", height: "100%", background: "linear-gradient(135deg, #374151, #111827)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <span style={{ fontSize: "32px", opacity: 0.8 }}>⚡</span>
                          </div>
                        )}
                        <div style={{ position: "absolute", bottom: "4px", right: "4px", background: "rgba(0,0,0,0.6)", borderRadius: "4px", padding: "2px 5px", fontSize: "12px" }}>
                          {t.emoji}
                        </div>
                      </div>

                      <p style={{ fontSize: "11px", fontWeight: sel ? 700 : 500, color: sel ? "#0F766E" : "var(--dash-text-main)", margin: 0, lineHeight: 1.3 }}>{t.name}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════
          TAB: JOBS
      ════════════════════════════════════════════════════════════════ */}
      {activeTab === "jobs" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <h2 style={{ fontSize: "17px", fontWeight: 700, color: "var(--dash-text-main)", margin: 0 }}>Processing Jobs</h2>
            <button onClick={loadJobs} style={{ fontSize: "12px", color: "#14B8A6", fontWeight: 600, background: "#F0FDFA", border: "1px solid #99F6E4", borderRadius: "8px", padding: "6px 14px", cursor: "pointer" }}>
              ↻ Refresh
            </button>
          </div>

          {loadingJobs && jobs.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px", color: "var(--dash-text-muted)" }}>
              <p style={{ fontSize: "14px" }}>Loading jobs…</p>
            </div>
          ) : jobs.length === 0 ? (
            <div style={{ textAlign: "center", padding: "80px 40px", background: "var(--dash-card-bg)", border: "1px solid #E5E7EB", borderRadius: "16px" }}>
              <div style={{ fontSize: "40px", marginBottom: "16px" }}>📭</div>
              <p style={{ fontSize: "16px", fontWeight: 600, color: "var(--dash-text-main)", margin: "0 0 8px" }}>No jobs yet</p>
              <p style={{ fontSize: "13px", color: "var(--dash-text-muted)", margin: "0 0 20px" }}>Create your first short from the Create tab</p>
              <button onClick={() => setActiveTab("create")} style={{ background: "#14B8A6", color: "white", border: "none", borderRadius: "10px", padding: "10px 24px", fontSize: "13px", fontWeight: 600, cursor: "pointer" }}>
                Create Now
              </button>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {jobs.map(job => {
                const col = STATUS_COLOR[job.status] ?? "var(--dash-text-muted)";
                const bg  = STATUS_BG[job.status]  ?? "var(--dash-input-bg)";
                const isExpanded = expandedJob === job.job_id;
                return (
                  <div key={job.job_id} style={{ background: "var(--dash-card-bg)", border: "1px solid #E5E7EB", borderRadius: "14px", overflow: "hidden", transition: "box-shadow 0.15s" }}>
                    <div
                      onClick={() => setExpandedJob(isExpanded ? null : job.job_id)}
                      style={{ padding: "16px 20px", cursor: "pointer", display: "flex", alignItems: "center", gap: "16px" }}
                    >
                      {/* Status dot */}
                      <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: col, flexShrink: 0, boxShadow: job.status === "processing" ? `0 0 0 4px ${col}22` : "none" }} />

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px", flexWrap: "wrap" }}>
                          <p style={{ fontSize: "13px", fontWeight: 600, color: "var(--dash-text-main)", margin: 0, fontFamily: "monospace" }}>
                            {job.job_id.slice(0, 8)}…
                          </p>
                          <span style={{ fontSize: "11px", fontWeight: 600, color: col, background: bg, border: `1px solid ${col}44`, borderRadius: "6px", padding: "2px 8px", textTransform: "capitalize" }}>
                            {job.status}
                          </span>
                          {job.clip_count > 0 && (
                            <span style={{ fontSize: "11px", color: "var(--dash-text-muted)" }}>{job.clip_count} clips</span>
                          )}
                        </div>
                        <p style={{ fontSize: "12px", color: "var(--dash-text-muted)", margin: 0 }}>{job.current_step}</p>
                      </div>

                      {/* Progress bar */}
                      {job.status === "processing" && (
                        <div style={{ width: "120px", flexShrink: 0 }}>
                          <div style={{ height: "5px", background: "var(--dash-hover)", borderRadius: "3px", overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${job.progress}%`, background: "#14B8A6", borderRadius: "3px", transition: "width 0.5s" }} />
                          </div>
                          <p style={{ fontSize: "10px", color: "var(--dash-text-muted)", margin: "3px 0 0", textAlign: "right" }}>{job.progress}%</p>
                        </div>
                      )}

                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--dash-text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ transform: isExpanded ? "rotate(180deg)" : "none", transition: "transform 0.2s", flexShrink: 0 }}>
                        <polyline points="6 9 12 15 18 9"/>
                      </svg>
                    </div>

                    {/* Expanded: clip results */}
                    {isExpanded && job.clips && job.clips.length > 0 && (
                      <div style={{ padding: "0 20px 20px", borderTop: "1px solid #F3F4F6" }}>
                        <p style={{ fontSize: "12px", fontWeight: 700, color: "var(--dash-text-muted)", textTransform: "uppercase", letterSpacing: "0.5px", margin: "14px 0 12px" }}>
                          Generated Clips
                        </p>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "12px" }}>
                          {job.clips.map(clip => (
                            <div key={clip.clip_id} style={{ background: "var(--dash-input-bg)", border: "1px solid #E5E7EB", borderRadius: "12px", overflow: "hidden" }}>
                              <div style={{ position: "relative", paddingTop: "177%", background: "#1E293B" }}>
                                {clip.thumbnail_url && (
                                  <img src={clip.thumbnail_url} alt={clip.top_title} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
                                )}
                                <div style={{ position: "absolute", top: "8px", right: "8px", background: "rgba(0,0,0,0.65)", borderRadius: "6px", padding: "2px 7px" }}>
                                  <span style={{ fontSize: "10px", color: "white", fontWeight: 600 }}>{Math.round(clip.duration)}s</span>
                                </div>
                                <div style={{ position: "absolute", bottom: "8px", left: "8px", right: "8px", background: "rgba(0,0,0,0.7)", borderRadius: "6px", padding: "4px 8px" }}>
                                  <p style={{ fontSize: "10px", color: "white", margin: 0, fontWeight: 600, lineHeight: 1.3, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                                    {clip.top_title}
                                  </p>
                                </div>
                              </div>
                              <div style={{ padding: "10px" }}>
                                <p style={{ fontSize: "10px", color: "var(--dash-text-muted)", margin: "0 0 6px" }}>{clip.bottom_tag}</p>
                                <div style={{ display: "flex", gap: "6px" }}>
                                  <a href={clip.clip_url} target="_blank" rel="noopener noreferrer"
                                    style={{ flex: 1, background: "#14B8A6", color: "white", border: "none", borderRadius: "7px", padding: "6px 0", fontSize: "11px", fontWeight: 600, cursor: "pointer", textAlign: "center", textDecoration: "none", display: "block" }}>
                                    ▶ View
                                  </a>
                                  <a href={clip.clip_url} download
                                    style={{ background: "var(--dash-hover)", color: "var(--dash-text-main)", border: "none", borderRadius: "7px", padding: "6px 10px", fontSize: "11px", fontWeight: 600, cursor: "pointer", textDecoration: "none", display: "flex", alignItems: "center" }}>
                                    ↓
                                  </a>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {isExpanded && (job.status === "processing" || job.status === "queued" || job.status === "pending") && (
                      <div style={{ padding: "12px 20px 18px", borderTop: "1px solid #F3F4F6", textAlign: "center", display: "flex", flexDirection: "column", gap: "10px", alignItems: "center" }}>
                        <p style={{ fontSize: "13px", color: job.status === "queued" ? "#6366F1" : "#14B8A6", fontWeight: 600, margin: 0 }}>
                          {job.status === "queued" ? "⏳ In Queue..." : "⚡ Processing..."} auto-refreshes every 6s
                        </p>
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            if (window.confirm("Are you sure you want to cancel this job?")) {
                              try {
                                await apiFetch(`/jobs/${job.job_id}`, { method: "DELETE" });
                                loadJobs();
                              } catch (err) {
                                alert("Failed to cancel job.");
                              }
                            }
                          }}
                          style={{
                            background: "transparent",
                            border: "1px solid #EF4444",
                            color: "#EF4444",
                            borderRadius: "6px",
                            padding: "6px 14px",
                            fontSize: "12px",
                            fontWeight: 600,
                            cursor: "pointer"
                          }}
                        >
                          Cancel Job
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════
          TAB: CLIPS (all clips across all completed jobs)
      ════════════════════════════════════════════════════════════════ */}
      {activeTab === "clips" && (
        <ClipsGallery />
      )}

    </div>
  );
}

// ─── Clips gallery ────────────────────────────────────────────────────────────
function ClipsGallery() {
  const [clips, setClips]   = useState<ClipResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const jobs: Job[] = await apiFetch("/jobs?limit=50");
        const all: ClipResult[] = jobs.flatMap(j => j.clips ?? []);
        setClips(all);
      } catch {/* */} finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div style={{ textAlign: "center", padding: "60px", color: "var(--dash-text-muted)" }}><p>Loading clips…</p></div>;

  if (clips.length === 0) return (
    <div style={{ textAlign: "center", padding: "80px 40px", background: "var(--dash-card-bg)", border: "1px solid #E5E7EB", borderRadius: "16px" }}>
      <div style={{ fontSize: "40px", marginBottom: "16px" }}>🎬</div>
      <p style={{ fontSize: "16px", fontWeight: 600, color: "var(--dash-text-main)", margin: "0 0 8px" }}>No clips yet</p>
      <p style={{ fontSize: "13px", color: "var(--dash-text-muted)" }}>Your generated shorts will appear here once complete</p>
    </div>
  );

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
        <h2 style={{ fontSize: "17px", fontWeight: 700, color: "var(--dash-text-main)", margin: 0 }}>My Clips <span style={{ color: "var(--dash-text-muted)", fontWeight: 400, fontSize: "14px" }}>({clips.length})</span></h2>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: "14px" }}>
        {clips.map(clip => (
          <div key={clip.clip_id} style={{ background: "var(--dash-card-bg)", border: "1px solid #E5E7EB", borderRadius: "14px", overflow: "hidden" }}>
            <div style={{ position: "relative", paddingTop: "177%", background: "#1E293B" }}>
              {clip.thumbnail_url && (
                <img src={clip.thumbnail_url} alt={clip.top_title} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
              )}
              <div style={{ position: "absolute", top: "8px", left: "8px", background: "rgba(0,0,0,0.65)", borderRadius: "6px", padding: "2px 7px" }}>
                <span style={{ fontSize: "10px", color: "white", fontWeight: 600 }}>{Math.round(clip.duration)}s</span>
              </div>
              {clip.viral_score && (
                <div style={{ position: "absolute", top: "8px", right: "8px", background: "linear-gradient(135deg,#14B8A6,#0EA5E9)", borderRadius: "6px", padding: "2px 7px" }}>
                  <span style={{ fontSize: "10px", color: "white", fontWeight: 700 }}>🔥{Math.round(clip.viral_score)}</span>
                </div>
              )}
            </div>
            <div style={{ padding: "10px 12px 12px" }}>
              <p style={{ fontSize: "11px", fontWeight: 700, color: "var(--dash-text-main)", margin: "0 0 3px", lineHeight: 1.3, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                {clip.top_title}
              </p>
              <p style={{ fontSize: "10px", color: "var(--dash-text-muted)", margin: "0 0 10px" }}>{clip.bottom_tag}</p>
              <div style={{ display: "flex", gap: "6px" }}>
                <a href={clip.clip_url} target="_blank" rel="noopener noreferrer"
                  style={{ flex: 1, background: "#14B8A6", color: "white", borderRadius: "8px", padding: "7px 0", fontSize: "11px", fontWeight: 600, textAlign: "center", textDecoration: "none", display: "block" }}>
                  ▶ Play
                </a>
                <a href={clip.clip_url} download
                  style={{ background: "var(--dash-hover)", color: "var(--dash-text-main)", borderRadius: "8px", padding: "7px 10px", fontSize: "11px", fontWeight: 600, textDecoration: "none", display: "flex", alignItems: "center" }}>
                  ↓
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Shared UI components ────────────────────────────────────────────────────
function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: "var(--dash-card-bg)", border: "1px solid #E5E7EB", borderRadius: "14px", padding: "20px" }}>
      <p style={{ fontSize: "11px", fontWeight: 700, color: "var(--dash-text-muted)", textTransform: "uppercase", letterSpacing: "0.7px", margin: "0 0 16px" }}>{title}</p>
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>{children}</div>
    </div>
  );
}

function OptionGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p style={{ fontSize: "12px", fontWeight: 600, color: "var(--dash-text-main)", margin: "0 0 8px" }}>{label}</p>
      {children}
    </div>
  );
}

function Toggle({ label, hint, value, onChange }: { label: string; hint?: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }} onClick={() => onChange(!value)}>
      <div>
        <p style={{ fontSize: "13px", fontWeight: 500, color: "var(--dash-text-main)", margin: 0 }}>{label}</p>
        {hint && <p style={{ fontSize: "11px", color: "var(--dash-text-muted)", margin: "2px 0 0" }}>{hint}</p>}
      </div>
      <div style={{ width: "42px", height: "24px", borderRadius: "12px", position: "relative", background: value ? "#14B8A6" : "#D1D5DB", transition: "background 0.2s", flexShrink: 0 }}>
        <div style={{ width: "18px", height: "18px", background: "white", borderRadius: "50%", position: "absolute", top: "3px", left: value ? "21px" : "3px", transition: "left 0.2s", boxShadow: "0 1px 4px rgba(0,0,0,0.15)" }} />
      </div>
    </div>
  );
}
