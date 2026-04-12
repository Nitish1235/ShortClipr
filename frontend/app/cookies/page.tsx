import type { Metadata } from "next";
import LegalLayout from "../components/LegalLayout";

export const metadata: Metadata = {
  title: "Cookie Policy – ShortClipr",
  description: "Learn how ShortClipr uses cookies and similar tracking technologies, and how to manage your preferences.",
};

export default function CookiesPage() {
  return (
    <LegalLayout title="Cookie Policy" lastUpdated="April 8, 2025">
      <div className="legal-content">

        <div className="legal-highlight-box">
          <p>
            ShortClipr uses cookies to keep you signed in, understand how you use our platform, and improve your experience.
            You can control cookie preferences in your browser settings or via our consent banner.
          </p>
        </div>

        <h2 id="what-are-cookies">1. What Are Cookies?</h2>
        <p>
          Cookies are small text files stored on your device when you visit a website. They help the website remember information about your visit,
          such as your preferences and login state. Similar technologies include local storage, session storage, and pixel tags.
        </p>
        <p>
          Cookies can be &ldquo;session cookies&rdquo; (deleted when you close your browser) or &ldquo;persistent cookies&rdquo; (retained between sessions for a set period).
        </p>

        <h2 id="cookies-we-use">2. Cookies We Use</h2>

        <h3>2.1 Strictly Necessary Cookies</h3>
        <p>These cookies are essential for the Service to function. They cannot be disabled.</p>
        <table>
          <thead>
            <tr>
              <th>Cookie Name</th>
              <th>Purpose</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            <tr><td><code>sc_session</code></td><td>Maintains your login session</td><td>Session</td></tr>
            <tr><td><code>sc_csrf</code></td><td>Protects against cross-site request forgery</td><td>Session</td></tr>
            <tr><td><code>sc_auth_token</code></td><td>Stores your authentication token securely</td><td>30 days</td></tr>
            <tr><td><code>sc_consent</code></td><td>Remembers your cookie consent preferences</td><td>1 year</td></tr>
          </tbody>
        </table>

        <h3>2.2 Performance & Analytics Cookies</h3>
        <p>These cookies help us understand how visitors interact with our Service.</p>
        <table>
          <thead>
            <tr>
              <th>Cookie Name / Provider</th>
              <th>Purpose</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Google Analytics (<code>_ga</code>, <code>_gid</code>)</td><td>Measures page visits, user flows, and feature usage (anonymized)</td><td>2 years / 24 hours</td></tr>
            <tr><td>Vercel Analytics</td><td>Tracks page performance and Core Web Vitals</td><td>Session</td></tr>
            <tr><td><code>sc_ab_test</code></td><td>Assigns you to A/B test variants to improve our UI</td><td>90 days</td></tr>
          </tbody>
        </table>

        <h3>2.3 Functional Cookies</h3>
        <p>These cookies remember your preferences and settings.</p>
        <table>
          <thead>
            <tr>
              <th>Cookie Name</th>
              <th>Purpose</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            <tr><td><code>sc_theme</code></td><td>Stores your light/dark mode preference</td><td>1 year</td></tr>
            <tr><td><code>sc_locale</code></td><td>Stores your language/region preference</td><td>1 year</td></tr>
            <tr><td><code>sc_onboarded</code></td><td>Tracks whether you have completed onboarding</td><td>Persistent</td></tr>
          </tbody>
        </table>

        <h3>2.4 Marketing Cookies</h3>
        <p>These cookies track your activity to serve you relevant ads and measure campaign effectiveness. They are only set with your consent.</p>
        <table>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Purpose</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Meta Pixel</td><td>Tracks conversions from Meta ads (Instagram, Facebook)</td><td>180 days</td></tr>
            <tr><td>Google Ads (<code>_gcl_au</code>)</td><td>Measures ad conversions from Google Search/Display</td><td>90 days</td></tr>
            <tr><td>TikTok Pixel</td><td>Tracks conversions from TikTok campaigns</td><td>30 days</td></tr>
          </tbody>
        </table>

        <h2 id="third-party">3. Third-Party Cookies</h2>
        <p>
          Some third-party services embedded in our platform may set their own cookies. These include:
        </p>
        <ul>
          <li><strong>YouTube embed:</strong> If you play a demo video hosted on YouTube, Google may set cookies (see <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer">Google&apos;s Privacy Policy</a>).</li>
          <li><strong>Intercom:</strong> Our support chat widget uses cookies to recognize returning users.</li>
          <li><strong>Stripe:</strong> Our payment processor uses cookies for fraud detection and payment security.</li>
        </ul>
        <p>We do not control these third-party cookies. Please refer to their respective privacy policies.</p>

        <h2 id="manage-cookies">4. How to Manage Cookies</h2>
        <p>You can control and manage cookies in several ways:</p>

        <h3>Browser Settings</h3>
        <p>Most browsers let you view, block, or delete cookies. Here are links to manage cookies in common browsers:</p>
        <ul>
          <li><a href="https://support.google.com/chrome/answer/95647" target="_blank" rel="noopener noreferrer">Google Chrome</a></li>
          <li><a href="https://support.mozilla.org/en-US/kb/enable-and-disable-cookies-website-preferences" target="_blank" rel="noopener noreferrer">Mozilla Firefox</a></li>
          <li><a href="https://support.apple.com/guide/safari/manage-cookies-sfri11471" target="_blank" rel="noopener noreferrer">Apple Safari</a></li>
          <li><a href="https://support.microsoft.com/en-us/microsoft-edge/delete-cookies-in-microsoft-edge-63947406" target="_blank" rel="noopener noreferrer">Microsoft Edge</a></li>
        </ul>
        <p>
          <strong>Note:</strong> Blocking strictly necessary cookies will affect the core functionality of ShortClipr (e.g., you may be unable to log in).
        </p>

        <h3>Opt-Out Tools</h3>
        <ul>
          <li><a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer">Google Analytics Opt-Out</a></li>
          <li><a href="https://www.youronlinechoices.eu/" target="_blank" rel="noopener noreferrer">Your Online Choices (EU)</a></li>
          <li><a href="https://optout.networkadvertising.org/" target="_blank" rel="noopener noreferrer">NAI Opt-Out (US)</a></li>
        </ul>

        <h2 id="do-not-track">5. Do Not Track</h2>
        <p>
          Some browsers have a &ldquo;Do Not Track&rdquo; (DNT) signal. Because there is no consistent industry standard for DNT, ShortClipr currently does not respond differently to DNT signals.
          You can manage your preferences through the methods described above.
        </p>

        <h2 id="updates-cookies">6. Updates to This Policy</h2>
        <p>
          We may update this Cookie Policy periodically. Changes will be reflected by updating the &ldquo;Last updated&rdquo; date above.
          For significant changes, we will notify you through the cookie consent banner on your next visit.
        </p>

        <h2 id="contact-cookies">7. Contact</h2>
        <p>Questions about our Cookie Policy? Email us at <a href="mailto:privacy@shortclipr.com">privacy@shortclipr.com</a>.</p>
      </div>
    </LegalLayout>
  );
}
