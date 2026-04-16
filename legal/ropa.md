# Records of Processing Activities (RoPA)
# Article 30 — General Data Protection Regulation (GDPR)
# OPENAUTONOMYX (OPC) PRIVATE LIMITED
# CIN: U62010KA2026OPC215666

**Document type:** Internal — not for public distribution  
**Maintained by:** Chinmay Panda (Data Protection Officer)  
**Last updated:** April 16, 2026  
**Review frequency:** Quarterly, or on any material change to processing activities

---

## Controller / Processor identity

| Field | Details |
|---|---|
| **Entity name** | OPENAUTONOMYX (OPC) PRIVATE LIMITED |
| **CIN** | U62010KA2026OPC215666 |
| **Registered address** | No. 78/9, Outer Ring Road, Varthur Hobli, Bellandur, Bangalore South, Bangalore – 560103, Karnataka, India |
| **Role** | Data Processor (for customer data) / Data Controller (for employee and prospect data) |
| **DPO / Grievance Officer** | Chinmay Panda — chinmay@openautonomyx.com |

---

## Processing Activity 1 — LLM Inference (Core Service)

| Field | Details |
|---|---|
| **Activity name** | LLM Inference via Model Gateway |
| **Role** | Processor (processing on behalf of Controller/customer) |
| **Purpose** | Deliver AI inference responses to customer API requests |
| **Legal basis** | Contract performance (Article 6(1)(b) GDPR) — necessary to deliver the Service |
| **Data subjects** | Customer's end users, employees, and contractors |
| **Categories of data** | API prompts and completions as submitted by the Controller. May include names, professional information, queries, or any other text the Controller chooses to submit |
| **Special categories** | None intentionally processed. Controller prohibited from submitting without written agreement |
| **Recipients** | Local Ollama models (on-VPS, no third party). Cloud fallback: Groq, OpenAI, Anthropic, Google Vertex AI (US, via SCCs) — only when local unavailable and request not flagged as containing PII |
| **Retention** | LLM traces in Langfuse: 90 days then auto-deleted. Prompts not persisted in primary DB |
| **International transfers** | Cloud fallback transfers to US — covered by SCCs (Decision 2021/914). PII blocked from US cloud by OPA policy gate |
| **Technical measures** | TLS 1.2+, OpenFGA per-agent model access control, OPA DPDP PII gate, per-tenant Langfuse isolation |
| **Processor** | Autonomyx acting as sub-processor when customer is itself a processor |

---

## Processing Activity 2 — Customer Account Management

| Field | Details |
|---|---|
| **Activity name** | Customer account registration and management |
| **Role** | Controller |
| **Purpose** | Create and manage customer accounts, authenticate users, enforce plan limits |
| **Legal basis** | Contract performance (Article 6(1)(b)) |
| **Data subjects** | Customer administrators and billing contacts |
| **Categories of data** | Name, email address, company name, billing address, phone number (optional) |
| **Special categories** | None |
| **Recipients** | Keycloak (self-hosted EU VPS — identity provider), Lago (self-hosted EU VPS — billing), Razorpay (India — payment), Stripe (US — payment, SCCs), PayPal (US — payment, SCCs) |
| **Retention** | Active: duration of account. Post-termination: 90 days then deleted. Billing records: 7 years (GST Act compliance) |
| **International transfers** | Stripe and PayPal in US — covered by SCCs |
| **Technical measures** | Keycloak SSO with MFA, Logto OIDC, TLS 1.2+, per-tenant isolation |

---

## Processing Activity 3 — Usage Metering and Billing

| Field | Details |
|---|---|
| **Activity name** | API usage tracking and invoice generation |
| **Role** | Controller |
| **Purpose** | Meter token usage per agent, calculate invoices, enforce budget limits |
| **Legal basis** | Contract performance (Article 6(1)(b)), legal obligation for GST records |
| **Data subjects** | Customer administrators |
| **Categories of data** | Customer ID, agent ID, token counts, model used, timestamp, cost in USD/INR. No prompt content. |
| **Special categories** | None |
| **Recipients** | Lago (self-hosted EU VPS), Razorpay/Stripe/PayPal (payment processing) |
| **Retention** | Usage records: 7 years (GST Act). Aggregated metrics: indefinite |
| **International transfers** | Stripe and PayPal in US — SCCs |
| **Technical measures** | Lago self-hosted, usage data scoped to customer ID, no prompt content in billing records |

---

## Processing Activity 4 — LLM Trace Observability

| Field | Details |
|---|---|
| **Activity name** | LLM trace storage for debugging and quality assurance |
| **Role** | Processor (on behalf of customer Controller) |
| **Purpose** | Store prompts, completions, token counts, and latency per agent for customer observability |
| **Legal basis** | Legitimate interest (Article 6(1)(f)) — necessary for service quality and debugging; Contract performance |
| **Data subjects** | Customer's end users (as submitted in prompts) |
| **Categories of data** | Prompts and completions as submitted. Agent ID, model, tokens, latency, timestamp |
| **Special categories** | None intentionally. Customer responsible for not submitting special category data |
| **Recipients** | Langfuse (self-hosted EU VPS) — per-tenant organisation isolation |
| **Retention** | 90 days then auto-deleted |
| **International transfers** | None — Langfuse self-hosted on EU VPS |
| **Technical measures** | Per-tenant Langfuse organisation, TLS 1.2+, no cross-tenant access possible |

---

## Processing Activity 5 — Error Tracking

| Field | Details |
|---|---|
| **Activity name** | Application error and exception tracking |
| **Role** | Controller |
| **Purpose** | Detect, alert, and resolve software errors and security incidents |
| **Legal basis** | Legitimate interest (Article 6(1)(f)) — necessary for service reliability and security |
| **Data subjects** | None directly — error payloads contain stack traces and agent IDs only |
| **Categories of data** | Stack traces, error messages, agent ID, endpoint, HTTP status code. No prompt content. No user PII. |
| **Special categories** | None |
| **Recipients** | GlitchTip (self-hosted EU VPS) |
| **Retention** | 90 days |
| **International transfers** | None — GlitchTip self-hosted on EU VPS |
| **Technical measures** | GlitchTip self-hosted, no prompt content captured in error payloads, invite-only access |

---

## Processing Activity 6 — Agent Identity and Authorization

| Field | Details |
|---|---|
| **Activity name** | AI agent identity management and access control |
| **Role** | Controller |
| **Purpose** | Create, authenticate, authorize, and lifecycle-manage AI agent identities |
| **Legal basis** | Contract performance (Article 6(1)(b)) |
| **Data subjects** | Customer administrators (as sponsors and owners of agent identities) |
| **Categories of data** | Agent name, sponsor user ID, owner user IDs, tenant ID, model allowlist, budget limit, creation timestamp |
| **Special categories** | None |
| **Recipients** | OpenFGA (self-hosted EU VPS — relationship authorization), OPA (self-hosted EU VPS — conditional policy), LiteLLM (self-hosted EU VPS — Virtual Key management) |
| **Retention** | Active: duration of agent lifecycle. Revoked: 90 days then purged. Authorization logs: 30 days |
| **International transfers** | None — all self-hosted on EU VPS |
| **Technical measures** | OpenFGA ReBAC model, OPA Rego policy engine, LiteLLM Virtual Keys scoped per agent, sponsor required at creation |

---

## Processing Activity 7 — Marketing and Sales (Prospects)

| Field | Details |
|---|---|
| **Activity name** | Lead capture and sales communications |
| **Role** | Controller |
| **Purpose** | Respond to inbound enquiries, schedule demos, manage sales pipeline |
| **Legal basis** | Legitimate interest (Article 6(1)(f)) for inbound enquiries; Consent for outbound marketing |
| **Data subjects** | Prospective customers |
| **Categories of data** | Name, email, company, job title, message content, booking details |
| **Special categories** | None |
| **Recipients** | cal.com (booking — US), Google Forms (inbound — US), email |
| **Retention** | 2 years from last contact, or until opt-out |
| **International transfers** | cal.com and Google Forms in US — standard contractual terms apply |
| **Technical measures** | Opt-out honoured within 30 days, no cold outreach without consent |

---

## Data Subject Rights — Response Procedures

| Right | Procedure | SLA |
|---|---|---|
| **Access (Article 15)** | Email chinmay@openautonomyx.com — verify identity, export data from Keycloak + Langfuse + Lago | 30 days |
| **Rectification (Article 16)** | Email request — update in Keycloak and notify sub-processors | 30 days |
| **Erasure (Article 17)** | Email request — delete from Keycloak, purge Langfuse traces, anonymise billing records (retain aggregates for GST) | 30 days |
| **Restriction (Article 18)** | Suspend agent identities, pause Langfuse tracing for tenant | 30 days |
| **Portability (Article 20)** | Export Langfuse traces and usage records as JSON on request | 30 days |
| **Object (Article 21)** | Opt out of legitimate-interest processing (error tracking, marketing) — honoured within 30 days | 30 days |

---

## Security Incident Response Procedure

1. **Detection** — GlitchTip alert or manual discovery
2. **Assessment** — determine if Personal Data affected, scope of breach
3. **Containment** — isolate affected service, rotate credentials if needed
4. **Notification** — notify affected Controllers within 72 hours per Article 33 GDPR
5. **Regulator notification** — notify supervisory authority if high risk to data subjects
6. **Post-incident** — root cause analysis, update security measures, document in incident log

---

## Review Log

| Date | Reviewer | Changes |
|---|---|---|
| April 16, 2026 | Chinmay Panda | Initial RoPA created — 7 processing activities |

---

> **Note:** This RoPA is an internal compliance document. It should be reviewed by qualified legal counsel and updated whenever a new processing activity is introduced, a sub-processor changes, or applicable law changes materially.
