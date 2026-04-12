import type { Metadata } from "next";
import LegalLayout from "../components/LegalLayout";

export const metadata: Metadata = {
  title: "Terms of Service – ShortClipr",
  description: "Read ShortClipr's Terms of Service — the rules, rights, and responsibilities governing use of our platform.",
};

export default function TermsPage() {
  return (
    <LegalLayout title="Terms of Service" lastUpdated="April 8, 2025">
      <div className="legal-content">

        <div className="legal-highlight-box">
          <p>
            By creating an account or using ShortClipr, you agree to these Terms.
            Please read them carefully. If you disagree with any part, do not use our service.
          </p>
        </div>

        <h2 id="acceptance">1. Acceptance of Terms</h2>
        <p>
          These Terms of Service (&ldquo;Terms&rdquo;) constitute a legally binding agreement between you (&ldquo;User&rdquo;, &ldquo;you&rdquo;) and ShortClipr Inc. (&ldquo;ShortClipr&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;).
          By accessing or using ShortClipr (the &ldquo;Service&rdquo;), you confirm that you are at least 13 years old and have the legal capacity to enter into this agreement.
        </p>

        <h2 id="description">2. Description of Service</h2>
        <p>
          ShortClipr is an AI-powered platform that processes long-form video content and automatically generates short-form video clips optimized for social media platforms including TikTok, YouTube Shorts, and Instagram Reels.
          The Service includes auto-captioning, vertical reframing, viral score ranking, bulk export, and related features.
        </p>

        <h2 id="accounts">3. User Accounts</h2>
        <ul>
          <li>You must provide accurate, current, and complete information when creating your account.</li>
          <li>You are responsible for maintaining the confidentiality of your credentials and for all activity under your account.</li>
          <li>Notify us immediately at <a href="mailto:support@shortclipr.com">support@shortclipr.com</a> if you suspect unauthorized access.</li>
          <li>One person or legal entity may not maintain more than one free account. Multiple accounts created to circumvent limitations may result in all accounts being terminated.</li>
        </ul>

        <h2 id="content">4. Your Content</h2>
        <h3>4.1 Ownership</h3>
        <p>You retain full ownership of all video content, footage, and media you upload to ShortClipr (&ldquo;Your Content&rdquo;).</p>

        <h3>4.2 License to Us</h3>
        <p>
          By uploading content, you grant ShortClipr a limited, non-exclusive, royalty-free license to process, store, transcode, and display Your Content solely for the purpose of providing the Service to you.
          This license terminates when you delete your content or close your account.
        </p>

        <h3>4.3 Your Representations</h3>
        <p>You represent and warrant that:</p>
        <ul>
          <li>You own or have the necessary rights and permissions to upload and process Your Content.</li>
          <li>Your Content does not infringe any third-party intellectual property, privacy, or other rights.</li>
          <li>Your Content complies with all applicable laws and these Terms.</li>
          <li>You have obtained any necessary consents from individuals appearing in Your Content.</li>
        </ul>

        <h2 id="prohibited">5. Prohibited Uses</h2>
        <p>You may not use ShortClipr to:</p>
        <ul>
          <li>Process or distribute content that is illegal, defamatory, harassing, hateful, or pornographic.</li>
          <li>Infringe any copyright, trademark, or other intellectual property rights.</li>
          <li>Upload malware, viruses, or any other harmful code.</li>
          <li>Attempt to reverse-engineer, decompile, or extract our AI models or source code.</li>
          <li>Use automated scrapers, bots, or other tools to access the Service in an unauthorized manner.</li>
          <li>Resell or sublicense access to the Service without written permission.</li>
          <li>Create deepfakes, non-consensual intimate imagery, or misleading synthetic media.</li>
          <li>Interfere with or disrupt the integrity or performance of the Service.</li>
        </ul>

        <h2 id="payment">6. Payment & Subscriptions</h2>
        <h3>6.1 Plans</h3>
        <p>
          ShortClipr offers free and paid subscription plans. Paid plans are billed on a monthly or annual basis.
          All prices are in USD and inclusive of applicable taxes unless stated otherwise.
        </p>

        <h3>6.2 Billing</h3>
        <p>
          By subscribing to a paid plan, you authorize ShortClipr (via our payment processor) to charge your payment method on a recurring basis.
          Subscriptions auto-renew unless cancelled at least 24 hours before the renewal date.
        </p>

        <h3>6.3 Changes to Pricing</h3>
        <p>
          We may change subscription prices. We will provide at least 30 days&apos; notice of any price increase.
          Your continued use of the paid plan after the notice period constitutes acceptance of the new price.
        </p>

        <h2 id="intellectual-property">7. Intellectual Property</h2>
        <p>
          All ShortClipr technology, AI models, software, designs, trademarks, and content (excluding Your Content) are the exclusive property of ShortClipr Inc.
          and protected by intellectual property laws. You may not use our branding or trademarks without prior written consent.
        </p>

        <h2 id="disclaimers">8. Disclaimers & Limitations of Liability</h2>
        <p>
          THE SERVICE IS PROVIDED &ldquo;AS IS&rdquo; AND &ldquo;AS AVAILABLE&rdquo; WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.
        </p>
        <p>
          TO THE MAXIMUM EXTENT PERMITTED BY LAW, SHORTCLIPR SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS, DATA, OR GOODWILL, ARISING FROM YOUR USE OF THE SERVICE.
          OUR TOTAL LIABILITY WILL NOT EXCEED THE AMOUNT YOU PAID US IN THE 12 MONTHS PRIOR TO THE CLAIM.
        </p>

        <h2 id="termination">9. Termination</h2>
        <p>
          You may cancel your account at any time via account settings. We may terminate or suspend your account immediately, without notice, if you violate these Terms or engage in activity that harms other users, third parties, or ShortClipr.
          Upon termination, your right to use the Service ceases and we may delete Your Content after a 30-day grace period.
        </p>

        <h2 id="governing-law">10. Governing Law & Disputes</h2>
        <p>
          These Terms are governed by the laws of the State of Delaware, USA, without regard to conflict of law provisions.
          Any disputes shall be resolved through binding arbitration under the rules of the American Arbitration Association,
          except that either party may seek injunctive relief in a court of competent jurisdiction.
        </p>

        <h2 id="changes-terms">11. Changes to Terms</h2>
        <p>
          We may update these Terms. Material changes will be communicated via email or in-app notification at least 14 days before taking effect.
          Your continued use of the Service constitutes acceptance of the updated Terms.
        </p>

        <h2 id="contact-terms">12. Contact</h2>
        <p>
          Questions about these Terms? Contact us at <a href="mailto:legal@shortclipr.com">legal@shortclipr.com</a>.
        </p>
      </div>
    </LegalLayout>
  );
}
