# ClearPrice Oncology Intelligence — Houston Area v1 Design

Date: 2026-07-15
Status: Approved for planning

## 1. Purpose

Turn hospital MRF (machine-readable file) price transparency data into a tool that
answers, per oncology drug per hospital: *is this charge fair, relative to what
Medicare pays (ASP) and what the drug costs to acquire (WAC/340B)?*

Scope of v1: Houston-area hospitals only. Architecture must generalize to other
metros/states later without rework (Epic 6 in `MRF_Intelligence_Product_BA.md`),
but v1 ships Houston only.

Grounded in, and must stay consistent with:
- `MRF_Intelligence_Product_BA.md` (epics, personas, data source mapping)
- `Specialty Drug Pricing MRF Intelligence Report.md` (source figures, cited by section)
- `ClearPrice_Build_Methodology.html` §4 (worked example — the exact output template)
- `oncology_top5_by_category.json`, `oncology_top5_asp_reference.json`,
  `340B_pricing_research.md` (already-verified data for Houston Methodist Hospital)

**Hard rule carried through every section below: no number is invented, estimated,
or interpolated without an explicit source citation and, where it's a calculation
rather than a quoted figure, an explicit formula shown next to it.**

## 2. Hospital universe (Houston scope)

Source: `Texas_validated_final.xlsx`, sheet `MRF Validation` (700 Texas hospitals,
columns: Hospital Name, Homepage URL, MRF Link, MRF File Type, Link Status, HTTP
Code, Detected From, Notes). No city/address column exists, so hospital selection
is done by name-pattern matching against known Houston-metro branch names and
health systems, manually reviewed and approved (see conversation log for the
review pass — 5 false positives removed: Ascension Seton Southwest Hospital,
North Texas Medical Center, Cypress Creek Hospital, Kingwood Pines Hospital,
Nexus Specialty Hospital-The Woodlands).

**Inclusion rule:**
- Acute-care general or cancer-treating hospital
- Branch name maps to a Houston-metro city/area (Houston, Sugar Land, The
  Woodlands, Baytown, Cypress, Clear Lake, Kingwood, Tomball, Willowbrook,
  Pearland, Conroe, Katy, League City, Missouri City, Richmond, etc.), or is a
  known Houston-anchored system branch (Memorial Hermann, Texas Children's, Ben
  Taub, Houston Methodist, HCA Houston Healthcare)
- MRF link status = OK (HTTP 200) at last validation

**Exclusion rule:**
- Standalone behavioral-health, physical-rehab-only, or orthopedic-only facilities
  (no oncology infusion service line)
- Branches of a matching chain name located outside Houston metro (e.g. Lufkin,
  Livingston, San Augustine, Lake Jackson, San Antonio, Austin)
- Broken/dead links (404 / NOT_FOUND) — excluded from ingestion, not fabricated

**Locked v1 list: 44 hospitals with working MRF links** (10 more matched the
naming pattern but had dead links and are excluded), spanning: Houston Methodist
(8, including the already-parsed Houston Methodist Hospital), HCA Houston
Healthcare (9), Memorial Hermann (10, incl. Children's/Women's), Texas Children's
(3), St. Luke's Health (2) + Baylor St. Luke's (1), UTMB Health (2), Ben Taub (1),
BMC Baytown (1), Houston Physicians' (1). Full list with URLs cached at
`houston_candidates_final.json`.

Formats across these 44: mixed json, csv, zip (needs unzip step), and
Azure-blob-with-SAS-token URLs. No uniform schema can be assumed beyond the
CMS-mandated MRF field set.

## 3. Ingestion pipeline

Per hospital, in order:
1. **Fetch** — download the MRF link. Handle zip (extract), SAS-token URLs
   (pass through query string as-is, don't strip).
2. **Parse** — load into the hospital's native schema (CMS standard-charges JSON
   schema, or CMS-required wide/tall CSV format).
3. **Filter** — extract only line items whose `code_information` matches one of
   the 33 target HCPCS/Q codes already defined in `oncology_top5_by_category.json`.
   Nothing else is extracted or stored.
4. **Normalize** — reshape into the same structure already used in
   `oncology_top5_by_category.json` (description, code, standard_charges by
   setting/billing_class, payers_information array).
5. **Tag provenance** — every normalized record stores: hospital name, source
   file name/URL, retrieval timestamp.
6. **Failure handling (explicit, never silent):**
   - Code not published by this hospital → `not published by this hospital`
   - File fails to parse / unsupported schema / link now dead → `ingestion
     failed: <reason>`, hospital excluded from results for that drug only (not
     dropped from the hospital list entirely — other drugs from the same
     hospital may still have parsed fine)

Output: one normalized dataset per hospital, same shape as the existing
Methodist Hospital file, written to `houston_hospitals/` — which is the mount
path of the Docker data volume described in §7, not a separate location. That
volume (git-ignored; large source files never enter the repo) is the single
place this data lives.

## 4. 340B enrollment verification ("verify twice" requirement)

Per hospital, query HRSA's **public** 340B OPAIS covered-entity search (the
covered-entity enrollment lookup is public; only the ceiling-price-per-NDC lookup
is login-gated — confirmed in `340B_pricing_research.md` §"Why exact 340B ceiling
prices are not shown"). Match by hospital name / NPI.

- Run the lookup **twice**, independently, before setting the enrollment flag.
  Both results must agree; a mismatch is logged and the hospital's 340B status is
  marked `unverified` rather than guessed.
- Cache: enrollment status (yes/no/unverified), lookup date, source URL.
- If enrolled → the calc engine includes the ASP−27% acquisition-cost line and
  spread (Section 5 below), explicitly labeled as an industry-average estimate,
  not the hospital's actual confidential ceiling price.
- If not enrolled → that line is omitted entirely; only ASP+6% standard
  reimbursement math applies.

## 5. Calculation engine

Runs per (selected drug × hospital), reproducing exactly the structure in
`ClearPrice_Build_Methodology.html` §4:

| Layer | Value | Source |
|---|---|---|
| Hospital gross charge (min–max, per payer, per setting) | from that hospital's normalized MRF extract | hospital MRF file name + retrieval date |
| CMS Medicare Part B ASP payment limit | `oncology_top5_asp_reference.json` | CMS ASP Payment Limit File, current quarter |
| ASP+6% (standard Part B reimbursement) | calculated: ASP × 1.06 | formula shown inline |
| ASP−27% (est. 340B acquisition cost) — **only if hospital verified 340B-enrolled** | calculated: ASP × 0.73 | formula shown inline, labeled "industry-average discount (COA report), not this hospital's actual ceiling price" |
| 340B spread | calculated: reimbursement − est. acquisition cost | formula shown inline |
| WAC/list benchmark | `340B_pricing_research.md` | per-drug citation link already in that file |
| Markup ratio | calculated per individual payer rate: that payer's rate ÷ ASP (not computed on the aggregate min–max range) | flagged if > 3x (per BA doc Epic 4 threshold) |
| CGT reimbursement risk (Q2041/Q2042/Q2055/Q2054/Q2056 only) | DRG payment ($269,139 / $314,231) vs. list-price acquisition cost | red flag if hospital's negotiated/DRG reimbursement is below list-price benchmark |

Every rendered number carries a visible source tag (file name+date, or a link)
matching the citation style already in `340B_pricing_research.md` and the HTML's
`<span class="src">` treatment. No field renders blank-but-implied-zero; codes
with no available benchmark show "not publicly available."

### 5.1 Payer-scheme verification (mandatory, twice, before any per-payer calc)

§4's worked example lists 18 named payer/plan rows for one drug at one hospital
(Aetna – HMO/POS/PPO, Aetna – Medicare Managed Care HMO/PPO, Aetna – New Business
Discount, BCBS – All Commercial Plans, BCBS – Medicare Managed Care HMO, Cigna –
Local Plus/SureFit HMO/PPO, Cigna – Network C-24 HMO/PPO, Cigna – PCP
Optional/Required HMO, Cigna – TX HealthSpring Medicare HMO/PPO, Community Health
Choice – D-SNP Medicare HMO, Community Health Choice – Silver & Gold Exchange,
Molina – Advantage Medicare Plan, Molina – Exchange, and others in that hospital's
own file). These "schemes" are payer/plan rows the hospital chose to publish in
its own MRF `payers_information` array — they are hospital-specific, not
universal.

Rule: before computing any per-payer margin/verdict line for a given
hospital+drug, check **twice** whether that specific payer/plan scheme is present
in that hospital's own normalized MRF extract (independent re-check of the parsed
record against the raw source file).
- Present in both checks → include that payer's rate in the calculation.
- Absent in both checks → do not include it; do not substitute another
  hospital's rate or a category average for it.
- Disagreement between the two checks → mark that payer row `unverified` for
  this hospital, exclude from calculation, and log the discrepancy.

No hospital's results ever include a payer scheme it did not itself publish.

### 5.2 Adult dose scale (per drug, sourced, never assumed, never copied across drugs)

§4's "/dose" figures (e.g. "$60.29/mg × 200 mg = $12,058.00 billed") are a
calculated scale-up of the hospital's own per-mg/per-unit rate — the hospital's
MRF never states a dose quantity itself (confirmed: `oncology_top5_by_category.json`
stores only per-mg/per-unit rates, no dose field, for all 33 drugs). §4's 200 mg
Keytruda figure is **specific to Keytruda's own FDA label** and must not be
reused, copied, or pattern-matched onto any other drug. Every one of the 33
drugs gets its own independent FDA-label lookup and its own dose figure — no
shared or default scale.

Rule per drug: use that drug's own FDA prescribing label, standard/most common
adult oncology regimen, at approximate normal-weighted-adult usage (i.e. the
regimen as an average/typical adult patient would receive it — not a
pediatric, renal-adjusted, or dose-reduced variant). Three dosing patterns
appear across the 33 drugs, each handled per that drug's own label:

- **Fixed dose (e.g. pembrolizumab 200 mg IV q3w per its label):** use that
  exact label figure, cited to that drug's label.
- **Weight-based, mg/kg (e.g. some monoclonal antibodies per their own
  labels):** use that drug's own label mg/kg figure × a disclosed reference
  adult body weight (70 kg — the standard reference weight used in clinical
  pharmacology dosing, not invented), cited to that drug's label + the 70 kg
  reference convention.
- **Body-surface-area, mg/m² (e.g. Paclitaxel J9267, per its own label; likely
  others — carboplatin-type/AUC dosing):** use that drug's own label mg/m²
  figure × a disclosed reference adult BSA (1.7 m², the standard reference BSA
  used in clinical pharmacology dosing, not invented), cited to that drug's
  label + the 1.7 m² reference convention.

For the weight- and BSA-based cases, the resulting "/dose" figure is
**explicitly labeled** "illustrative reference dose (this drug's own label
regimen × reference adult weight/BSA) — not this hospital's actual patient
dose," the same disclosure §4 already gives its own 200 mg scale-up rather than
presenting it as hospital-stated fact.

Every dose-scale value carries its own source citation (that specific drug's
FDA label link + access date) directly next to it, same as every other number
in this app. This is 33 individual label lookups — one per drug — never
inferred or defaulted from another drug's regimen.

## 6. UI

- **Drug picker:** all 33 drugs as checkboxes, grouped under their 7 categories
  (Chemotherapy, Immunotherapy, Targeted Therapy, Hormone Therapy, Supportive
  Care, Antibody-Drug Conjugates, Cellular and Gene Therapy) — same taxonomy as
  `oncology_top5_by_category.json`.
- **Results view:** on selection, list only hospitals (of the 44) that publish at
  least one selected drug. Hospitals with a failed ingestion for a given drug show
  "MRF unavailable" for that cell instead of being silently dropped from the list.
- **Detail view — one full §4-style breakdown per hospital, per selected drug:**
  for every drug the user checks, the app renders the complete Section-4-style
  breakdown (readout cards, sources table, verdict block, margin-formula table,
  all-payer rate table, dose-scale disclosure per §5.2) for **every hospital (of
  the 44) that publishes that drug in its own MRF** — not one example hospital
  per drug. If the user selects N drugs, and a given drug is published by M of
  the 44 hospitals, that drug gets M full breakdowns, one per hospital. Computed
  live from ingested data, never hardcoded to the Keytruda example.
- **Visual style:** reuse the existing `ClearPrice_Build_Methodology.html`
  look (same CSS variables/typography) for continuity.
- **Rendering scale:** selecting many drugs (up to all 33) across 44 hospitals
  can produce hundreds of full breakdowns in one view. Results are grouped by
  drug first, then by hospital within that drug, and rendered/loaded
  incrementally (not all at once) rather than a single giant unpaginated page.

## 7. Tech stack

- **Backend:** Python (ingestion pipeline + calc engine + FastAPI JSON API) —
  consistent with the user's existing Python/Anaconda environment.
- **Frontend:** plain HTML/JS (no build step), styled to match the existing
  methodology HTML. No framework needed for a checkbox-driven, single-page tool.
- **Data storage:** normalized per-hospital JSON files, one per hospital, stored
  inside a Docker container (dedicated data volume/container — e.g.
  `clearprice-data`). The ingestion pipeline writes all 44 hospitals' normalized
  MRF extracts into that container's volume; it is the single source of truth.
  Both the FastAPI backend and the frontend read exclusively from that
  container's data (via the backend, which mounts the volume) — no results are
  computed from files elsewhere on disk once ingestion has run. Rationale: one
  place to inspect/audit what data the app is actually using, and portable to
  redeploy elsewhere later (Phase 2, other metros).

## 8. Out of scope for v1 (stated, not hidden)

- True 340B ceiling price per drug (HRSA OPAIS ceiling-price lookup is
  login-gated; not obtainable — same conclusion as `340B_pricing_research.md`).
- Non-Houston hospitals (Phase 2, per BA doc Epic 6).
- Payer Transparency-in-Coverage MRFs (Phase 2, per BA doc Epic 6).
- The 5 excluded false-positive hospitals and 10 dead-link hospitals from the
  naming-pattern match — not ingested in v1.

## 9. Open verification note

MD Anderson Cancer Center and Kelsey-Seybold Clinic — both real, prominent
Houston oncology providers — do **not** appear anywhere in
`Texas_validated_final.xlsx`'s 700-row list under any name variant checked. They
are excluded from v1 not because they were reviewed and rejected, but because no
MRF link for them exists in the source file at all. Flagged here rather than
silently omitted.

## 10. Fresh-eyes review — risks flagged before implementation

- **Per-drug label verification is 33 separate lookups, not one pattern.**
  Confirming fixed-dose vs. weight/BSA-based, and the exact cited regimen, has
  to be done individually per drug against its FDA label. Cannot infer drug #2's
  dosing pattern from drug #1's — different drugs, different labels, different
  regimens (and some drugs have multiple FDA-approved regimens/indications;
  where that's true, the specific regimen/indication cited must be stated next
  to the number, not left ambiguous).
- **Reference-BSA figures are still an illustrative construct, not this
  hospital's real patient dose** — disclosed per §5.2, but worth restating: any
  "per dose" dollar figure for a weight/BSA-based drug is a labeled reference
  calculation, never presented as fact the hospital charges per full course.
- **Combinatorial rendering load.** 33 drugs × 44 hospitals is up to 1,452
  possible full breakdowns if every drug were published everywhere (in practice
  fewer, since not every hospital publishes every code) — confirmed the design
  already requires incremental/grouped rendering (§6) rather than one flat page.
- **Ingestion is the long pole, not the UI.** 43 of the 44 hospitals' MRFs are
  still unparsed (only Houston Methodist Hospital's file is processed today).
  Formats vary (json/csv/zip/SAS-token URLs, §2) — some will likely fail to
  parse cleanly on the first pass and need per-hospital debugging, per §3's
  explicit `ingestion failed: <reason>` handling (never papered over).
- **340B enrollment lookup is a live external dependency** (HRSA OPAIS public
  search, §4) — if that site's structure changes or a hospital's registered
  name doesn't match cleanly, the double-check can legitimately land on
  `unverified` for some hospitals; that's the correct outcome per the spec, not
  a bug to work around by guessing.
- **No blocking unknowns found beyond the above** — all are execution-effort
  and disclosure items, not open design questions.
