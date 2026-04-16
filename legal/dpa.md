# Data Processing Agreement

**OPENAUTONOMYX (OPC) PRIVATE LIMITED**
No. 78/9, Outer Ring Road, Varthur Hobli, Bellandur, Bangalore South, Bangalore – 560103, Karnataka, India
CIN: U62010KA2026OPC215666

**Version:** 1.0  
**Effective Date:** April 16, 2026

---

This Data Processing Agreement ("DPA") forms part of the Terms of Service between **OPENAUTONOMYX (OPC) PRIVATE LIMITED** ("Processor", "Autonomyx") and the customer entity that has accepted those Terms ("Controller").

This DPA applies where and to the extent Autonomyx processes Personal Data on behalf of the Controller in the course of providing the Autonomyx Model Gateway service ("Service").

---

## 1. Definitions

| Term | Meaning |
|---|---|
| **Personal Data** | Any information relating to an identified or identifiable natural person, as defined under applicable Data Protection Law |
| **Data Protection Law** | All applicable laws and regulations relating to the processing of Personal Data, including the GDPR, UK GDPR, DPDP Act 2023, and any national implementing legislation |
| **GDPR** | Regulation (EU) 2016/679 of the European Parliament and of the Council |
| **DPDP Act** | The Digital Personal Data Protection Act 2023 (India) |
| **Controller** | The customer entity that determines the purposes and means of processing Personal Data |
| **Processor** | Autonomyx, which processes Personal Data on behalf of the Controller |
| **Data Subject** | The natural person to whom Personal Data relates |
| **Processing** | Any operation performed on Personal Data |
| **Sub-processor** | Any third party engaged by Autonomyx to process Personal Data on behalf of the Controller |
| **Security Incident** | Any confirmed breach of security leading to accidental or unlawful destruction, loss, alteration, unauthorised disclosure of, or access to, Personal Data |
| **Services** | The Autonomyx Model Gateway platform as described in the Terms of Service |
| **SCCs** | The Standard Contractual Clauses adopted by the European Commission by Decision 2021/914 of 4 June 2021 |

---

## 2. Scope and Roles

### 2.1 Processor role

Autonomyx processes Personal Data solely as a data processor, acting on the instructions of the Controller. The Controller is the data controller (or data fiduciary under the DPDP Act) for all Personal Data processed under this DPA.

### 2.2 Subject matter

The subject matter of processing includes:

- Routing API requests containing Controller-supplied prompts to local or cloud AI models
- Storing LLM trace data in Langfuse (self-hosted, per-tenant isolated)
- Processing usage data for billing records
- Error tracking via GlitchTip (stack traces only — no prompt content)

### 2.3 Processing details

| Element | Details |
|---|---|
| **Nature** | LLM inference, trace storage, usage metering, error tracking |
| **Purpose** | Delivery of the Autonomyx Model Gateway service |
| **Duration** | Term of the agreement plus legal retention obligations |
| **Data subjects** | Controller's employees, contractors, and end users |
| **Categories of data** | As submitted in API prompts; account and billing data |
| **Special categories** | Not processed — Controller must not submit without prior written agreement |

---

## 3. Controller Instructions

Autonomyx shall process Personal Data only on documented instructions from the Controller. The Terms of Service and this DPA constitute those instructions. If required by law to process otherwise, Autonomyx shall notify the Controller unless prohibited.

---

## 4. Autonomyx's Obligations

### 4.1 Confidentiality

Personnel authorised to process Personal Data are subject to binding confidentiality obligations.

### 4.2 Security

Autonomyx implements and maintains appropriate technical and organisational measures as described in Annex B.

### 4.3 Sub-processors

The Controller provides general authorisation for sub-processors listed in Annex C. Autonomyx shall:

(a) notify the Controller at least 30 days before adding or replacing a sub-processor;
(b) impose equivalent data protection obligations on sub-processors;
(c) remain liable for sub-processor performance.

### 4.4 Data subject rights

Autonomyx shall assist the Controller with Data Subject rights requests through appropriate technical measures where feasible.

### 4.5 DPIA assistance

Autonomyx shall provide reasonable assistance for Data Protection Impact Assessments where the assistance relates to information available to Autonomyx.

### 4.6 Deletion or return

Upon termination, Autonomyx shall delete or return all Personal Data within 90 days, certifying deletion in writing upon request, unless retention is required by law.

### 4.7 Audit rights

Autonomyx shall support audits by the Controller or mandated auditor, subject to:

(a) 30 days prior written notice;
(b) once per year unless a confirmed Security Incident has occurred;
(c) costs borne by the Controller;
(d) auditor signing a non-disclosure agreement before receiving information.

---

## 5. Controller's Obligations

The Controller warrants it has a lawful basis for processing, shall not submit special category data without prior agreement, and is responsible for notifying Data Subjects of Autonomyx's role as processor.

---

## 6. Security Incident Notification

Autonomyx shall notify the Controller within 72 hours of becoming aware of a confirmed Security Incident affecting Controller Personal Data, including: nature of the incident, categories and approximate number of affected data subjects and records, likely consequences, and measures taken.

---

## 7. International Transfers

### 7.1 SCCs

Where Autonomyx transfers Personal Data of EU/EEA Data Subjects to US-based sub-processors, such transfers are made pursuant to the Standard Contractual Clauses (Controller-to-Processor, Module 2) adopted by European Commission Decision 2021/914 of 4 June 2021, incorporated into this DPA by reference:
`https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32021D0914`

### 7.2 UK transfers

For UK Data Subjects, the UK International Data Transfer Agreement (IDTA) or EU SCCs plus UK Addendum apply as appropriate.

### 7.3 India transfers

For Indian residents, Autonomyx complies with the DPDP Act 2023 and shall not transfer personal data to countries without adequate protection without appropriate safeguards.

### 7.4 DPDP technical control

An OPA policy engine enforces that requests flagged as containing personal data (`contains_pii: true` in metadata) are never routed to US-based cloud model providers. PII-containing requests are processed exclusively by local Ollama models on Autonomyx's EU-based VPS.

---

## 8. Private Node Deployments

For Private Node customers, the Controller operates the software on their own infrastructure and is the sole Data Fiduciary for data processed there. This DPA does not apply to data processed exclusively on a Private Node.

---

## 9. Liability

Each party is liable for damages caused by its breach of this DPA per the Terms of Service liability provisions. Autonomyx is exempt where it proves it is not responsible for the event causing damage.

---

## 10. Term and Termination

This DPA runs for the duration of the Terms of Service. Sections 4.6, 6, and 9 survive termination.

---

## 11. Governing Law

Governed by the laws of India. Mandatory provisions of the Controller's EU/EEA jurisdiction prevail where they conflict.

---

## Annex A — Processing Details

| Item | Details |
|---|---|
| **Controller name** | [Customer entity name] |
| **Controller address** | [Customer registered address] |
| **Processor** | OPENAUTONOMYX (OPC) PRIVATE LIMITED, Bengaluru, India |
| **Service tier** | [Free / Developer / Growth / SaaS Basic / Private Node] |
| **Nature** | LLM inference, trace storage, usage metering, error tracking |
| **Purpose** | Delivery of the Autonomyx Model Gateway service |
| **Data subjects** | Controller's employees, contractors, and end users |
| **Categories of data** | API prompts and outputs; account data; usage and billing data |
| **Retention** | LLM traces: 90 days. Billing: 7 years (GST). Account data: 90 days post-termination |
| **Transfer mechanism** | SCCs (EU Commission Decision 2021/914) for US sub-processors |

---

## Annex B — Technical and Organisational Security Measures

**Encryption in transit**
TLS 1.2+ on all endpoints via Nginx and Traefik. Automatic HTTP to HTTPS redirect. Certificates issued and auto-renewed via Let's Encrypt.

**Access control**
Per-tenant Virtual Key isolation in LiteLLM. Per-agent scoped credentials via OpenFGA relationship model. Three-role agent governance: Owner, Sponsor, Manager. Master key never exposed to agent-level operations.

**Authorization**
OpenFGA relationship-based authorization on every request. OPA conditional policy evaluation: budget, expiry, DPDP PII gate, TPM rate limits. PII-flagged requests never routed to US cloud providers.

**Infrastructure security**
All containers run as non-root users. OCI image annotations on all custom builds. Secrets stored in server environment — never committed to version control. CI/CD pipeline: tests gate build, build gates deploy.

**Monitoring**
GlitchTip (self-hosted): error tracking per agent and tenant, no prompt content in error payloads. Langfuse (self-hosted): per-tenant LLM trace observability. Prometheus and Grafana: infrastructure metrics. All authorization decisions logged.

**Data isolation**
Langfuse traces scoped to tenant organisation. Lago billing records scoped to customer ID. Namespace isolation per tenant in all data stores.

**Vulnerability management**
All Docker image versions pinned — no `:latest` in production. Dockerfile linting via hadolint in CI. GitHub Actions enforces: test then build then deploy.

---

## Annex C — Approved Sub-processors

| Sub-processor | Purpose | Location | Transfer mechanism |
|---|---|---|---|
| **Razorpay** | Payment processing (INR) | India | Contractual |
| **Stripe** | Payment processing (international) | USA | SCCs (Decision 2021/914) |
| **PayPal** | Payment processing | USA | SCCs (Decision 2021/914) |
| **Groq** | Cloud LLM inference (fallback only) | USA | SCCs (Decision 2021/914) |
| **OpenAI** | Cloud LLM inference (fallback only) | USA | SCCs (Decision 2021/914) |
| **Anthropic** | Cloud LLM inference (fallback only) | USA | SCCs (Decision 2021/914) |
| **Google Vertex AI** | Cloud LLM inference (fallback only) | USA (us-central1) | SCCs (Decision 2021/914) |

**Excluded from this list (self-hosted on Autonomyx EU VPS):**
Lago, Langfuse, GlitchTip, OpenFGA, OPA, Keycloak — these are not third-party sub-processors.

**SurrealDB:** Self-hosted on Private Node deployments only. Personal data is not routed to SurrealDB Cloud on shared SaaS tiers.

**Cloud LLM note:** US-based cloud providers receive prompts only as fallback when local Ollama models are unavailable, and only for requests not flagged as containing personal data.

---

## Annex D — Contact

**Autonomyx Data Protection and Grievance Officer**
Chinmay Panda
OPENAUTONOMYX (OPC) PRIVATE LIMITED
Email: chinmay@openautonomyx.com
Response time: Within 30 days

To request a signed DPA:
Email: chinmay@openautonomyx.com
Subject: "DPA Request — [Company name]"

---

> **Legal Notice:** This DPA was drafted with AI assistance. It must be reviewed by qualified legal counsel before execution — particularly Sections 7 (international transfers and SCCs), 9 (liability), and Annex B (technical measures). Standard Contractual Clauses are incorporated by reference to European Commission Decision 2021/914.
