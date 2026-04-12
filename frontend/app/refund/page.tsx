import type { Metadata } from "next";
import LegalLayout from "../components/LegalLayout";

export const metadata: Metadata = {
  title: "Refund Policy – ShortClipr",
  description: "ShortClipr's refund and cancellation policy for subscriptions and one-time purchases.",
};

export default function RefundPage() {
  return (
    <LegalLayout title="Refund Policy" lastUpdated="April 8, 2025">
      <div className="legal-content">

        <div className="legal-highlight-box">
          <p>
            <strong>30-Day Money-Back Guarantee:</strong> If you&apos;re not satisfied with ShortClipr within the first 30 days of your first paid subscription,
            we will issue a full refund — no questions asked. Contact <a href="mailto:billing@shortclipr.com">billing@shortclipr.com</a>.
          </p>
        </div>

        <h2 id="subscription-refunds">1. Subscription Refunds</h2>

        <h3>1.1 30-Day Money-Back Guarantee</h3>
        <p>
          New subscribers on any paid plan (Starter, Growth, or Pro) are eligible for a full refund within <strong>30 days</strong> of their first payment.
          This guarantee applies only to the first invoice on a new account and cannot be used more than once.
        </p>

        <h3>1.2 Renewals</h3>
        <p>
          After the 30-day period, subscription payments are generally non-refundable. However, we review refund requests on a case-by-case basis.
          If you were charged due to a technical error or forgot to cancel before your renewal date, contact us within <strong>7 days</strong> of the charge and we will consider a partial or full refund.
        </p>

        <h3>1.3 Annual Plans</h3>
        <p>
          If you cancel an annual plan within 30 days of payment, you receive a full refund.
          After 30 days, we may offer a prorated refund for unused months at our discretion.
        </p>

        <h2 id="cancellation">2. Cancellation</h2>
        <p>You can cancel your subscription at any time from your account settings under <strong>Billing → Cancel Subscription</strong>.</p>
        <ul>
          <li>Cancellation takes effect at the end of your current billing period.</li>
          <li>You retain full access to all paid features until the period ends.</li>
          <li>No partial refunds are issued for the unused portion of the current billing period after the 30-day window.</li>
          <li>Your account reverts to the free plan at the end of the period.</li>
        </ul>

        <h2 id="free-plan">3. Free Plan</h2>
        <p>
          The free plan is provided at no charge. No refunds are applicable to free plan usage.
          Features and limits of the free plan may change at any time with reasonable notice.
        </p>

        <h2 id="add-ons">4. Add-Ons & One-Time Purchases</h2>
        <p>
          Credit packs, additional export quotas, and other one-time purchases are <strong>non-refundable</strong> once credits have been consumed.
          Unused credits at the time of account deletion are forfeited and not refundable.
        </p>

        <h2 id="processing-refunds">5. How Refunds Are Processed</h2>
        <p>
          Approved refunds are returned to the original payment method within <strong>5–10 business days</strong>, depending on your bank or card issuer.
          Refunds are issued in the original currency. ShortClipr is not responsible for exchange rate differences.
        </p>

        <h2 id="exceptions">6. Exceptions & Abuse</h2>
        <p>We reserve the right to deny a refund if:</p>
        <ul>
          <li>The account has violated our <a href="/terms">Terms of Service</a>.</li>
          <li>We detect refund abuse patterns (e.g., repeated sign-up and refund cycles).</li>
          <li>The request is made outside the eligible refund window without extraordinary circumstances.</li>
        </ul>

        <h2 id="how-to-request">7. How to Request a Refund</h2>
        <p>To request a refund:</p>
        <ol>
          <li>Email <a href="mailto:billing@shortclipr.com">billing@shortclipr.com</a> with the subject line <strong>&ldquo;Refund Request&rdquo;</strong>.</li>
          <li>Include your registered email address and the reason for your request.</li>
          <li>We will respond within <strong>2 business days</strong> with a decision.</li>
        </ol>

        <h2 id="contact-refund">8. Contact</h2>
        <p>For billing or refund questions, reach our team at <a href="mailto:billing@shortclipr.com">billing@shortclipr.com</a>.</p>
      </div>
    </LegalLayout>
  );
}
