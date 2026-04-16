# Terms of Service

**OPENAUTONOMYX (OPC) PRIVATE LIMITED**
No. 78/9, Outer Ring Road, Varthur Hobli, Bellandur, Bangalore South, Bangalore – 560103, Karnataka, India
CIN: U62010KA2026OPC215666

**Effective Date:** April 15, 2026
**Last Updated:** April 15, 2026

---

## 1. Parties and Acceptance

These Terms of Service ("Terms") constitute a legally binding agreement between **OPENAUTONOMYX (OPC) PRIVATE LIMITED** ("Autonomyx", "we", "us", "our") and the individual or entity accessing or using the Autonomyx Model Gateway platform ("Customer", "you", "your").

By accessing the platform, creating an account, generating an API key, or making any payment, you confirm that:

(a) you have read, understood, and agree to be bound by these Terms;
(b) if acting on behalf of an organisation, you have authority to bind that organisation;
(c) you are at least 18 years of age or the age of majority in your jurisdiction.

If you do not agree to these Terms, do not access or use the platform.

---

## 2. Definitions

| Term | Meaning |
|---|---|
| **Platform** | The Autonomyx Model Gateway software, APIs, pre-built workflows, documentation, and associated services operated by Autonomyx |
| **Service** | Access to the Platform provided under these Terms, including Shared SaaS tiers and Private Node deployments |
| **API** | The OpenAI-compatible REST API exposed by the Platform at `llm.openautonomyx.com` |
| **Virtual Key** | A scoped API credential issued to a Customer for authenticating requests and tracking usage |
| **Shared SaaS** | The Free, Developer, Growth, and SaaS Basic tiers where compute infrastructure is shared across customers |
| **Private Node** | A dedicated single-VPS deployment of the Platform provisioned for a specific Customer |
| **Usage** | API calls, workflow executions, token consumption, and web scraping jobs initiated using a Virtual Key |
| **Fees** | Amounts payable by the Customer based on Usage as recorded by our billing system |
| **Sub-processors** | Third-party AI model providers and infrastructure services used to deliver the Service |

---

## 3. Service Description and Tiers

### 3.1 What the Platform Provides

Autonomyx Model Gateway is a self-hosted AI platform that provides:

(a) unified API access to local and cloud AI models via an OpenAI-compatible endpoint;
(b) pre-built AI workflows for code review, policy generation, policy analysis, feature gap analysis, fraud detection, web scraping, structured data parsing, and other tasks;
(c) intelligent model routing, task classification, and multilingual support including 22 Indian languages;
(d) per-tenant usage tracking, billing, and observability.

### 3.2 Service Tiers

| Tier | Monthly Usage Allowance | Compute | SLA |
|---|---|---|---|
| **Free** | 10M tokens | Shared | None — best effort |
| **Developer** (₹999/month equivalent) | 100M tokens | Shared | None — best effort |
| **Growth** (₹4,999/month equivalent) | 1B tokens | Shared | None — best effort |
| **SaaS Basic** (₹14,999/month equivalent) | 5B tokens | Shared + white-label | None — best effort |
| **Private Node** (₹50,000+/month equivalent) | Usage-based, unlimited | Dedicated VPS | Commercially reasonable efforts — see Section 3.4 |

### 3.3 Shared SaaS — No SLA

For Free, Developer, Growth, and SaaS Basic tiers:

(a) the Platform is provided on a **best-effort basis** with no uptime guarantee;
(b) Autonomyx does not warrant uninterrupted, error-free, or secure access;
(c) planned and unplanned maintenance may occur at any time without prior notice;
(d) shared compute resources may be subject to throttling during peak periods.

### 3.4 Private Node — Support Commitment

For Private Node deployments, Autonomyx provides the following support commitments:

(a) **Bug reports:** acknowledged within 2 Indian business days of receipt via email to support@openautonomyx.com;
(b) **Critical outages** (Platform software rendering the API completely unavailable): initial response within 8 Indian business hours;
(c) **Software updates:** made available within 30 days of a new stable release;
(d) **Scope:** these commitments cover the Platform software delivered to the Customer. They do not cover the Customer's VPS, network, operating system, Docker installation, or any infrastructure the Customer operates independently.

"Indian business hours" means 9:00 AM to 6:00 PM IST, Monday through Friday, excluding Indian public holidays.

### 3.5 Private Node — Support Boundary

| Autonomyx's responsibility | Customer's responsibility |
|---|---|
| Platform software, Docker images, configuration templates | Customer's VPS — provisioning, availability, security |
| Bug fixes and software updates | Operating system, Docker, and dependency management |
| Documentation and onboarding guidance | Data backups on the Customer's node |
| Response to Platform software issues within committed timelines | Network configuration, firewall, and SSL certificates |
| Sub-processor integrations (Langfuse, Lago traces) | Compliance obligations under applicable law for data on their node |

Managed infrastructure support beyond the above is available as a paid add-on. Contact chinmay@openautonomyx.com for pricing.

### 3.6 Beta and Experimental Features

Certain features may be made available in beta or preview. These are provided without warranty of any kind, may be discontinued at any time, and are excluded from any support commitments.

### 3.7 Sub-processors and Third-Party Models

The Platform routes requests to third-party AI model providers depending on your tier, configuration, and fallback settings. Current sub-processors include Groq, OpenAI, Anthropic, and Google Vertex AI. A current list of sub-processors is maintained at `openautonomyx.com/legal/sub-processors`. Autonomyx is not responsible for the availability, accuracy, or output quality of third-party models.

---

## 4. Acceptable Use and Prohibited Conduct

### 4.1 Permitted Use

You may use the Platform solely for lawful purposes in accordance with these Terms and all applicable laws, regulations, and third-party policies including those of sub-processors.

### 4.2 Prohibited Conduct

You must not use the Platform to:

(a) violate any applicable law, regulation, or third-party right including intellectual property, privacy, and data protection laws;
(b) resell, sublicense, or provide third-party access to your Virtual Key or API access without prior written permission from Autonomyx;
(c) mine cryptocurrency, blockchain tokens, or perform proof-of-work computations via the API;
(d) scrape, harvest, or process personal data of third parties at scale using the Playwright web scraping workflow without ensuring you have the legal right to do so under applicable data protection law including the DPDP Act 2023;
(e) generate, distribute, or store content that is defamatory, obscene, fraudulent, harassing, or that promotes violence, hatred, or discrimination;
(f) generate content designed to impersonate another person or entity, or to deceive end users about the AI-generated nature of outputs;
(g) attempt to reverse engineer, decompile, or extract the source code of the Platform beyond what is expressly permitted by open-source licences applicable to individual components;
(h) circumvent, disable, or interfere with security features, rate limits, budget controls, or access controls of the Platform;
(i) use the Platform in any manner that could damage, overburden, or impair the Platform or other customers' access to it;
(j) use outputs from the Platform to train, fine-tune, or distil competing AI models without prior written permission from Autonomyx;
(k) generate, distribute, or store child sexual abuse material or any content that sexualises minors.

### 4.3 Web Scraping — Customer Responsibility

The Platform includes a web scraping workflow powered by Playwright. When you use this feature:

(a) you represent and warrant that you have the legal right to scrape, process, and store content from each target URL;
(b) you are solely responsible for complying with the target website's terms of service, robots.txt directives, and applicable law;
(c) Autonomyx provides the technical capability only and accepts no liability for how you use it or what you scrape;
(d) you must not use the scraping workflow to harvest personal data in violation of the DPDP Act 2023, GDPR, or any other applicable data protection law.

### 4.4 AI Output Disclaimer

Outputs generated by AI models via the Platform:

(a) are not legal, financial, medical, or professional advice;
(b) may be inaccurate, incomplete, or outdated;
(c) must be reviewed by a qualified professional before being relied upon for consequential decisions;
(d) are your responsibility — Autonomyx is not liable for decisions made based on AI-generated outputs.

### 4.5 Suspension for Breach

Autonomyx reserves the right to immediately suspend or terminate your access to the Platform without notice if you breach Section 4.2 or any other material provision of these Terms. Suspension does not waive Autonomyx's right to pursue other remedies.

---

## 5. Accounts and Virtual Keys

### 5.1 Account Registration

To access the Platform you must register an account and provide accurate, complete information. You are responsible for maintaining the accuracy of your account information.

### 5.2 Virtual Keys

(a) Virtual Keys are issued to you for authenticating API requests and tracking Usage;
(b) you are solely responsible for keeping your Virtual Keys confidential;
(c) you are responsible for all Usage and Fees incurred under your Virtual Keys, whether authorised by you or not;
(d) if you believe a Virtual Key has been compromised, you must revoke it immediately via the Platform dashboard and notify Autonomyx at chinmay@openautonomyx.com;
(e) Autonomyx may revoke Virtual Keys at any time for security reasons or breach of these Terms.

### 5.3 Account Security

You are responsible for all activity that occurs under your account. Autonomyx is not liable for any loss or damage arising from unauthorised access to your account where you failed to take reasonable security precautions.

---

## 6. Fees, Billing, and Payment

### 6.1 Usage-Based Billing

All Fees are usage-based, calculated on actual token consumption, API requests, and workflow executions as recorded by our billing system. Usage records maintained by Lago (our billing sub-processor) are the authoritative record for all billing purposes.

### 6.2 Payment Processors

Payments are processed by:
- **Razorpay** — for customers paying in Indian Rupees
- **Stripe** — for international customers
- **PayPal** — where offered at checkout

By making a payment you agree to the applicable payment processor's terms of service. Autonomyx does not store your payment card details.

### 6.3 Invoicing

Invoices are generated automatically at the end of each billing cycle and delivered to your registered email address. Invoices are inclusive of applicable taxes unless stated otherwise.

### 6.4 Taxes

You are responsible for all applicable taxes, duties, and levies including GST, in connection with your use of the Platform. Where Autonomyx is required by law to collect tax, it will be added to your invoice.

### 6.5 Disputed Charges

If you believe a charge is incorrect, you must notify Autonomyx in writing within 30 days of the invoice date. Disputes raised after 30 days will not be entertained. Undisputed amounts remain due and payable.

### 6.6 Late Payment

Amounts not paid within 15 days of the invoice due date may attract interest at 1.5% per month or the maximum rate permitted by applicable law, whichever is lower. Autonomyx reserves the right to suspend access for non-payment after 7 days' written notice.

### 6.7 Refunds

All Fees are non-refundable except:
(a) where required by applicable law;
(b) where Autonomyx has materially failed to deliver the Service and the Customer has notified Autonomyx in writing within 15 days of the failure.

Free tier usage generates no charges and is not eligible for any credit or refund.

---

## 7. Data, Privacy, and Security

### 7.1 Customer Data

"Customer Data" means any data, content, or information submitted to the Platform by you or on your behalf, including prompts, inputs, documents, and URLs submitted for scraping.

### 7.2 Data Processing

(a) Autonomyx processes Customer Data solely to deliver the Service;
(b) Autonomyx does not use Customer Data to train, fine-tune, or improve AI models without your explicit opt-in consent;
(c) Customer Data processed via local Ollama models never leaves your VPS or our VPS infrastructure;
(d) Customer Data routed to cloud sub-processors (Groq, OpenAI, Anthropic, Google Vertex AI) is subject to those providers' data processing terms;
(e) trace data (LLM inputs and outputs) is stored in Langfuse, scoped to your tenant organisation, and is not accessible to other customers.

### 7.3 Private Node Data

For Private Node deployments, Customer Data processed on the Customer's own VPS remains exclusively within the Customer's infrastructure. Autonomyx has no access to data on the Customer's node unless the Customer explicitly grants access for support purposes.

### 7.4 DPDP Act 2023

Where Autonomyx processes personal data of Indian residents on your behalf, it does so as a Data Processor under the Digital Personal Data Protection Act 2023. You are the Data Fiduciary responsible for ensuring lawful processing. A Data Processing Agreement is available on request at chinmay@openautonomyx.com.

### 7.5 Security

Autonomyx implements commercially reasonable technical and organisational measures to protect the Platform and Customer Data. These include per-tenant data isolation, virtual key scoping, encrypted data in transit (TLS), and access controls. No security measure is infallible and Autonomyx does not warrant that the Platform is free from vulnerabilities.

### 7.6 Breach Notification

In the event of a confirmed data breach affecting your Customer Data, Autonomyx will notify you within 72 hours of becoming aware of the breach, to the extent reasonably practicable, in accordance with applicable law.

---

## 8. Intellectual Property

### 8.1 Platform Ownership

The Platform, including all software, workflows, documentation, and branding, is owned by or licensed to Autonomyx. Nothing in these Terms transfers any intellectual property right to you except the limited right to use the Service as described herein.

### 8.2 Open Source Components

Certain components of the Platform are open source and subject to their respective licences (MIT, Apache 2.0, AGPL-3.0). Your rights to those components are governed by the applicable open-source licence, not these Terms. A list of open-source components is available at `github.com/openautonomyx/autonomyx-model-gateway`.

### 8.3 Customer Data Ownership

You retain all ownership rights in your Customer Data. By submitting Customer Data to the Platform you grant Autonomyx a limited, non-exclusive licence to process it solely for the purpose of delivering the Service.

### 8.4 Feedback

If you provide feedback, suggestions, or ideas about the Platform, you grant Autonomyx a perpetual, irrevocable, royalty-free licence to use that feedback for any purpose without obligation to you.

### 8.5 AI Output Ownership

Autonomyx makes no claim of ownership over outputs generated by AI models in response to your prompts. Ownership of AI outputs is determined by applicable law in your jurisdiction and is your responsibility to assess.

---

## 9. Confidentiality

### 9.1 Mutual Confidentiality

Each party may disclose to the other certain non-public, confidential information ("Confidential Information"). Each party agrees to:

(a) keep Confidential Information strictly confidential;
(b) not disclose it to any third party without prior written consent;
(c) use it solely for the purposes of these Terms;
(d) protect it with at least the same degree of care it uses for its own confidential information, and no less than reasonable care.

### 9.2 Exclusions

Confidentiality obligations do not apply to information that:
(a) is or becomes publicly available through no fault of the receiving party;
(b) was already known to the receiving party without restriction;
(c) is independently developed without reference to the Confidential Information;
(d) is required to be disclosed by law or court order, provided the disclosing party is given prompt written notice where permitted.

---

## 10. Limitation of Liability

### 10.1 Exclusion of Consequential Loss

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, AUTONOMYX SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS, REVENUE, DATA, BUSINESS, OR GOODWILL, ARISING OUT OF OR IN CONNECTION WITH THESE TERMS OR THE SERVICE, EVEN IF AUTONOMYX HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

### 10.2 Liability Cap — Shared SaaS

For Free, Developer, Growth, and SaaS Basic tiers, Autonomyx's total aggregate liability to you for any and all claims arising under or in connection with these Terms shall not exceed the Fees actually paid by you in the 90 days immediately preceding the event giving rise to the claim. For Free tier customers, this amount is ₹0.

### 10.3 Liability Cap — Private Node

For Private Node customers, Autonomyx's total aggregate liability for any and all claims arising under or in connection with these Terms shall not exceed the Fees actually paid by you in the 90 days immediately preceding the event giving rise to the claim, or ₹10,000, whichever is greater.

### 10.4 Essential Basis

The parties acknowledge that the limitations of liability in this Section reflect a reasonable allocation of risk and are an essential basis of the bargain between the parties. Autonomyx would not provide the Service on these terms without these limitations.

### 10.5 Exceptions

Nothing in these Terms limits liability for:
(a) death or personal injury caused by negligence;
(b) fraud or fraudulent misrepresentation;
(c) any liability that cannot be excluded or limited under applicable law.

---

## 11. Indemnification

You agree to indemnify, defend, and hold harmless Autonomyx, its directors, employees, and agents from and against any claims, damages, losses, liabilities, costs, and expenses (including reasonable legal fees) arising out of or relating to:

(a) your use of the Platform in violation of these Terms;
(b) your Customer Data, including any claim that it infringes a third party's rights;
(c) your use of the web scraping workflow without legal authority to scrape the target content;
(d) your violation of any applicable law or regulation;
(e) any claim by your end users arising from AI-generated outputs you provide to them.

---

## 12. Term and Termination

### 12.1 Term

These Terms commence when you first access the Platform and continue until terminated in accordance with this Section.

### 12.2 Termination by You

You may terminate your account at any time by deleting your account via the Platform dashboard or by written notice to chinmay@openautonomyx.com. Termination does not entitle you to a refund of any Fees paid.

### 12.3 Termination by Autonomyx

Autonomyx may terminate or suspend your access:

(a) immediately, without notice, for breach of Section 4.2 (Prohibited Conduct) or any other material breach that is incapable of remedy;
(b) on 7 days' written notice for any material breach that is capable of remedy but remains unremedied after notice;
(c) on 30 days' written notice for any reason, with a pro-rata refund of any prepaid Fees for the unused period.

### 12.4 Effect of Termination

On termination:
(a) all Virtual Keys are immediately revoked;
(b) your right to access the Platform ceases;
(c) Autonomyx will delete or anonymise your Customer Data within 90 days unless required by law to retain it;
(d) for Private Node customers, the software continues to run on your VPS but will no longer receive updates or support;
(e) Sections 4.4, 8, 9, 10, 11, 13, and 14 survive termination.

---

## 13. Dispute Resolution and Governing Law

### 13.1 Governing Law

These Terms are governed by and construed in accordance with the laws of India, without regard to conflict of law principles.

### 13.2 Informal Resolution

Before initiating formal proceedings, the parties agree to attempt to resolve any dispute informally by written notice to the other party. The parties will negotiate in good faith for a period of 30 days from the date of notice.

### 13.3 Jurisdiction

If informal resolution fails, all disputes arising out of or in connection with these Terms shall be subject to the exclusive jurisdiction of the courts of Bengaluru, Karnataka, India. This applies to all customers including Private Node enterprise customers.

---

## 14. General Provisions

### 14.1 Entire Agreement

These Terms, together with the Privacy Policy and any order form or Statement of Work, constitute the entire agreement between the parties regarding the Platform and supersede all prior agreements, representations, and understandings.

### 14.2 Amendments

Autonomyx may update these Terms at any time. Material changes will be notified by email to your registered address at least 14 days before taking effect. Continued use of the Platform after the effective date constitutes acceptance of the updated Terms. If you do not agree to the changes, you must terminate your account before the effective date.

### 14.3 Severability

If any provision of these Terms is found to be unenforceable, that provision will be modified to the minimum extent necessary to make it enforceable, and the remaining provisions will continue in full force and effect.

### 14.4 Waiver

Failure by either party to enforce any provision of these Terms shall not constitute a waiver of that party's right to enforce it in the future.

### 14.5 Assignment

You may not assign or transfer your rights or obligations under these Terms without Autonomyx's prior written consent. Autonomyx may assign these Terms in connection with a merger, acquisition, or sale of all or substantially all of its assets.

### 14.6 Force Majeure

Neither party shall be liable for failure or delay in performance to the extent caused by circumstances beyond their reasonable control, including natural disasters, acts of government, Internet outages, third-party service failures, or labour disputes.

### 14.7 Notices

All legal notices under these Terms must be in writing and sent to:

**Autonomyx:** chinmay@openautonomyx.com
OPENAUTONOMYX (OPC) PRIVATE LIMITED
No. 78/9, Outer Ring Road, Varthur Hobli, Bellandur,
Bangalore South, Bangalore – 560103, Karnataka, India

**Customer:** the email address registered on your account.

### 14.8 Language

These Terms are drafted in English. In the event of any conflict between an English version and a translated version, the English version prevails.

---

*These Terms of Service were last updated on April 15, 2026. For questions, contact chinmay@openautonomyx.com.*

> **Legal Notice:** These Terms were drafted with AI assistance and reviewed interactively. They should be reviewed by a qualified Indian legal counsel before publication, particularly Sections 7 (DPDP Act 2023 compliance), 10 (liability limitations), and 13 (jurisdiction).
