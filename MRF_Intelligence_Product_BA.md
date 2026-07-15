# Oncology Drug MRF Pricing Intelligence Platform — Product Concept & BA Report

Grounded in: `Specialty Drug Pricing MRF Intelligence Report.md` (source report, cited by section #) and the 4 data assets already built in this project:
- `hcpcs_only_standardcharges.json` — 20,463 HCPCS line items, full hospital MRF
- `oncology_top5_by_category.json` — 33 top-market oncology drugs × 7 categories, hospital charges + payer rates
- `oncology_top5_asp_reference.json` — official CMS ASP payment limits for the 33 drugs (July 2026)
- `340B_pricing_research.md` — WAC/list/cash benchmarks for the 33 drugs, sourced per-drug

No feature below is justified by a number that isn't traceable to one of these 5 sources. Where I'm proposing a product decision rather than quoting a fact, it's labeled **[Product decision]**.

---

## 0. What this app actually does — plain terms

A hospital publishes a giant price file every year (the MRF). It lists every drug, every charge, every payer's negotiated rate — but nothing that tells you if that price is *fair*.

This app takes that file and answers one question per drug: **"Is this hospital charging a reasonable amount, or a huge markup?"**

It does that by lining up 3 numbers side by side for each of the 33 oncology drugs:

1. **What the hospital charges** — pulled straight from their MRF (`gross_charge`, `payers_information`).
2. **What Medicare says is fair** — the official CMS ASP price, refreshed every quarter.
3. **What the drug actually costs to buy** — the list/WAC price, and, for 340B hospitals, a price that's ~27% cheaper still.

If #1 is way bigger than #2 and #3, that's a red flag — the hospital's overcharging (or, in the case of CAR-T, sometimes it's the opposite: charge is *too low* to cover the ~$400,000 drug cost, meaning the hospital is losing money on every case).

Think of it like a car-buying site that shows you MSRP, dealer invoice, and what the dealer is actually asking — except for cancer drugs, and the stakes are a hospital either overbilling patients/insurers or bleeding money on life-saving treatment.

**Who uses it:**
- A hospital's finance team, to check if they're 340B-compliant and not accidentally losing money on CAR-T cases.
- An insurance company's contract negotiator, to spot which hospitals are overcharging so they can push back at renewal.

**Why now:** the government forces hospitals to publish this data (that's why we have the MRF file), but nobody's built the tool that actually makes the numbers mean something — that's the gap this fills.

---

## 1. Problem, grounded in the report

- CAR-T list prices run **$373,000–$475,000** (report §1); actual hospital reimbursement often lands at **$269,139–$314,231**, a **16.8%** gap even before accounting for the **$400,000+** cost vs **$269,000** case-rate reimbursement mismatch reported in §4/§7 — hospitals can lose money per case.
- Only **~130–150** centers nationwide are CAR-T certified (§1, §7), so the addressable hospital base for CGT-specific tooling is small and identifiable.
- Hospital charge markups documented in the report's case study: **$2,396 → $10,112 (4.2x)**, and separate line items marked up **190%, 203%, 173%** over acquisition cost (§4).
- 340B hospitals acquire drugs at **~27% below Medicare ASP** (§2.4/§8, COA report) but the report notes this spread is invisible in public MRFs — hospitals aren't required to disclose acquisition cost, only charges.
- Immunotherapy monthly cost was found to vary **$20,060/month vs $12,548/month (71% spread)** for clinically comparable regimens depending on site of service (§6).
- Existing competitive tools (§9.1) are point solutions: compliance checkers, buy-and-bill calculators (BuyandBill.com), generic pricing dashboards — none of them join **MRF hospital charges + CMS ASP + 340B/WAC benchmark + oncology-drug categorization** into one comparative view. That gap is the product opening the report identifies but doesn't build.

## 2. Reimbursement Schemes — the actual money flows (report §2)

This is what the app is built to expose. Four different reimbursement schemes apply to the same drug depending on payer and setting, and the report documents real numbers for each:

**Medicare Part B — outpatient "buy-and-bill" (physician-administered drugs, most of our 33 codes)**
- Standard formula: hospital gets reimbursed **ASP + 6%** (ASP = Average Sales Price, the CMS benchmark we already pulled for all 33 drugs).
- Some settings/sequestration-adjusted claims see only **ASP + 3%**.
- **340B-enrolled hospitals** acquire the same drug at **ASP − 27%** (HRSA ceiling-price discount) but still bill and get reimbursed at ASP+6% — creating a **$1,000–$3,000+ spread per infusion** that the hospital keeps. This spread is legal, but invisible in a public MRF unless you cross it against ASP like this app does.

**Medicare Part A — inpatient CAR-T/CGT (MS-DRG based)**
- Base DRG payment: **$269,139 (2025) → $314,231 (2026)**, a **16.8%** year-over-year increase.
- Drug acquisition cost alone for CAR-T therapies: **$373,000–$475,000**.
- Net result: hospitals can lose **up to $300,000+ per inpatient CAR-T case**, even after New Technology Add-on Payments (NTAP) — a structural reimbursement gap the report flags as a top financial risk for the ~130–150 certified CAR-T centers.

**Commercial payers**
- Negotiated rates run **2–7x Medicare rates**, set per individual hospital-payer contract against the Medicare DRG as an internal reference point. No standard formula — every contract is different, and none of it is visible in a single public file (this is exactly the payer-MRF gap flagged as Phase 2 in Epic 6 below).

**Medicaid**
- State-by-state inconsistency (report names Massachusetts and New York specifically) — some states reimburse off actual invoice/acquisition cost, others off a fixed fee schedule.
- CMS's Cell and Gene Therapy (CGT) Access Model, rolled out mid-2025, covers an estimated **84%** of Medicaid beneficiaries eligible for CGT drugs — meaningful but not universal.

**What this produces on the ground (hospital charge markup, report §4)**
- Case study: a line item billed at **$2,396** against a benchmark of **$10,112** — a **4.2x** markup.
- Separate line items marked up **190%, 203%, 173%** over acquisition cost.
- General range across the dataset: hospital charges run **190–300%+** over what the hospital actually paid.

This is the exact math the app runs per drug, per hospital: *what Medicare pays (ASP+6%) vs. what 340B lets the hospital acquire it for (ASP−27%) vs. what the hospital actually bills (gross_charge in the MRF)*. The gap between those three numbers is the whole product.

## 3. Product concept **[Product decision]**

**Name (working):** ClearPrice Oncology Intelligence

**What it does:** ingests a hospital's MRF (like the one in this folder), auto-classifies HCPCS codes into oncology drug categories (chemo/immunotherapy/targeted/hormone/supportive/ADC/CGT — the same 7 we built), and for each code overlays CMS ASP payment limit, WAC/list benchmark, and (where computable) an estimated 340B spread — surfacing exactly the markup gap and reimbursement-vs-cost risk the report describes, per hospital, per drug, per payer.

**Primary users:** hospital finance/340B compliance teams, payer contracting analysts, oncology service-line administrators. (Report §8.1–8.5 discusses both hospital and payer-side stakeholders — this covers both sides the report analyzes.)

## 4. Personas

| Persona | Role | Pain (from report) | Wants |
|---|---|---|---|
| Hospital 340B/Finance Analyst | Runs 340B compliance & drug cost reporting | Can't see own facility's 340B spread vs peers; CGT case losses invisible until billed (§4, §7) | Per-drug margin/loss flag before administering |
| Payer Contract Analyst | Negotiates hospital reimbursement rates | No visibility into what a hospital actually paid for a drug vs what they're billing (§2/§8.4) | Charge-to-ASP ratio benchmarking across hospitals in a market |
| Oncology Service-Line Admin | Manages CAR-T/CGT program financials | Reimbursement gap on CGT cases threatens program viability (§7, ~130-150 centers) | Early warning when a planned case's reimbursement won't cover acquisition cost |

## 5. Data source mapping (every epic ties to a file we already verified)

| Data need | Source | Status |
|---|---|---|
| Hospital gross charge / cash price / payer rates, all HCPCS | `hcpcs_only_standardcharges.json` | Built, verified against source MRF field-by-field |
| Oncology drug categorization (7 categories, market-relevance filtered) | `oncology_top5_by_category.json` | Built, 33/33 codes cross-checked vs hospital MRF |
| CMS Medicare Part B ASP payment limit | `oncology_top5_asp_reference.json` | Built from live-downloaded official CMS July 2026 file |
| WAC/list/cash benchmark per drug | `340B_pricing_research.md` | Built, 33/33 sourced, no invented figures |
| True 340B ceiling price | **Not available** — HRSA OPAIS is login-gated (confirmed, §8.2/§8.3 references 340B without exposing per-drug ceiling either) | Out of scope until hospital provides own 340B invoice data |
| Payer in-network negotiated rates (Transparency in Coverage MRFs) | Not yet ingested | **[Product decision]** — Phase 2 backlog |

## 6. Epics

### Epic 1 — MRF Ingestion & Oncology Classification
Ingest any hospital's standard-charges MRF, extract HCPCS line items, classify against the 7-category oncology drug taxonomy.
*Proven feasible*: this is exactly the pipeline already built for this hospital's file (20,463 → 33 filtered items).

### Epic 2 — CMS ASP Benchmark Overlay
For every classified oncology HCPCS code, attach the current-quarter official CMS ASP payment limit.
*Proven feasible*: already done for all 33 codes against the real July 2026 CMS file, including correctly flagging J9202 as not-separately-payable.

### Epic 3 — WAC/List Price Benchmark Overlay
Attach a WAC/list/cash-price reference per drug from public sources, each with a citation link.
*Proven feasible*: done for all 33 drugs in `340B_pricing_research.md`.

### Epic 4 — Charge-to-Benchmark Ratio & Markup Flagging
Compute gross_charge ÷ ASP and gross_charge ÷ WAC per line item; flag outliers against the report's own benchmark ranges (190–300%+, §4/§7).

### Epic 5 — CGT Reimbursement Risk Flag
For the 5 CGT codes (Q2041/Q2042/Q2055/Q2054/Q2056), compare hospital's negotiated payer rate (from `standard_charges.payers_information`) against the drug's list-price benchmark; flag if projected reimbursement is likely below acquisition cost, mirroring the report's $400,000+ cost vs $269,000 reimbursement finding (§4/§7).

### Epic 6 — Multi-Hospital / Payer Benchmarking **[Product decision, Phase 2]**
Once more than one hospital's MRF is ingested, compare the same HCPCS code's charge across facilities/regions (report §8.1 references regional/percentile variation).

### Epic 7 — Data Provenance & No-Hallucination Guardrail
Every number surfaced in the UI must carry its source (CMS file name + date, or the specific URL from `340B_pricing_research.md`). No field is shown without a citation — directly enforces the standard already applied building these files by hand.

---

## 7. User Stories (sample per epic, with acceptance criteria)

**Epic 1**
- *As a* hospital finance analyst, *I want* to upload our MRF file *so that* the system extracts and classifies our oncology HCPCS codes automatically.
  - AC: given a CMS-schema-compliant MRF JSON, system extracts all `HCPCS`-typed `code_information` entries and classifies against the 7-category taxonomy; unclassified codes remain visible but unflagged, never dropped silently.

**Epic 2**
- *As a* 340B analyst, *I want* to see the current CMS ASP payment limit next to each drug's hospital charge *so that* I can spot billing-vs-benchmark gaps.
  - AC: ASP value sourced only from the current-quarter official CMS ASP Pricing File; if a code is in CMS's "Not Payable Under Part B" file instead, show that status explicitly rather than a blank or zero.

**Epic 4**
- *As a* payer contract analyst, *I want* a markup ratio per drug *so that* I can prioritize which codes to renegotiate.
  - AC: ratio = gross_charge / ASP_payment_limit; codes with ratio > 3x (aligned to report's 190–300%+ finding) surfaced in a priority queue.

**Epic 5**
- *As a* oncology service-line admin, *I want* a red/yellow/green flag on CGT cases *so that* I know before scheduling if the case is financially exposed.
  - AC: flag = RED if payer negotiated rate < WAC benchmark for that CGT code; flag stores which benchmark and payer rate were compared, for audit.

**Epic 7**
- *As any* user, *I want* every number to show its source *so that* I trust the platform isn't fabricating data.
  - AC: no numeric field renders without a `source_url` or `source_file` tooltip; codes with no available benchmark show "not publicly available" rather than a guessed value — same rule already enforced building `340B_pricing_research.md` by hand.

## 8. Explicit assumptions vs. verified facts

**Verified (from report or our built files):** CAR-T price range, 130-150 center count, 4.2x/190-300% markup figures, 340B ~27% ASP discount, ASP+6%/ASP-27% reimbursement mechanics, all 33-drug pricing figures and their exact source links, CMS July 2026 ASP file contents, J9202 non-payable status.

**Assumptions (product decisions, not report facts) — labeled [Product decision] above:** product name, UI flagging thresholds (3x ratio, red/yellow/green), Phase 2 payer-MRF ingestion scope, multi-hospital benchmarking. None of these are claimed as report findings.

## 9. Out of scope / known gaps (stated, not hidden)
- True 340B ceiling price per drug — HRSA-gated, not obtainable without hospital's own OPAIS credentials.
- NADAC — doesn't apply (physician-administered drugs, per your earlier instruction to drop it).
- Payer Transparency-in-Coverage MRFs — not yet ingested, needed for Epic 6.
