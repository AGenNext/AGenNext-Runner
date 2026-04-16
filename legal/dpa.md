# Data Processing Agreement

**OPENAUTONOMYX (OPC) PRIVATE LIMITED**
No. 78/9, Outer Ring Road, Varthur Hobli, Bellandur, Bangalore South, Bangalore – 560103, Karnataka, India
CIN: U62010KA2026OPC215666

**Version:** 1.0
**Effective Date:** April 16, 2026

---

This Data Processing Agreement ("DPA") forms part of and is incorporated into the Agreement between OPENAUTONOMYX (OPC) PRIVATE LIMITED ("Processor", "Autonomyx") and the customer identified in the Agreement ("Controller"). This DPA governs the processing of Personal Data by Autonomyx on behalf of the Controller in connection with the Autonomyx Model Gateway platform.

---

## 1. Definitions

For the purposes of this DPA:

**"Agreement"** means the Terms of Service or other agreement between the Controller and Autonomyx governing access to and use of the Service.

**"Applicable Data Protection Law"** means, as applicable to the processing of Personal Data under this DPA:
- (a) the General Data Protection Regulation (EU) 2016/679 ("GDPR") and any national implementing legislation;
- (b) the UK GDPR and the Data Protection Act 2018 (where the Controller is established in or processes data of individuals in the United Kingdom);
- (c) the Digital Personal Data Protection Act 2023 ("DPDP Act") of India;
- (d) the California Consumer Privacy Act 2018 as amended by the California Privacy Rights Act 2020 ("CCPA/CPRA"); and
- (e) any other applicable data protection or privacy legislation.

**"Controller"** means the entity that determines the purposes and means of processing Personal Data and enters into the Agreement with Autonomyx.

**"Data Principal / Data Subject"** means the identified or identifiable natural person to whom Personal Data relates.

**"Data Processing Impact Assessment" or "DPIA"** means an assessment of the impact of processing on the protection of Personal Data as required under Article 35 GDPR or equivalent provision.

**"Personal Data"** means any information relating to an identified or identifiable natural person that is submitted to or processed by the Service.

**"Personal Data Breach"** means a breach of security leading to the accidental or unlawful destruction, loss, alteration, unauthorised disclosure of, or access to, Personal Data transmitted, stored, or otherwise processed.

**"Processor"** means Autonomyx, which processes Personal Data on behalf of the Controller.

**"Processing"** means any operation or set of operations performed on Personal Data, whether or not by automated means.

**"SCCs"** means the Standard Contractual Clauses adopted by the European Commission Decision 2021/914 of 4 June 2021.

**"Service"** means the Autonomyx Model Gateway platform, as described in the Agreement.

**"Sub-processor"** means any third party engaged by Autonomyx to process Personal Data on behalf of the Controller.

---

## 2. Scope and Role of the Parties

### 2.1 Processor Role

The Controller appoints Autonomyx as a Processor to process Personal Data on behalf of the Controller solely for the purpose of providing the Service, as further described in **Annex A** (Description of Processing).

### 2.2 Controller Instructions

Autonomyx shall process Personal Data only on documented instructions from the Controller, including those set out in this DPA and the Agreement. The Controller's use and configuration of the Service constitutes documented instructions. If Autonomyx believes an instruction infringes Applicable Data Protection Law, it shall promptly notify the Controller.

### 2.3 Autonomyx as Controller

Autonomyx processes certain Personal Data as an independent Controller for its own purposes (account management, billing, security). Such processing is governed by Autonomyx's Privacy Policy, not this DPA.

---

## 3. Controller Obligations

The Controller represents and warrants that:

(a) it has a valid lawful basis for processing Personal Data under Applicable Data Protection Law and for instructing Autonomyx to process it;

(b) it has provided all required notices and obtained all required consents from Data Subjects;

(c) the Personal Data submitted to the Service does not violate any third-party rights or Applicable Data Protection Law;

(d) where the Controller is established outside India and submits Personal Data of Indian residents, it has complied with the DPDP Act 2023 as Data Fiduciary.

---

## 4. Autonomyx Obligations

### 4.1 Confidentiality

Autonomyx shall ensure that persons authorised to process Personal Data are bound by appropriate confidentiality obligations.

### 4.2 Security

Autonomyx shall implement and maintain the technical and organisational measures described in **Annex B** (Security Measures) to protect Personal Data against the risks appropriate to the nature and context of processing.

### 4.3 Sub-processors

Autonomyx shall not engage a new Sub-processor without providing the Controller prior written notice of at least 14 days. If the Controller objects to a new Sub-processor on reasonable data protection grounds, the parties shall work in good faith to resolve the objection. The current Sub-processor list is maintained at **https://trust.openautonomyx.com#subprocessors** and set out in **Annex C**.

Autonomyx shall impose data protection obligations on all Sub-processors that are equivalent to those in this DPA, and shall remain liable to the Controller for Sub-processor performance.

### 4.4 Data Subject Rights

Autonomyx shall, taking into account the nature of processing, assist the Controller in fulfilling its obligations to respond to Data Subject requests. Where a Data Subject contacts Autonomyx directly, Autonomyx shall promptly forward the request to the Controller.

### 4.5 Assistance

Autonomyx shall provide reasonable assistance to the Controller in:

(a) conducting DPIAs where required by Article 35 GDPR or equivalent provision;

(b) engaging with supervisory authorities;

(c) fulfilling obligations under Article 32 GDPR (security) and Articles 33–34 GDPR (breach notification).

### 4.6 Deletion and Return

On termination of the Agreement, Autonomyx shall, at the Controller's election, delete or return all Personal Data and delete existing copies, unless Applicable Data Protection Law requires retention. Autonomyx will complete deletion within 90 days of termination.

### 4.7 Audit Rights

Autonomyx shall make available all information reasonably necessary to demonstrate compliance with this DPA and shall allow and contribute to audits conducted by the Controller or a mandated auditor, subject to:

(a) reasonable advance notice of at least 30 days;

(b) agreement on scope, timing, and confidentiality;

(c) audits conducted no more than once per 12-month period unless required by a supervisory authority;

(d) the Controller bearing all costs of such audits.

Autonomyx may satisfy audit obligations by providing current third-party audit reports or certifications where available.

---

## 5. International Data Transfers

### 5.1 Transfers within India

Processing on Autonomyx's self-hosted EU VPS infrastructure is subject to the DPDP Act 2023. Autonomyx maintains appropriate safeguards for cross-border transfers of data of Indian residents.

### 5.2 Transfers to Third Countries (EU/UK Controllers)

Where the Controller is established in the EU or UK and Personal Data is transferred to Autonomyx in India, or onward to US-based Sub-processors, the parties agree that the Standard Contractual Clauses adopted by the European Commission Decision 2021/914 of 4 June 2021 (Module Two: Controller to Processor) are incorporated into this DPA by reference and shall apply to such transfers. The SCCs are available at: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021D0914

For transfers subject to UK GDPR, the UK International Data Transfer Agreement (IDTA) or the EU SCCs with UK Addendum shall apply as appropriate.

### 5.3 DPDP PII Gate

Autonomyx's technical infrastructure enforces a policy-level gate (OPA) that prevents Personal Data containing PII from being routed to US-based cloud model providers (Groq, OpenAI, Anthropic, Google Vertex AI). All PII-containing requests are processed exclusively on local Ollama models hosted on Autonomyx's EU VPS. Private Node customers' data never leaves their own infrastructure.

---

## 6. Personal Data Breach

### 6.1 Notification

Autonomyx shall notify the Controller without undue delay, and in any event within **72 hours** of becoming aware of a Personal Data Breach affecting the Controller's Personal Data.

### 6.2 Breach Notification Content

The notification shall include, to the extent available at the time:

(a) nature of the breach, including categories and approximate number of Data Subjects and records affected;

(b) name and contact details of the data protection contact;

(c) likely consequences of the breach;

(d) measures taken or proposed to address the breach.

### 6.3 Controller Obligations

The Controller is responsible for notifying supervisory authorities and Data Subjects where required by Applicable Data Protection Law.

---

## 7. Liability

### 7.1 Controller Indemnity

The Controller shall indemnify and hold harmless Autonomyx from any claims, fines, or losses arising from the Controller's failure to comply with its obligations under Applicable Data Protection Law or this DPA.

### 7.2 Limitation of Liability

Autonomyx's total liability under this DPA is subject to the limitation of liability provisions in the Agreement. Each party's liability to the other shall be limited to direct damages actually suffered.

### 7.3 Regulatory Fines

If a supervisory authority imposes a fine on Autonomyx for a breach attributable solely to the Controller's instructions, the Controller shall reimburse Autonomyx for such fine.

---

## 8. Term and Termination

This DPA is effective from the date of the Agreement and continues until termination of the Agreement. Sections 5, 6, and 7 survive termination.

---

## 9. General

### 9.1 Order of Precedence

In the event of conflict, this DPA takes precedence over the Agreement with respect to data protection matters. The SCCs (where applicable) take precedence over this DPA.

### 9.2 Governing Law

This DPA is governed by the laws of India. Disputes are subject to the exclusive jurisdiction of the courts of Bengaluru, Karnataka, India, subject to any mandatory provisions of Applicable Data Protection Law that require a different jurisdiction.

### 9.3 Amendments

Autonomyx may update this DPA to reflect changes in Applicable Data Protection Law or Sub-processors. Material changes will be notified 14 days in advance. Continued use of the Service constitutes acceptance.

---

## Annex A — Description of Processing

| Element | Details |
|---|---|
| **Subject matter** | LLM inference, workflow execution, structured data processing, web scraping, translation, error tracking, and billing in connection with the Autonomyx Model Gateway platform |
| **Duration** | For the term of the Agreement |
| **Nature of processing** | Collection, storage, transmission, transformation, routing, inference, embedding, and deletion of Personal Data submitted to the Service |
| **Purpose** | Provision of the Autonomyx Model Gateway Service as instructed by the Controller |
| **Categories of Personal Data** | As submitted by the Controller: may include names, email addresses, professional information, and any other data submitted in prompts or inputs |
| **Categories of Data Subjects** | Controller's end users, employees, customers, or other individuals whose data is submitted to the Service |
| **Special categories** | Not permitted unless explicitly agreed in writing. Controller must not submit health, biometric, or other special-category data without prior written consent from Autonomyx |

---

## Annex B — Technical and Organisational Security Measures

Autonomyx implements and maintains the following measures:

**Encryption**
- TLS 1.2+ for all data in transit across all endpoints
- HTTPS enforced via Nginx and Traefik with auto-renewed Let's Encrypt certificates

**Access Control**
- Per-tenant Virtual Key isolation in LiteLLM
- Per-agent scoped credentials via OpenFGA relationship model
- Role-based access control: sponsor, owner, manager per agent identity
- No cross-tenant data access architecturally possible

**Authorisation**
- OpenFGA: relationship-based access control on every request
- OPA: conditional policy evaluation — budget, DPDP, expiry, rate limits
- Fail-closed: all requests denied if policy engine is unreachable

**Pseudonymisation and Data Minimisation**
- LLM trace data scoped per tenant organisation in Langfuse
- Usage records keyed by external customer ID, not personal identifiers
- PII routing gate: OPA policy prevents Personal Data from reaching US cloud providers

**Availability and Resilience**
- Docker restart policies on all services
- Prometheus and Grafana monitoring with alerting
- GlitchTip error tracking for incident detection

**Incident Response**
- Documented 72-hour breach notification commitment
- GlitchTip captures all system errors with agent and tenant context
- Security disclosure process documented at trust.openautonomyx.com

**Personnel**
- Confidentiality obligations on all personnel with access to Personal Data
- Access limited to personnel requiring access to provide the Service

**Subprocessor Management**
- Written agreements with all Sub-processors imposing equivalent obligations
- Sub-processor list maintained and updated at trust.openautonomyx.com

**Audit**
- All LLM calls traced in Langfuse with agent_id, tenant_id, model, timestamp
- OpenFGA logs all authorisation decisions
- Deployment audit trail via GitHub Actions CI/CD

---

## Annex C — Approved Sub-processors

The following Sub-processors are approved as of the Effective Date. Updates are published at **https://trust.openautonomyx.com#subprocessors** with 14 days' notice.

| Sub-processor | Purpose | Personal Data | Location | Safeguard |
|---|---|---|---|---|
| Razorpay | Payment processing (INR) | Name, email, billing address, transaction data | India | Contractual terms |
| Stripe | Payment processing (international) | Name, email, billing address, transaction data | USA | SCCs (2021/914) |
| PayPal | Payment processing | Name, email, transaction data | USA | SCCs (2021/914) |
| Groq | Cloud LLM inference (fallback) | Prompts — no PII (OPA gate enforced) | USA | SCCs (2021/914) |
| OpenAI | Cloud LLM inference (fallback) | Prompts — no PII (OPA gate enforced) | USA | SCCs (2021/914) |
| Anthropic | Cloud LLM inference (fallback) | Prompts — no PII (OPA gate enforced) | USA | SCCs (2021/914) |
| Google Vertex AI | Cloud LLM inference (fallback) | Prompts — no PII (OPA gate enforced) | USA (us-central1) | SCCs (2021/914) |
| Lago | Usage metering and billing | Usage records, customer ID | Self-hosted EU VPS | Contractual terms |
| Langfuse | LLM trace storage | Prompts and outputs (per-tenant isolated) | Self-hosted EU VPS | Contractual terms |
| SurrealDB Cloud | Vector storage for RAG | Scraped content and embeddings | AWS ap-south-1 (India) | Contractual terms |
| GlitchTip | Error tracking | Error messages, stack traces (no user PII) | Self-hosted EU VPS | Contractual terms |

**Note on US cloud LLM providers:** Autonomyx's OPA policy gate technically prevents Personal Data containing PII from being transmitted to Groq, OpenAI, Anthropic, or Google Vertex AI. SCCs are included as an additional safeguard for any residual transfer risk.

---

## Execution

This DPA is entered into as of the date the Controller accepts the Agreement.

**Controller**

Signed: _________________________ Date: _____________

Name: _________________________

Title: _________________________

Organisation: _________________________

**Processor — OPENAUTONOMYX (OPC) PRIVATE LIMITED**

Signed: _________________________ Date: _____________

Name: Chinmay Panda

Title: Director

CIN: U62010KA2026OPC215666

---

*This DPA was prepared with legal assistance. It should be reviewed by qualified legal counsel in the Controller's jurisdiction before execution, particularly with respect to the applicable Standard Contractual Clauses and any jurisdiction-specific requirements.*
