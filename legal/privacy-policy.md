# Privacy Policy

**OPENAUTONOMYX (OPC) PRIVATE LIMITED**
No. 78/9, Outer Ring Road, Varthur Hobli, Bellandur, Bangalore South, Bangalore – 560103, Karnataka, India
CIN: U62010KA2026OPC215666

**Effective Date:** April 15, 2026
**Last Updated:** April 15, 2026

---

## 1. Introduction

OPENAUTONOMYX (OPC) PRIVATE LIMITED ("Autonomyx", "we", "us", "our") operates the Autonomyx Model Gateway platform. This Privacy Policy explains how we collect, use, store, share, and protect personal data when you access or use our platform, website, and associated services.

This Policy applies to:
- Visitors to `openautonomyx.com`
- Registered users and API customers
- Private Node customers and their authorised users

We are committed to protecting your privacy in accordance with the **Digital Personal Data Protection Act 2023 (DPDP Act)**, and where applicable, the **General Data Protection Regulation (GDPR)** and the **California Consumer Privacy Act (CCPA)**.

---

## 2. Data We Collect

### 2.1 Account and Identity Data

When you register an account, we collect:
- Full name
- Email address
- Company name and designation (if applicable)
- Account credentials (password stored as hashed value — never in plain text)

### 2.2 Payment Data

When you make a payment, we collect:
- Billing name and address
- Payment method type (card, UPI, PayPal)
- Transaction ID and amount

We do **not** store card numbers, CVV, or full payment credentials. All payment data is processed by our payment processors (Razorpay, Stripe, PayPal) under their respective privacy policies.

### 2.3 Usage Data

When you use the API or workflows, we collect:
- API request metadata: timestamp, model used, token count, latency, Virtual Key alias
- Workflow execution logs: flow ID, execution status, duration
- Spend records: usage amounts, billing cycle, invoice history
- LLM trace data (inputs and outputs) stored in Langfuse, scoped to your tenant organisation

We do **not** use your API prompts or outputs to train, fine-tune, or improve AI models without your explicit opt-in consent.

### 2.4 Technical Data

When you access our platform or website, we automatically collect:
- IP address
- Browser type and version
- Operating system
- Device identifiers
- Pages visited, time spent, referring URL
- Error logs and crash reports

### 2.5 Communications Data

When you contact us, we collect:
- Email correspondence
- Support ticket content
- Feedback and survey responses

### 2.6 Data We Do Not Collect

We do not knowingly collect:
- Personal data of children under 18
- Sensitive personal data (health, biometric, financial beyond payment processing, religious, political) unless you voluntarily submit it in API prompts — in which case you are responsible for ensuring lawful processing under applicable law

---

## 3. How We Use Your Data

| Purpose | Legal Basis (DPDP) | Legal Basis (GDPR) |
|---|---|---|
| Providing and operating the Service | Consent / Contract | Contract performance |
| Processing payments and issuing invoices | Contract | Contract performance |
| Usage tracking and billing via Lago | Contract | Contract performance |
| LLM trace storage in Langfuse | Consent | Legitimate interests |
| Sending transactional emails (invoices, alerts, account notices) | Contract | Contract performance |
| Sending product updates and announcements | Consent | Consent |
| Security monitoring, fraud detection, abuse prevention | Legitimate use | Legitimate interests |
| Improving the Platform (aggregated, anonymised analytics only) | Legitimate use | Legitimate interests |
| Complying with legal obligations (GST, court orders) | Legal obligation | Legal obligation |

We do not use your personal data for automated decision-making or profiling that produces legal or similarly significant effects.

---

## 4. Data Sharing and Sub-processors

We share your data only as necessary to deliver the Service. Current sub-processors:

| Sub-processor | Purpose | Data shared | Location |
|---|---|---|---|
| **Razorpay** | Payment processing (INR) | Name, email, billing address, transaction data | India |
| **Stripe** | Payment processing (international) | Name, email, billing address, transaction data | USA |
| **PayPal** | Payment processing | Name, email, transaction data | USA |
| **Groq** | Cloud LLM inference (fallback) | API prompts and inputs | USA |
| **OpenAI** | Cloud LLM inference (fallback) | API prompts and inputs | USA |
| **Anthropic** | Cloud LLM inference (fallback) | API prompts and inputs | USA |
| **Google Vertex AI** | Cloud LLM inference (fallback) | API prompts and inputs | USA (us-central1) |
| **Lago** | Usage metering and billing | Usage records, customer ID | Self-hosted on our VPS |
| **Langfuse** | LLM trace storage and observability | Prompts and outputs (per-tenant isolated) | Self-hosted on our VPS |
| **SurrealDB Cloud** | Vector storage for RAG and web scraping | Scraped content and embeddings | AWS ap-south-1 |

**Cloud LLM sub-processors:** When your requests are routed to cloud model providers (Groq, OpenAI, Anthropic, Google Vertex AI), your prompt data is transmitted to those providers. This only occurs as a fallback when local models are unavailable or your plan permits cloud routing. We recommend using Private Node deployment if you require data to remain exclusively within your own infrastructure.

We do not sell your personal data to third parties. We do not share your data with advertisers.

---

## 5. Data Retention

| Data type | Retention period |
|---|---|
| Account data | Duration of account + 90 days post-deletion |
| API usage logs and billing records | 7 years (GST compliance requirement under Indian law) |
| LLM trace data in Langfuse | 90 days from creation |
| Payment transaction records | 7 years (GST compliance) |
| Support correspondence | 2 years from last interaction |
| Technical logs (IP, access logs) | 90 days |
| Anonymised aggregated analytics | Indefinite |

When the retention period expires, we delete or anonymise your data. Legal holds may extend retention where required by law or ongoing proceedings.

---

## 6. Data Security

We implement commercially reasonable technical and organisational measures including:

- **Encryption in transit:** TLS 1.2+ for all API and web traffic
- **Encryption at rest:** for databases storing personal data
- **Access controls:** Virtual Key scoping, per-tenant data isolation, role-based access
- **Infrastructure security:** Coolify-managed deployments, non-root container users, restricted network exposure
- **Payment security:** We never store raw card data — all payment processing is handled by PCI-DSS compliant processors

No security measure is absolute. In the event of a confirmed data breach affecting your personal data, we will notify you within 72 hours of becoming aware, as required by the DPDP Act 2023.

---

## 7. Your Rights

### 7.1 Rights Under DPDP Act 2023 (India)

As a Data Principal under the DPDP Act 2023, you have the right to:

(a) **Access** — request confirmation of whether we process your personal data and obtain a summary of it;
(b) **Correction** — request correction of inaccurate or incomplete personal data;
(c) **Erasure** — request deletion of your personal data where processing is no longer necessary, subject to legal retention obligations;
(d) **Grievance redressal** — raise a complaint with our Data Protection Officer and, if unresolved, with the Data Protection Board of India;
(e) **Nominate** — nominate another individual to exercise these rights on your behalf in the event of your death or incapacity.

### 7.2 Rights Under GDPR (EU/UK customers)

If you are located in the EU or UK, you additionally have the right to:

(a) **Data portability** — receive your personal data in a structured, machine-readable format;
(b) **Restriction** — request restriction of processing in certain circumstances;
(c) **Object** — object to processing based on legitimate interests;
(d) **Withdraw consent** — where processing is based on consent, withdraw it at any time without affecting prior processing;
(e) **Lodge a complaint** — with your local supervisory authority.

### 7.3 Rights Under CCPA (California customers)

If you are a California resident, you have the right to:

(a) know what personal information we collect and how it is used;
(b) delete your personal information, subject to exceptions;
(c) opt out of the sale of personal information — we do not sell personal information;
(d) non-discrimination for exercising your rights.

### 7.4 Exercising Your Rights

To exercise any of the above rights, contact us at:
**Email:** chinmay@openautonomyx.com
**Subject line:** "Privacy Rights Request — [your right]"

We will respond within 30 days. We may ask you to verify your identity before processing your request.

---

## 8. Cookies and Tracking

### 8.1 Website

Our website (`openautonomyx.com`) uses:
- **Strictly necessary cookies** — for session management and security. These cannot be disabled.
- **Functional cookies** — to remember your preferences.

We do not currently use advertising or behavioural tracking cookies.

### 8.2 Platform

The Autonomyx Model Gateway platform does not use cookies. Authentication is handled via Virtual Keys transmitted in API request headers.

---

## 9. International Data Transfers

We are headquartered in India. When we transfer personal data to sub-processors located outside India (including USA-based cloud LLM providers), we do so:

(a) only to countries notified by the Indian Government as providing adequate data protection, or
(b) under contractual terms requiring the recipient to provide a level of protection equivalent to that under the DPDP Act 2023.

For EU/UK data subjects, international transfers are made under Standard Contractual Clauses (SCCs) or equivalent safeguards.

---

## 10. Private Node Customers

For customers running a Private Node deployment:

(a) Personal data processed exclusively on the Customer's own VPS remains within the Customer's infrastructure and is outside Autonomyx's control;
(b) The Customer is the Data Fiduciary (under DPDP) / Data Controller (under GDPR) for all data processed on their node;
(c) Autonomyx acts as a Data Processor only for trace data sent to our Langfuse instance and usage data sent to our Lago instance;
(d) A Data Processing Agreement (DPA) is available on request for Private Node customers — contact chinmay@openautonomyx.com.

---

## 11. Children's Privacy

The Platform is not directed at individuals under 18 years of age. We do not knowingly collect personal data from children. If you become aware that a child has provided us with personal data, contact us at chinmay@openautonomyx.com and we will delete it promptly.

---

## 12. Changes to This Policy

We may update this Privacy Policy from time to time. Material changes will be notified by email to your registered address at least 14 days before taking effect. The updated Policy will be posted at `openautonomyx.com/legal/privacy-policy` with the revised effective date. Continued use of the Platform after the effective date constitutes acceptance of the updated Policy.

---

## 13. Contact and Grievance Redressal

**Data Protection Officer / Grievance Officer:**
Chinmay Panda
OPENAUTONOMYX (OPC) PRIVATE LIMITED
No. 78/9, Outer Ring Road, Varthur Hobli, Bellandur,
Bangalore South, Bangalore – 560103, Karnataka, India
**Email:** chinmay@openautonomyx.com
**Response time:** Within 30 days of receipt

If your grievance is not resolved within 30 days, you may escalate to the **Data Protection Board of India** once it is constituted and operational under the DPDP Act 2023.

---

*This Privacy Policy was last updated on April 15, 2026.*

> **Legal Notice:** This Privacy Policy was drafted with AI assistance and reviewed interactively. It should be reviewed by a qualified Indian legal counsel before publication, particularly with respect to DPDP Act 2023 compliance, international transfer provisions, and the sub-processor list.
