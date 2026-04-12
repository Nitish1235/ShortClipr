import type { Metadata } from "next";
import LegalLayout from "../components/LegalLayout";

export const metadata: Metadata = {
  title: "Contact Us – ShortClipr",
  description: "Get in touch with the ShortClipr team for support, billing questions, partnerships, or feedback.",
};

export default function ContactPage() {
  return (
    <LegalLayout title="Contact Us" lastUpdated="April 8, 2025">
      <div className="legal-content">

        <p style={{ fontSize: '16px', color: 'var(--text-medium)', marginBottom: '40px' }}>
          Have a question, feedback, or need help? We&apos;re here for you. Choose the right channel below and we&apos;ll get back to you as fast as possible.
        </p>

        {/* Contact Cards */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(220px, 1fr))', gap:'16px', marginBottom:'48px' }}>
          <div className="contact-info-card">
            <div style={{ fontSize:'28px', marginBottom:'12px' }}>💬</div>
            <h3>General Support</h3>
            <p>Problems with the platform, export issues, account help.</p>
            <a href="mailto:support@shortclipr.com" className="contact-email">support@shortclipr.com</a>
            <p style={{ fontSize:'12px', color:'var(--text-muted)', marginTop:'8px' }}>Response: within 24 hours</p>
          </div>

          <div className="contact-info-card">
            <div style={{ fontSize:'28px', marginBottom:'12px' }}>💳</div>
            <h3>Billing & Payments</h3>
            <p>Subscription questions, refund requests, invoice issues.</p>
            <a href="mailto:billing@shortclipr.com" className="contact-email">billing@shortclipr.com</a>
            <p style={{ fontSize:'12px', color:'var(--text-muted)', marginTop:'8px' }}>Response: within 24 hours</p>
          </div>

          <div className="contact-info-card">
            <div style={{ fontSize:'28px', marginBottom:'12px' }}>🤝</div>
            <h3>Partnerships & Press</h3>
            <p>Collaboration, affiliate, media inquiries, and business development.</p>
            <a href="mailto:hello@shortclipr.com" className="contact-email">hello@shortclipr.com</a>
            <p style={{ fontSize:'12px', color:'var(--text-muted)', marginTop:'8px' }}>Response: within 3 business days</p>
          </div>

          <div className="contact-info-card">
            <div style={{ fontSize:'28px', marginBottom:'12px' }}>🔒</div>
            <h3>Privacy & Security</h3>
            <p>Data requests, GDPR, vulnerability reports.</p>
            <a href="mailto:privacy@shortclipr.com" className="contact-email">privacy@shortclipr.com</a>
            <p style={{ fontSize:'12px', color:'var(--text-muted)', marginTop:'8px' }}>Response: within 30 days (legal)</p>
          </div>
        </div>

        {/* Contact Form */}
        <h2 id="send-message" style={{ borderBottom:'1px solid rgba(0,0,0,0.06)', paddingBottom:'10px' }}>Send Us a Message</h2>
        <p>Fill out the form below and we&apos;ll get back to you as soon as possible.</p>

        <form
          action="#"
          method="POST"
          style={{ marginTop: '24px' }}
        >
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'16px' }}>
            <div className="contact-form-group">
              <label htmlFor="contact-name">Full Name *</label>
              <input id="contact-name" type="text" name="name" placeholder="Alex Johnson" required />
            </div>
            <div className="contact-form-group">
              <label htmlFor="contact-email">Email Address *</label>
              <input id="contact-email" type="email" name="email" placeholder="alex@example.com" required />
            </div>
          </div>

          <div className="contact-form-group">
            <label htmlFor="contact-subject">Subject *</label>
            <select id="contact-subject" name="subject" required>
              <option value="">Select a topic...</option>
              <option value="support">Technical Support</option>
              <option value="billing">Billing / Subscription</option>
              <option value="refund">Refund Request</option>
              <option value="feature">Feature Request</option>
              <option value="partnership">Partnership / Press</option>
              <option value="privacy">Privacy / Data Request</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="contact-form-group">
            <label htmlFor="contact-message">Message *</label>
            <textarea
              id="contact-message"
              name="message"
              placeholder="Describe your question or issue in detail..."
              required
            />
          </div>

          <button
            type="submit"
            className="btn-cta-large"
            style={{ width:'100%', justifyContent:'center' }}
          >
            Send Message
          </button>
        </form>

        <hr />

        <h2 id="faq">Frequently Asked Questions</h2>

        <h3>How long does the AI take to process a video?</h3>
        <p>
          Processing time depends on video length and complexity. A 60-minute video typically takes 3–8 minutes. You&apos;ll receive an email notification and in-app alert when your shorts are ready.
        </p>

        <h3>Which video formats do you support?</h3>
        <p>
          We support MP4, MOV, AVI, MKV, and WebM files up to 10GB. YouTube and Vimeo URLs are also supported.
        </p>

        <h3>Can I cancel my subscription at any time?</h3>
        <p>
          Yes, absolutely. Cancel any time from your account settings. You keep full access until the end of your billing period.
          See our <a href="/refund">Refund Policy</a> for money-back eligibility.
        </p>

        <h3>Do you offer a free trial?</h3>
        <p>
          Yes! The free plan includes 3 viral shorts per week — no credit card required.
          Paid plans come with a 30-day money-back guarantee.
        </p>

        <h3>Is my video content used to train your AI?</h3>
        <p>
          No. Your uploaded content is processed solely to generate your shorts and is never used for AI training.
          See our <a href="/privacy">Privacy Policy</a> for full details.
        </p>
      </div>
    </LegalLayout>
  );
}

