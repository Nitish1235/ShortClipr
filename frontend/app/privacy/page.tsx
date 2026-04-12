import type { Metadata } from "next";
import LegalLayout from "../components/LegalLayout";

export const metadata: Metadata = {
  title: "Privacy Policy – ShortClipr",
  description: "Learn how ShortClipr collects, uses, and protects your personal information.",
};

export default function PrivacyPage() {
  return (
    <LegalLayout title="Privacy Policy" lastUpdated="April 8, 2025">
      <div className="legal-content">

        <div className="legal-highlight-box">
          <p>
            <strong>Summary:</strong> ShortClipr collects data to deliver and improve our video-to-shorts AI service.
            We do not sell your personal data. You can request deletion of your data at any time by contacting{" "}
            <a href="mailto:privacy@shortclipr.com">privacy@shortclipr.com</a>.
          </p>
        </div>

        <h2 id="info-collect">1. Information We Collect</h2>
        <p>We collect information you provide directly to us, information we collect automatically, and information from third-party services.</p>

        <h3>1.1 Information You Provide</h3>
        <ul>
          <li><strong>Account data:</strong> Name, email address, and password when you register.</li>
          <li><strong>Payment data:</strong> Billing address and payment method details (processed securely by our payment provider — we do not store full card numbers).</li>
          <li><strong>Content data:</strong> Video files, URLs, and metadata you upload or submit for processing.</li>
          <li><strong>Communications:</strong> Messages you send to our support team.</li>
        </ul>

        <h3>1.2 Information Collected Automatically</h3>
        <ul>
          <li><strong>Usage data:</strong> Pages viewed, features used, videos processed, exports generated.</li>
          <li><strong>Device data:</strong> IP address, browser type, operating system, device identifiers.</li>
          <li><strong>Cookies & tracking:</strong> See our <a href="/cookies">Cookie Policy</a> for full details.</li>
          <li><strong>Log data:</strong> Server logs including timestamps, request paths, and error codes.</li>
        </ul>

        <h3>1.3 Information from Third Parties</h3>
        <ul>
          <li>When you sign in via Google or another OAuth provider, we receive your name, email, and profile photo from that provider.</li>
          <li>Analytics partners may share aggregated segment data about your usage patterns.</li>
        </ul>

        <h2 id="how-we-use">2. How We Use Your Information</h2>
        <p>We use the information we collect to:</p>
        <ul>
          <li>Provide, operate, and improve the ShortClipr platform and AI processing pipeline.</li>
          <li>Process your video content and deliver generated short clips to you.</li>
          <li>Authenticate your identity and maintain the security of your account.</li>
          <li>Process payments and manage your subscription.</li>
          <li>Send transactional emails (receipts, export-ready notifications, password resets).</li>
          <li>Send product updates and marketing communications (only with your consent, and you can opt out at any time).</li>
          <li>Analyze aggregate usage patterns to improve our AI models and UX (using anonymized or aggregated data only).</li>
          <li>Comply with legal obligations.</li>
        </ul>

        <h2 id="sharing">3. How We Share Your Information</h2>
        <p>
          We <strong>do not sell</strong> your personal data. We share data only in the following circumstances:
        </p>
        <ul>
          <li><strong>Service providers:</strong> Trusted third parties who help us operate (cloud hosting, payment processing, email delivery, analytics). They are bound by data processing agreements.</li>
          <li><strong>AI processing:</strong> Your video content is processed by our AI pipeline and may pass through third-party AI API services (e.g., transcription, scene detection). We use providers that do not train on your content.</li>
          <li><strong>Legal compliance:</strong> When required by law, court order, or to protect the rights, property, or safety of ShortClipr, our users, or the public.</li>
          <li><strong>Business transfers:</strong> In connection with a merger, acquisition, or sale of assets, with appropriate confidentiality protections.</li>
        </ul>

        <h2 id="data-retention">4. Data Retention</h2>
        <p>
          We retain your personal data for as long as your account is active or as needed to provide services.
          Uploaded video files and generated shorts are stored for <strong>30 days</strong> after processing, after which they are permanently deleted from our servers.
          You can manually delete content from your dashboard at any time.
          Account data is retained for 90 days after account deletion, then permanently purged.
        </p>

        <h2 id="your-rights">5. Your Rights</h2>
        <p>Depending on your location, you may have the following rights regarding your personal data:</p>
        <table>
          <thead>
            <tr>
              <th>Right</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr><td><strong>Access</strong></td><td>Request a copy of the personal data we hold about you.</td></tr>
            <tr><td><strong>Correction</strong></td><td>Request correction of inaccurate or incomplete data.</td></tr>
            <tr><td><strong>Deletion</strong></td><td>Request erasure of your personal data ("right to be forgotten").</td></tr>
            <tr><td><strong>Portability</strong></td><td>Receive your data in a structured, machine-readable format.</td></tr>
            <tr><td><strong>Opt-out</strong></td><td>Opt out of marketing communications at any time via unsubscribe links or account settings.</td></tr>
            <tr><td><strong>Restriction</strong></td><td>Request restriction of processing in certain circumstances.</td></tr>
          </tbody>
        </table>
        <p>To exercise any of these rights, email us at <a href="mailto:privacy@shortclipr.com">privacy@shortclipr.com</a>. We will respond within 30 days.</p>

        <h2 id="cookies">6. Cookies</h2>
        <p>We use cookies and similar technologies to operate the service and understand usage. See our <a href="/cookies">Cookie Policy</a> for full details on what cookies we use and how to manage them.</p>

        <h2 id="security">7. Security</h2>
        <p>
          We implement industry-standard security measures including TLS encryption in transit, AES-256 encryption at rest, access controls, and regular security audits.
          No system is 100% secure; if you believe your account has been compromised, contact us immediately at <a href="mailto:security@shortclipr.com">security@shortclipr.com</a>.
        </p>

        <h2 id="childrens-privacy">8. Children&apos;s Privacy</h2>
        <p>
          ShortClipr is not intended for users under 13 years of age. We do not knowingly collect personal data from children under 13.
          If you believe a child has provided us with personal data, contact us and we will delete it promptly.
        </p>

        <h2 id="international">9. International Data Transfers</h2>
        <p>
          ShortClipr operates globally. Your data may be transferred to and processed in countries outside your own, including the United States.
          We ensure appropriate safeguards are in place (such as Standard Contractual Clauses for EU/EEA transfers) to protect your data.
        </p>

        <h2 id="changes">10. Changes to This Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. We will notify you of significant changes via email or an in-app banner at least 14 days before changes take effect.
          Your continued use of ShortClipr after changes constitutes acceptance of the updated policy.
        </p>

        <h2 id="contact">11. Contact Us</h2>
        <p>For privacy-related questions or requests:</p>
        <ul>
          <li><strong>Email:</strong> <a href="mailto:privacy@shortclipr.com">privacy@shortclipr.com</a></li>
          <li><strong>Response time:</strong> Within 30 days of receipt</li>
          <li><strong>Mailing address:</strong> ShortClipr Inc., [Your Address]</li>
        </ul>
      </div>
    </LegalLayout>
  );
}
