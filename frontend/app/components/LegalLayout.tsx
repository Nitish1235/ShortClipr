import Link from "next/link";

interface LegalLayoutProps {
  title: string;
  lastUpdated: string;
  children: React.ReactNode;
}

export default function LegalLayout({ title, lastUpdated, children }: LegalLayoutProps) {
  return (
    <div className="legal-page">
      {/* Navbar */}
      <nav className="navbar">
        <Link href="/" className="navbar-logo">ShortClipr</Link>
        <ul className="navbar-links">
          <li><Link href="/#how-it-works">How It Works</Link></li>
          <li><Link href="/#features">Features</Link></li>
          <li><Link href="/#testimonials">Testimonials</Link></li>
          <li><Link href="/#pricing">Pricing</Link></li>
        </ul>
        <div className="navbar-actions">
          <Link href="/login" className="btn-ghost">Log in</Link>
          <Link href="/signup" className="btn-primary">Get Started Free</Link>
        </div>
      </nav>

      {/* Hero bar */}
      <div className="legal-hero">
        <div className="legal-hero-inner">
          <div className="legal-breadcrumb">
            <Link href="/">Home</Link>
            <span>/</span>
            <span>{title}</span>
          </div>
          <h1 className="legal-title">{title}</h1>
          <p className="legal-meta">Last updated: {lastUpdated}</p>
        </div>
      </div>

      {/* Content */}
      <div className="legal-body">
        <div className="legal-container">
          {/* Sidebar TOC */}
          <aside className="legal-toc" aria-label="Table of contents">
            <p className="toc-label">On this page</p>
            <div id="toc-links" />
          </aside>

          {/* Main content */}
          <article className="legal-content">
            {children}
          </article>
        </div>
      </div>

      {/* Footer */}
      <footer className="legal-footer">
        <div className="legal-footer-inner">
          <span className="footer-brand">© {new Date().getFullYear()} ShortClipr. All rights reserved.</span>
          <div className="legal-footer-links">
            <Link href="/privacy">Privacy Policy</Link>
            <Link href="/terms">Terms of Service</Link>
            <Link href="/cookies">Cookie Policy</Link>
            <Link href="/refund">Refund Policy</Link>
            <Link href="/contact">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
