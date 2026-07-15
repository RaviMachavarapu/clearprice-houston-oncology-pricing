# Specialty Drug Procurement, Reimbursement & MRF-Based Pricing Intelligence
### CAR-T, Gene Therapy, Immunotherapy, and Chemotherapy — A Data Platform Opportunity

***

## Executive Summary

The U.S. market for highly specialized oncology and cell/gene therapies represents the most financially complex, opaque, and inefficient segment of healthcare pricing. CAR-T cell therapies now cost between $373,000 and $475,000 for the drug product alone, with total care costs per patient exceeding $1 million when hospitalizations and complications are factored in. Gene therapies for conditions like sickle cell disease carry list prices exceeding $2–3 million per patient. Yet despite years of mandated price transparency, hospitals receive wildly variable reimbursement for the same drugs — with four national insurers paying between $830 and $10,878 for identical bevacizumab products at the same hospitals. This report examines how hospitals procure and get reimbursed for these therapies, decodes the federal drug pricing benchmarks available to analysts, and maps a compelling data product opportunity — combining hospital MRF data, payer MRF data, and federal drug pricing benchmarks — to build actionable pricing intelligence for hospitals, payers, and patients.[^1][^2][^3]

***

## 1. How Hospitals Procure Specialty Drugs

### 1.1 The Buy-and-Bill Model

The dominant procurement model for physician- and hospital-administered specialty drugs — including chemotherapy, immunotherapy checkpoint inhibitors, and CAR-T — is **buy-and-bill**. Under this model, a hospital purchases the drug from a manufacturer, wholesaler, or distributor; administers it to the patient; and then bills the patient's insurer for both the drug and the associated clinical services. The drug is processed under the patient's **medical benefit**, not the pharmacy benefit — a distinction that creates dramatically different cost-sharing obligations and reimbursement pathways.[^4][^5]

For standard chemotherapy and immunotherapy agents (e.g., Keytruda/pembrolizumab, Avastin/bevacizumab, Opdivo/nivolumab), hospitals purchase from pharmaceutical distributors at prices referenced against the **Wholesale Acquisition Cost (WAC)** — the manufacturer's published list price — or negotiate below-WAC contracts with large wholesalers. For hospitals enrolled in the **340B Drug Pricing Program**, acquisition prices can be dramatically lower — approximately ASP minus 27% on average, according to MedPAC — creating a significant "spread" between what is paid and what is billed.[^6][^2]

### 1.2 CAR-T and Gene Therapy: A Fundamentally Different Procurement Path

CAR-T therapies (tisagenlecleucel/Kymriah by Novartis; axicabtagene ciloleucel/Yescarta by Kite/Gilead; lisocabtagene maraleucel/Breyanzi by Bristol Myers Squibb) operate under an entirely different model. These are **autologous therapies** — manufactured from the patient's own T-cells — so they cannot be stocked in inventory. The hospital must:[^1]

1. Perform **leukapheresis** (T-cell collection) from the patient
2. Ship the cells to the manufacturer's certified processing facility
3. Receive the engineered CAR-T product back under stringent cold-chain conditions weeks later
4. Administer the infusion in a **Qualified Treatment Center (QTC)** — currently only ~130–150 U.S. centers are certified[^7]
5. Manage intensive post-infusion monitoring for serious adverse events including Cytokine Release Syndrome (CRS) and immune effector cell-associated neurotoxicity syndrome (ICANS)

This model locks CAR-T almost exclusively to **large academic medical centers**, as community hospitals lack the infrastructure, certified personnel, and financial reserves to absorb the upfront capital. Because FDA originally required CAR-T administration only at specially certified hospitals, most U.S. cancer patients — who receive care at community settings — have historically had limited access.[^8]

Gene therapies (e.g., Casgevy and Lyfgenia for sickle cell disease, Hemgenix for hemophilia B, Luxturna for inherited retinal dystrophy) face similar procurement dynamics, but are administered as **one-time curative treatments** delivered at specialty infusion centers, often affiliated with academic medical systems.

### 1.3 Distribution Variants: White-Bagging and Brown-Bagging

Beyond buy-and-bill, two other distribution models increasingly compete for specialty drugs, particularly as payers attempt to redirect drugs through specialty pharmacies:[^4]

- **White-bagging**: A specialty pharmacy ships a patient-specific drug directly to the provider for administration. The provider does not take ownership and bills only for administration, not the drug.
- **Brown-bagging**: The patient picks up the drug from a specialty pharmacy and brings it to the provider for infusion.

Payers prefer white/brown-bagging because it shifts drug purchasing away from hospitals (where markups are highest) to specialty pharmacies (where PBM-negotiated rates apply). Hospitals strongly resist this because it eliminates the lucrative drug margin embedded in buy-and-bill.[^9]

***

## 2. Reimbursement Mechanisms: Medicare, Medicaid, and Commercial Payers

### 2.1 Medicare Inpatient: The MS-DRG System for CAR-T

For Medicare beneficiaries receiving CAR-T as an **inpatient**, CMS pays under a **Medicare Severity Diagnosis-Related Group (MS-DRG)**. Following significant advocacy by treatment centers, CMS created **MS-DRG 018** specifically for CAR-T cell therapy. For FY 2025, the base reimbursement rate for MS-DRG 018 is **$269,139**, rising to approximately **$314,231** in FY 2026 — a 16.8% increase. However, given that drug acquisition costs alone range from $373,000 to $475,000, this fixed DRG payment leaves hospitals with a structural deficit before any other care costs are counted.[^10][^11][^12]

Previously, hospitals relied on a **New Technology Add-On Payment (NTAP)** to supplement the DRG, but this mechanism provides temporary relief and applies only while a therapy is classified as "new technology". Without it, hospitals face losses of up to $300,000 per inpatient CAR-T case under Medicare.[^13][^12][^14]

CMS also applies a **72-hour rule**: if a CAR-T patient given in the outpatient setting is hospitalized within 3 days, the case reverts to the inpatient DRG mechanism, undermining theoretical outpatient financial advantages.[^1]

### 2.2 Medicare Outpatient: ASP + 6% and the Part B Drug Benefit

For drugs administered in the **outpatient hospital setting**, including most chemotherapy and immunotherapy infusions, Medicare pays under the **Average Sales Price (ASP) + 6% add-on** methodology. The ASP is a volume-weighted average of manufacturer sales prices to all U.S. purchasers, net of all rebates, chargebacks, and discounts. CMS publishes ASP pricing quarterly. The 6% add-on is intended to cover handling, storage, administration complexity, and geographic purchasing variation.[^15][^16][^6]

Key dynamics under the Part B system:
- **Large health systems** can negotiate drug acquisition prices at or below ASP (due to purchasing volume), meaning they profit from the +6% spread
- **Solo practitioners** and small community hospitals typically purchase drugs at ASP +3%, leaving them with effectively a net loss on the Medicare spread[^17]
- **340B-enrolled hospitals** acquire drugs at approximately ASP −27%, earning substantial margins on Medicare ASP + 6% reimbursements, yielding spreads of $1,000–$3,000+ per infusion for common oncology drugs[^2]

### 2.3 Commercial Payer Reimbursement

Commercial payers have historically reimbursed hospitals using several methodologies:[^18]
- **Percentage of Charges (% of Charges)**: The most lucrative for hospitals, where the hospital's internally set chargemaster price is the baseline. Hospitals earning reimbursement as a % of their inflated gross charges can receive 2–7x the amount that Medicare would pay
- **Percentage of WAC or AWP**: Common in older commercial contracts; less favorable than % of charges but still above ASP
- **ASP-based rates**: Typically applied only in physician office settings; rarely applied at hospitals
- **Case rates (bundled payments)**: Flat payments for an entire episode — increasingly used for CAR-T, where commercial payers negotiate a single case rate covering drug + infusion + monitoring

For CAR-T specifically, ZS Associates found that commercial reimbursement via case rates generally provides hospitals with "measured upside" — meaning profitability — in contrast to the structurally deficient Medicare DRG. However, this upside varies significantly by institution: prestigious academic medical centers with greater negotiating leverage command substantially higher commercial rates than regional or community hospitals.[^1]

The degree of profitability depends almost entirely on **negotiation leverage**, and negotiated rates remain highly confidential. This is precisely where MRF data becomes transformative.[^1]

### 2.4 Medicaid: Structural Underpayment and the CGT Access Model

Medicaid reimbursement for specialty drugs is deeply inadequate for cell and gene therapies. Most state Medicaid programs pay based on **fixed bundled payment rates** that do not account for drug acquisition costs at scale. Some states, such as California, Massachusetts, and New York, have published "carve-out" policies that reimburse providers at acquisition/invoice cost for high-cost therapies, but this remains inconsistent.[^19]

CMS launched the **Cell and Gene Therapy (CGT) Access Model** in January 2025 to directly address this gap. The model is a Medicaid demonstration program in which CMS negotiates **outcomes-based agreements (OBAs)** with manufacturers on behalf of all participating states. If a therapy fails to achieve promised clinical outcomes, the manufacturer provides rebates or refunds to the state. As of mid-2025, 33 states plus the District of Columbia and Puerto Rico have signed on, representing approximately 84% of Medicaid beneficiaries with sickle cell disease. The initial focus is on FDA-approved gene therapies for sickle cell disease (Casgevy and Lyfgenia), but the model is designed to expand to additional CGTs.[^20][^21][^22]

### 2.5 Innovative Payment Models for One-Time Therapies

The one-time nature of gene therapies creates a fundamental tension with insurance systems built around recurring payments. Several models are now in active use or development:[^23]

| Model | Description | Examples |
|-------|-------------|---------|
| **Outcomes-Based Agreement (OBA)** | Manufacturer refunds or rebates if therapy underperforms vs. agreed outcomes | Kymriah/Yescarta in EU, Luxturna–Harvard Pilgrim[^24] |
| **Annuity/Installment Payment** | Cost spread over 3–5 years, mitigating single-year budget shock | Novartis/Zolgensma 5-year plan via Accredo[^24] |
| **Warranty** | Manufacturer guarantees a minimum clinical benefit; provides financial compensation if not met | Emerging CGT models[^25] |
| **Milestone Rebates** | Payments tied to clinical milestones at defined follow-up intervals | EU-based CGT agreements[^26] |
| **Third-Party Financial Intermediation** | A neutral party negotiates OBAs with both manufacturers and payers, eliminating provider financial risk | Proposed by USC Schaeffer Center[^27] |

The core challenge is patient churn across payers — if a patient switches insurers after receiving a one-time curative therapy, the original payer absorbs full cost but future payers benefit from improved health without contributing to the cost.[^27]

***

## 3. Federal Drug Pricing Data Infrastructure

### 3.1 The Master Benchmarks

A rich set of federally maintained and commercially available pricing benchmarks form the foundation of any drug pricing intelligence system:

| Benchmark | Definition | Source | Use Case |
|-----------|------------|--------|----------|
| **WAC** | Manufacturer list price to wholesalers before discounts | Manufacturer-reported | Gross charge baseline; commercial contract starting point |
| **AWP** | Historical "sticker price" ~20–25% above WAC | Compendia (Wolters Kluwer, Elsevier) | Older % of AWP contracts; pharmacy billing |
| **ASP** | Volume-weighted average net price to all U.S. purchasers, after all rebates | CMS (quarterly)[^15] | Medicare Part B drug payment benchmark; gold standard for physician-administered drugs |
| **ASP + 6%** | Medicare's outpatient payment rate for Part B drugs | CMS | Provider reimbursement floor; benchmarking reference |
| **NADAC** | Average pharmacy invoice acquisition cost, surveyed weekly | CMS/Medicaid[^28][^29] | Retail/community pharmacy benchmarking |
| **340B Price** | Discounted price for qualifying covered entities (~ASP −22.5% on average) | HRSA OPA[^30] | Covered entity drug cost baseline |
| **MFP** | Maximum Fair Price negotiated by CMS under Inflation Reduction Act | CMS | IRA-selected Part B/D drugs |
| **AMP** | Average manufacturer price to retail pharmacies | Manufacturer-reported to CMS | Medicaid rebate calculations |

### 3.2 Hospital MRF Data (Hospital Price Transparency Rule)

Since January 2021, all U.S. hospitals are required to publish a **machine-readable file (MRF)** containing:[^31]
- Gross charges (chargemaster prices)
- Discounted cash prices
- Payer-specific negotiated rates (as dollar amounts or algorithms)
- De-identified minimum and maximum negotiated charges

As of 2024, CMS mandated compliance with a standardized schema (version 2.0 finalized; enforcement from February 2026). Starting January 1, 2025, hospitals must include **drug-specific pricing**, with requirements to report NDC codes, HCPCS codes, and unit pricing for over 700 buy-and-bill drugs.[^32][^33]

**Key data quality finding**: An analysis of 1,300+ hospital MRFs found that while 93% of files adhered to the required format, only **62% contained usable drug pricing data** — the distinction between "in-form" compliance and "in-spirit" compliance. Prices for the same drug can differ by **10-fold or more** within the same hospital depending on payer contract and billing unit conventions.[^34]

### 3.3 Payer MRF Data (Transparency in Coverage Rule)

Since July 2022, all non-grandfathered group health plans and insurers must publish monthly MRFs containing:[^35]
- In-network negotiated rates with all providers
- Historical out-of-network allowed amounts
- Prescription drug negotiated rates and historical net prices (including rebates, discounts, dispensing fees, and administrative fees)

The payer MRF data is enormous — individual payer files can reach hundreds of gigabytes — and the schema is evolving (updated version effective February 2026). Turquoise Health aggregates over a **trillion records** from provider, payer, professional, drug, and device rates. Serif Health ingests **billions of rows monthly** across all published MRFs.[^36][^37][^35]

***

## 4. What the Data Reveals: Pricing Variation as a Market Signal

### 4.1 The Scale of Reimbursement Variation

The empirical reality from MRF analysis is striking. Analysis of four national commercial insurers (Aetna, Anthem, Cigna, UnitedHealthcare) and 26 cancer hospitals found:[^2]

- For bevacizumab (Avastin), reimbursement to the same hospitals by Aetna ranged from **$2,396 to $10,112** — a **4.2x spread** for the identical drug
- For Mvasi (a bevacizumab biosimilar), reimbursement ranged from **$1,025 (Cigna)** to **$6,756 (Aetna)**
- For Zirabev (another biosimilar), payment ranged from **$830 (UnitedHealthcare)** to **$6,012 (Aetna)**
- Hospitals, on average, received **190% of ASP** for Avastin, **203% of ASP** for Mvasi, and **173% of ASP** for Zirabev[^2]
- In 1 out of 10 cases, hospital reimbursement for a biosimilar **exceeded the brand drug's list price**

A separate comprehensive analysis of 1,300+ hospital MRFs found that even when the same insurer is controlling reimbursement, there is an average **$35,000+ difference** in therapy cost depending on which hospital a patient visits — a spread large enough to cover interstate travel while still generating significant savings.[^34]

This data paints a clear picture: the current buy-and-bill market for specialty drugs is characterized by **systematic pricing disorder**, not rational market pricing.

### 4.2 Interpreting Wide Reimbursement Ranges

When MRF data shows a wide range of negotiated or reimbursed prices across hospitals or payers for the same drug, this is **not random noise** — it is a layered signal encoding multiple market inefficiencies:

**Signals indicating hospital bargaining power differentials:**
- Large academic medical centers with regional monopoly or "must-have" network status extract premium rates from payers who cannot afford to exclude them[^38][^39]
- Community hospitals, lacking negotiating leverage, accept rates near or below Medicare rates
- The result: the same drug can command 2–3x higher reimbursement at UCLA Ronald Reagan vs. a regional community hospital[^2]

**Signals indicating 340B program exploitation:**
- 340B-enrolled hospitals acquire drugs at approximately ASP −27% and bill commercial payers at 190–300% of ASP, generating spreads of $3,000+ per infusion[^40][^2]
- A 2022 analysis found 340B hospitals price the top oncology drugs at **4.9 times their 340B acquisition cost**[^41][^42]
- Over $124 billion in 340B drug spending flowed through the healthcare ecosystem in 2023[^40]

**Signals indicating contracting methodology heterogeneity:**
- Some hospitals bill as % of charges; others under case rates; others as % of WAC or ASP. MRFs cannot yet reliably separate these methodologies, making direct comparison hazardous without normalization[^43]

**Signals indicating true losses for some providers:**
- For Medicare CAR-T cases, even the highest-end community hospital cannot negotiate above the fixed DRG rate. With drugs costing $400,000+ and DRG reimbursement at $269,000, these hospitals absorb losses measured in hundreds of thousands per case[^12][^14]
- A narrow negotiated rate below ASP + 6% for a community hospital **does not necessarily represent efficiency** — it more likely represents financial distress and lack of leverage

**Signals indicating payer-specific contract blind spots:**
- Wide ranges across payers for the same hospital and drug reveal that individual payer contracting teams are operating without market intelligence. Aetna consistently paid 2–4x what UnitedHealthcare paid for the same drugs at the same hospitals[^2]

***

## 5. The Hospital Perspective: Community vs. Large Academic Systems

### 5.1 Large Academic Medical Centers

Large academic health systems (e.g., MD Anderson, Memorial Sloan Kettering, Mayo Clinic, UPMC, Cleveland Clinic) hold **dominant structural advantages** in specialty drug economics:

- They are the **only credentialed CAR-T treatment centers** (FDA requirements initially limited administration to ~130–150 certified centers)[^8][^7]
- Their "must-have" network status gives them maximum commercial contracting leverage — payers cannot exclude them without risking patient revolt
- They operate large 340B programs, capturing the maximum acquisition discount spread
- They have pharmacy directors and financial modeling teams who optimize cost-to-charge ratios and negotiate effective case rates[^1]
- Revenue from commercially insured CAR-T cases (profitable at commercial case rates) cross-subsidizes Medicare losses

Even so, the aggregate CAR-T financial picture is challenging: ZS research found that some large centers minimize Medicare losses by marking up CAR-T charges to **multiple times the actual cost** to generate favorable cost-to-charge ratios in CMS reimbursement calculations.[^1]

### 5.2 Community and Regional Hospitals

For community and regional hospitals, the economics of highly specialized therapies are dire:

- **CAR-T access**: Most community hospitals cannot qualify as treatment centers — they lack REMS certification, bone marrow transplant programs, and ICU-level monitoring capabilities[^44][^8]
- **Chemotherapy and immunotherapy**: Community hospitals do administer standard chemotherapy and checkpoint inhibitors, but their acquisition costs are higher and their commercial negotiated rates are lower
- A matched analysis found that patients treated in hospital-based settings paid **$20,060/month vs. $12,548/month** in community-based practices, with **71% higher chemotherapy costs** specifically[^45]
- Community practices typically purchase drugs at ASP +3%, leaving no meaningful spread under Medicare's ASP +6% reimbursement[^17]
- Without 340B eligibility or commercial contracts above WAC, community hospitals face **structural losses on nearly every specialty drug infusion** under government payers

The financial consequences extend to patient access: smaller hospitals and rural cancer centers increasingly decline to administer expensive specialty drugs because the financial risk is too high. This is one of the most important but least-visible access crises in modern oncology.[^46][^8]

### 5.3 The 340B Divide

The 340B program creates a fundamental bifurcation in the hospital market. Qualifying covered entities include disproportionate share hospitals (DSH), rural referral centers, and critical access hospitals — in theory, safety-net providers who serve low-income patients. However, program expansion has extended 340B benefits to hospital systems with multiple outpatient pharmacy "child sites" in affluent neighborhoods. Key observations:[^47][^48]

- Nearly **half of hospitals** qualifying for 340B are using the drug discounts to increase profits and consolidate market power rather than passing savings to patients[^48]
- 340B activity growth at the state level accounted for approximately **8% of overall growth in employer-based health insurance premiums** over recent years[^40]
- 340B-eligible DSH hospitals price oncology drugs at 4.9x their acquisition cost vs. a target of providing affordable access[^41]
- For cancer patients with employer-sponsored insurance, 340B hospitals represent a higher-cost site of care — the opposite of the program's intent[^45]

***

## 6. The Patient Perspective

### 6.1 Financial Toxicity

"Financial toxicity" — the term oncologists use for the economic harm caused by cancer treatment costs — is a recognized clinical problem with measurable health consequences. Patients with cancer spend a median of $1,730–$4,727 annually on out-of-pocket expenses, an estimated $976–$1,170 higher than comparable patients without cancer. For immunotherapy specifically:[^49]

- A full course of immunotherapy checkpoint inhibitor treatment can cost more than **$150,000**, with Medicare spending rising $19,000 per melanoma patient after immune checkpoint inhibitor introduction[^50]
- CAR-T therapy total costs frequently exceed $500,000–$1,000,000 per patient, making it the most expensive Medicare DRG[^3]
- Patients and caregivers face burdens beyond drug costs: travel to certified centers, lodging, caregiver time, and non-medical expenses[^44]
- 76% of cancer patients enrolled in clinical trials reported moderate-to-severe financial burden[^51]

### 6.2 Access Disparities Amplified by Pricing Complexity

The pricing variation revealed by MRF data is not clinically neutral — it translates directly into access disparities:[^52][^46]

- Patients residing in lower-income or rural areas are less likely to receive immunotherapy, with education and income-stratified odds ratios of 0.71 for both[^52]
- Patients with private insurance treated at academic centers are far more likely to receive CAR-T and immunotherapy than Medicaid patients or those at community hospitals[^8]
- Because CAR-T is limited to ~150 academic centers, patients must often travel long distances — adding financial and logistical burden that compounds health inequity[^44]
- Insurance authorization barriers remain the most commonly cited access obstacle for CAR-T, with prior authorization denials disproportionately affecting Medicaid patients[^44]

***

## 7. The Data Product Opportunity: Combining MRF + Federal Benchmarks

### 7.1 The Data Architecture

The most powerful pricing intelligence system for specialized drugs would combine multiple authoritative data layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEDERAL BENCHMARKS (Static Reference)         │
│  CMS ASP Quarterly Files  |  NADAC Weekly  |  WAC Compendia     │
│  340B HRSA Ceiling Prices |  MFP (IRA)    |  AMP / MDRP Rebates│
└─────────────────────────────────────────────────────────────────┘
                              ↕  Join on NDC / HCPCS
┌─────────────────────────────────────────────────────────────────┐
│              HOSPITAL MRF DATA (Hospital Price Transparency)     │
│  Gross Charges  |  Cash Prices  |  Payer-Specific Negotiated    │
│  Rates by NDC/HCPCS  |  Min/Max Negotiated Charges             │
│  340B indicator (derivable from hospital type + HRSA data)      │
└─────────────────────────────────────────────────────────────────┘
                              ↕  Join on NPI / TIN / Payer Name
┌─────────────────────────────────────────────────────────────────┐
│           PAYER MRF DATA (Transparency in Coverage Rule)         │
│  In-Network Negotiated Rates  |  Historical Net Prices          │
│  Out-of-Network Allowed Amounts  |  Drug-Specific Rates         │
└─────────────────────────────────────────────────────────────────┘
                              ↕  Join on CMS Certification Number
┌─────────────────────────────────────────────────────────────────┐
│              HCRIS COST REPORT DATA (CMS Annual)                 │
│  Hospital Type / Bed Count  |  340B Status  |  Case Mix Index   │
│  Cost-to-Charge Ratios  |  Teaching Status  |  Payor Mix        │
│  Medicare/Medicaid Days  |  Urban/Rural Classification          │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Key Analytical Products

**1. Drug Pricing Benchmark Dashboard (per NDC/HCPCS code)**
- Display WAC, ASP, ASP+6%, 340B ceiling price, and NADAC for each drug
- Overlay hospital-reported gross charges, cash prices, and payer-specific negotiated rates
- Compute **markup multiples** (Negotiated Rate / ASP+6%) by hospital, payer, and geography
- Flag anomalies: rates below acquisition cost (potential loss indicators), rates above 3x ASP (potential excessive markup), biosimilar rates exceeding reference product

**2. Hospital Reimbursement Position Analysis**
- For each hospital: compute its full reimbursement profile across all reported payers
- Compare to peer cohort (by bed size, teaching status, 340B eligibility, urban/rural)
- Identify payers where the hospital is significantly under-reimbursed vs. market median
- Estimate annual dollar impact of underpriced contracts using claims volume proxies (from HCRIS cost reports)

**3. Payer Contract Intelligence Tool**
- For each payer-hospital pair: identify contracted rate vs. market min/median/max
- Flag payers systematically overpaying certain hospitals (potential anti-competitive arrangements)
- Model the cost impact of moving member volume from high-cost to mid-cost providers

**4. 340B Spread Estimator**
- For each 340B-eligible hospital: compute estimated acquisition cost (from HRSA ceiling price data) vs. reported negotiated reimbursement
- Compute **spread = Reimbursement − Acquisition Cost** per drug per payer
- Flag cases where patients bear coinsurance calculated on inflated billed charges while hospitals earn large spreads

**5. CAR-T and Gene Therapy Access Mapping**
- Map certified CAR-T treatment centers against patient population demographics
- Overlay Medicare MS-DRG 018 reimbursement rates vs. estimated total costs
- Identify geographies where access is constrained by financial viability of nearby treatment centers
- Model which community hospitals could viably expand CAR-T access if commercial contracting rates were adjusted

### 7.3 Normalization Challenges and Solutions

The core technical problem with raw MRF data is **heterogeneity** — different hospitals and payers express the same information in structurally incompatible ways:[^53][^43]

| Challenge | Description | Resolution Approach |
|-----------|-------------|---------------------|
| **Contracting methodology mismatch** | Some hospitals report dollar amounts; others report % of charges or % of fee schedule. Comparing these directly yields false conclusions[^43] | Normalize all rates to dollar amounts using hospital-specific average charges from HCRIS cost reports |
| **Billing unit inconsistency** | The same drug may be reported per mg, per vial, per 100mg, or per administration. NDC unit reconciliation is essential[^54] | Build NDC-to-unit crosswalk; normalize to per-mg or per-standard-dose |
| **Payer/plan name variation** | "UnitedHealthcare," "UHC," "United Health Group" appear as different entities in different MRFs | Entity resolution using fuzzy matching + payer ID registries |
| **Missing NDC data** | 65% of drug MRF records from payer files had missing NPI, reimbursement rate, or NDC information[^54] | Impute using HCPCS-to-NDC crosswalks; flag confidence levels |
| **In-form vs. in-spirit compliance** | Only 62% of hospital files contain usable drug pricing[^34] | Score completeness; weight analysis toward complete reporters; track improvement over time |

Your existing architecture using **Kinetica + H3** is well-suited to this workload: H3 hexagonal indexing can efficiently associate each hospital with its market competitive environment, while Kinetica's GPU-accelerated SQL can handle the trillion-row payer MRF datasets that compete with companies like Turquoise Health and Serif Health.

***

## 8. Value Creation by Stakeholder Segment

### 8.1 Community Hospitals and Regional Health Systems

These are arguably the highest-value customers, because they are the most disadvantaged in the current market and have the least internal analytical capability:

- **Reimbursement benchmarking**: "Here is what your peers are receiving from Aetna for pembrolizumab — you are at the 22nd percentile. Here is the estimated annual revenue impact of bringing your rate to the 50th percentile."
- **Contract negotiation ammunition**: Historical negotiated rates from comparable hospitals give smaller institutions data to push back on payer lowball offers
- **340B optimization**: For eligible community hospitals, modeling optimal drug ordering under 340B program to maximize spread without triggering compliance violations
- **CAR-T viability modeling**: Financial feasibility analysis for community hospitals considering CAR-T program expansion — what commercial contract terms would need to be achieved to break even?

### 8.2 Large Academic Medical Centers

While these institutions have more internal sophistication, they face different challenges:

- **Payer contract auditing**: Are all payers adhering to contracted rates? MRF data can reveal systematic underpayment patterns
- **Market share defense**: As the pricing data becomes public, payers may pressure high-rate hospitals. Understanding the full market distribution helps develop defensible rate justifications
- **340B compliance risk monitoring**: Tracking the expanding regulatory and legal scrutiny of 340B spreads; modeling financial impact of potential program changes

### 8.3 Commercial Payers and Employers

Payers increasingly need to justify specialty drug reimbursement to self-insured employer clients:

- **Network design optimization**: Identify which hospitals within a market provide the best clinical outcomes per dollar for specific therapy types — particularly relevant for CAR-T where outcomes data is now becoming available
- **Outlier payment detection**: Using MRF data to identify payer-hospital-drug combinations where the insurer is paying above market (often due to legacy contracts not renegotiated as the market evolved)
- **Prior authorization target selection**: Identify drugs and sites of care with the widest spread between minimum and maximum negotiated rates — these are highest-priority for utilization management

### 8.4 Patients and Patient Advocacy Organizations

- **Hospital selection tool**: Show patients the out-of-pocket cost differential for receiving the same immunotherapy infusion at different network hospitals — even within the same insurer network, variation can be $10,000+ per treatment course
- **Financial toxicity early warning**: For CAR-T candidates, model total expected patient cost burden including travel, lodging, and out-of-pocket maximums across different insurance plans and treatment centers
- **Access gap mapping**: Geographic visualization of CAR-T access deserts — areas with large patient populations but no financially viable treatment center within reasonable distance

### 8.5 Drug Manufacturers and Market Access Teams

- **Real-world reimbursement intelligence**: For new therapy launches, understanding the distribution of negotiated rates for comparable drugs helps set realistic WAC pricing and anticipate payer pushback
- **Site-of-care financial modeling**: Model whether a drug's commercial viability is better under buy-and-bill vs. specialty pharmacy distribution at different types of provider sites
- **Outcomes-based contract design**: Market data on reimbursement ranges helps manufacturers design OBAs with floor prices that keep providers financially viable while tying upper payments to outcome milestones

***

## 9. Competitive Landscape and Differentiation

### 9.1 Existing Players

| Company | Focus | Strength | Gap |
|---------|-------|----------|-----|
| **Turquoise Health** | MRF aggregation, contract intelligence, compliance[^36][^55] | Broadest dataset (~1T records), VC-backed, SaaS platform | Not specialty drug-specific; generic rate benchmarking tool |
| **Serif Health** | MRF analytics, payer contracting intelligence[^37] | High data quality, payer-side focus | Primarily general services, not drug pricing-specific |
| **3 Axis Advisors + hospitaldrugprices.org** | Drug pricing research + dashboard[^34] | Deep drug pricing focus, academic credibility | Not a commercial product; limited interactive analytics |
| **ZS Associates + Turquoise** | Specialty drug reimbursement analytics[^56][^57] | Strong pharma client base, deep drug analytics | Consulting/research model; not a self-serve SaaS for hospitals |
| **BuyandBill.com**[^58] | ASP/WAC/AWP search tool | Free tool, HCPCS lookup | No MRF integration; no benchmarking against peers |
| **Drug Channels Institute** | Research reports on buy-and-bill[^2] | High-quality analysis | Subscription research; not actionable analytics |

### 9.2 Differentiation Opportunity

A specialized platform focusing on **high-cost specialty drugs** (CAR-T, gene therapy, checkpoint inhibitors, oncology biologics) and combining:
1. Normalized hospital and payer MRF data
2. Federal benchmarks (ASP, WAC, NADAC, 340B ceiling prices)
3. HCRIS cost report stratification (hospital size, 340B status, teaching status, payer mix)
4. Geospatial analysis of market concentration and access gaps

...would fill a documented white space. The market currently lacks a product that gives **community hospitals the same pricing intelligence that large academic systems have by virtue of their internal analytics teams**. This is particularly relevant given the February 2026 MRF schema 2.0 enforcement deadline and January 2025 drug reporting requirements — there is a fresh wave of drug pricing data only now becoming clean enough to analyze at scale.

***

## 10. Is Wide Price Variation Indicative of Losses or Inefficiencies?

The answer is both — but in a non-uniform and often counterintuitive way:

**Wide variation where a hospital is at the LOW end of the range:**
- For CAR-T and gene therapies: almost certainly indicates **financial losses** on Medicare/Medicaid cases. The fixed DRG rate is structurally below drug acquisition cost regardless of the hospital's negotiating position
- For standard chemotherapy/immunotherapy: indicates either lack of negotiating leverage (community hospital), inadequate 340B program utilization, or acceptance of Medicare-equivalent rates from commercial payers

**Wide variation where a hospital is at the HIGH end of the range:**
- Often indicates **excess hospital profit** — particularly at 340B-eligible academic centers where drug acquisition at ASP−27% is combined with commercial billing at 200-400% of ASP
- May reflect legitimate market power (regional monopoly status) or historical contracts not renegotiated in a transparent era

**Wide variation across payers for the same hospital:**
- Indicates **payer-level contracting inefficiency** — different payer teams negotiated independently without market information, producing rates that are clearly not anchored to any rational benchmark
- Post-transparency, this spread should theoretically compress. The evidence from 2025 data suggests it has not[^2]

**Wide variation across hospitals for the same payer and drug:**
- Primarily reflects **market structure** (competition, hospital market power) more than clinical or cost differences
- Provides the clearest signal for payer network optimization: why is Aetna paying Ronald Reagan UCLA 4x what it pays UPMC Shadyside for the same drug?[^2]

The critical analytical framework is always to **benchmark against ASP+6% as the floor and WAC as the ceiling** for the commercial market. Any negotiated rate below ASP+6% for a hospital (without 340B acquisition advantage) is a strong indicator of financial loss. Any negotiated rate above 200% of ASP for a hospital warrants scrutiny regarding whether that reflects legitimate complexity premium or market exploitation.

***

## 11. Policy Tailwinds and Regulatory Trajectory

Several concurrent policy developments strengthen the data opportunity:

1. **Executive Order 14221 (February 2025)**: President Trump's EO directed rapid action to improve hospital and health plan price transparency, leading to the May 2025 cross-agency guidance requiring hospitals to post actual prices (not estimates) in MRFs[^59][^60][^35]
2. **MRF Schema Version 2.0 (enforcement February 2026)**: Standardized format will dramatically improve data comparability and reduce the normalization burden for MRF analytics platforms[^32]
3. **Drug Reporting Requirement (effective January 2025)**: Hospitals must now include Part B drug pricing data in their MRFs, creating the first systematic public database of hospital-reported drug prices keyed to NDC codes[^33]
4. **IRA Drug Price Negotiation**: CMS's Maximum Fair Price (MFP) for IRA-selected drugs creates a new pricing floor; MFP data will need to be incorporated into benchmarking models as affected drugs come off patent/negotiation cycles
5. **CGT Access Model expansion**: As more states join outcomes-based agreements for cell/gene therapies, the data infrastructure for tracking clinical performance against payment will create demand for outcomes-linked pricing analytics

***

## 12. Implementation Roadmap for a Specialty Drug Pricing Intelligence Platform

### Phase 1: Foundation (Months 1–3)
- **Data ingestion**: Establish pipelines for CMS ASP quarterly files, NADAC weekly files, WAC/AWP from commercial compendium licenses, HRSA 340B ceiling price files, HCRIS cost report downloads
- **MRF normalization engine**: Build NDC/HCPCS unit crosswalk; implement billing unit normalization; apply contracting methodology detection algorithms
- **Hospital taxonomy**: Enrich each hospital with HCRIS attributes (bed count, 340B status, teaching status, rural/urban, case mix index, payer mix) joined via CMS Certification Number (CCN)
- **Focus universe**: Target 50 high-cost specialty drugs (CAR-T HCPCS codes, top checkpoint inhibitors, bevacizumab/biosimilars, rituximab/biosimilars, trastuzumab/biosimilars)

### Phase 2: Analytics (Months 4–6)
- Build benchmark overlay engine: for each hospital-drug-payer tuple, compute Negotiated Rate / ASP+6% markup multiple
- Implement peer cohort engine: cluster hospitals by HCRIS attributes; compute percentile ranks within cohorts
- 340B spread estimator: join hospital MRF rates against HRSA ceiling prices; compute estimated gross margin per drug per payer
- CAR-T access map: H3-based geospatial analysis of certified treatment center proximity to patient populations

### Phase 3: Product (Months 7–12)
- SaaS portal for hospital CFO/managed care contracting teams: payer-by-payer benchmark reports, revenue impact modeling, contract renewal prep
- Employer/payer analytics module: network cost optimization, outlier detection, benchmark reporting for self-insured plan sponsors
- Patient-facing cost estimator: hospital comparison tool for high-cost drug therapies by insurer and geography
- API/data licensing tier for pharmaceutical manufacturers (reimbursement intelligence, market access planning)

***

## Conclusion

The intersection of CAR-T, gene therapy, immunotherapy, and chemotherapy drug pricing represents the most financially consequential and analytically underserved domain in U.S. healthcare. The combination of MRF data from both hospitals and payers — normalized against federal benchmarks (ASP, WAC, NADAC, 340B ceiling prices) and enriched with HCRIS hospital characteristics — creates a uniquely powerful foundation for a pricing intelligence platform. Wide variation in negotiated rates is simultaneously a signal of market inefficiency, predatory contracting, financial distress, and systemic access inequity — and therefore exactly the kind of multi-valued signal that a sophisticated data product can decode and monetize across all healthcare stakeholders. The policy trajectory strongly favors more complete and standardized data disclosure through 2026 and beyond, and the current crop of MRF analytics platforms (Turquoise Health, Serif Health, ZS/Turquoise partnership) do not specifically serve the **community hospital contracting** and **specialty drug benchmarking** use cases with the depth this market needs.

---

## References

1. [CAR-T reimbursement in the US: ZS separates myths from reality](https://www.zs.com/insights/car-t-reimbursement-in-the-us-zs-separates-myth-from-reality) - Unlike traditional therapies, the commercial reimbursement mechanism and margins for CAR-T are simil...

2. [Markup Madness 2025: Hospitals, Insurers, and the Broken Buy-and ...](https://www.drugchannels.net/2025/08/markup-madness-2025-hospitals-insurers.html) - ASP approximates the commercial pricing of a provider-administered drug, so this measure includes th...

3. [Navigating the Financial Aspects of CAR T-Cell Therapy - WebMD](https://www.webmd.com/cancer/lymphoma/features/navigate-finances-car-t-cell-therapy) - Experts estimate that CAR T-cell therapy can cost between $500,000 and $1,000,000. “CAR [T-cell ther...

4. [Buy-and-Bill Definition | MMIT](https://www.mmitnetwork.com/glossary/buy-and-bill/) - Buy-and-bill: Provider purchases and manages the drug. White-bagging: Specialty pharmacy ships drug ...

5. [Specialty Pharmacy Billing: Medical vs Pharmacy Benefit, Buy-and ...](https://www.careroute.ai/blog/specialty-pharmacy-billing) - Specialty drugs account for 55% of drug spending. Understand medical benefit vs pharmacy benefit bil...

6. [From ASP to WAC: 8 key drug pricing terms life science companies ...](https://www.milliman.com/en/insight/asp-wac-8-key-drug-pricing-terms-life-science) - 1. WAC (Wholesale Acquisition Cost) · 2. AWP (Average Wholesale Price) · 3. ASP (average sales price...

7. [Hospitals are saving lives with CAR-T. Getting paid is another story](https://www.statnews.com/2019/03/12/hospitals-arent-getting-paid-for-car-t/) - Reimbursement issues plague hospitals offering CAR-T therapy, a pricey yet cutting-edge medical proc...

8. [Disparities in Clinical Research and Cancer Treatment | AACR](https://cancerprogressreport.aacr.org/disparities/cdpr26-contents/cdpr26-disparities-in-clinical-research-and-cancer-treatment/) - Understand disparities in cancer treatment and clinical research, including barriers to trial partic...

9. [The role of buy and bill in the specialty pharmacy landscape](https://www.fishbowlinventory.com/blog/buy-and-bill-specialty-pharmacy) - Unlike buy and bill, where providers purchase and store medications, specialty pharmacies handle the...

10. [Advocating for Reimbursement for CAR T Hospitals in the US](https://cartvision.com/case-study/us-advocating-for-adequate-reimbursement-for-hospitals-delivering-car-t-cell-therapy/) - Learn how the US CAR T Working Group successfully engaged Medicare to create a new MS-DRG that suppo...

11. [New CAR-T Policies Affect Access, Reimbursement](https://advisory.avalerehealth.com/insights/new-car-t-policies-affect-access-reimbursement) - For FY 2025, inpatient stays with CAR-T treatment are currently assigned to MS-DRG 018, which has a ...

12. [CAR T-cell Therapy Causes Heavy Financial Losses for Hospitals](https://www.medscape.com/viewarticle/921315) - Hospitals may lose up to $300000 for each CAR T-cell infusion given, but a group of experts offer so...

13. [A Path Forward for CAR-T Therapy Reimbursement Under the IPPS](https://www.americanactionforum.org/research/a-path-forward-for-car-t-therapy-reimbursement-under-the-ipps/) - The process of CAR-T reimbursement is typical of any case under the IPPS but requires a fair bit of ...

14. [CAR T-Cell Therapy Causes Heavy Financial Losses for Hospitals](http://pc3i.upenn.edu/news/car-t-cell-therapy-causes-heavy-financial-losses-for-hospitals/) - It says hospitals may be losing up to $300,000 for each CAR-T treatment they provide. The price of C...

15. [Medicare Part B Drug Average Sales Price - CMS](https://www.cms.gov/medicare/payment/fee-for-service-providers/part-b-drugs/average-drug-sales-price) - Medicare pays most separately payable drugs and biological products at a rate of ASP plus 6%. To cal...

16. [Medicare Monday: What is ASP? - PhRMA](https://phrma.org/blog/medicare-monday-what-is-asp) - Average Sales Price (ASP)+6 percent. ASP is a market-based price that reflects the weighted average ...

17. [Compare your costs with ASP and Medicare allowable](https://www.cancernetwork.com/view/compare-your-costs-asp-and-medicare-allowable) - You need to determine what you are paying for your oncology drugs, as compared to the Average Sales ...

18. [How Hospitals Inflate Specialty Drug Prices: The Latest Medical ...](https://www.drugchannels.net/2015/03/how-hospitals-inflate-specialty-drug.html) - Basically, a hospital marks up a drug to create a stratospheric "charge," then discounts the bogus c...

19. [Charting The Landscape Of Cell Gene Therapy Reimbursement In ...](https://www.cellandgene.com/doc/charting-the-landscape-of-cell-gene-therapy-reimbursement-in-the-u-s-0001) - Medicaid's fixed payment bundling for inpatient and outpatient episodes of care is another example o...

20. [CGT (Cell and Gene Therapy Access) Model - CMS](https://www.cms.gov/priorities/innovation/innovation-models/cgt) - Be enrolled in Medicaid or CHIP (if applicable) in a state participating in the model at time of the...

21. [Cell and Gene Therapy (CGT) Access Model - Mississippi Medicaid](https://medicaid.ms.gov/cell-and-gene-therapy-cgt-access-model/) - The initial focus of the model is on CGTs for sickle cell disease. The Mississippi Division of Medic...

22. [[PDF] CMS Cell & Gene Therapy Access Model – State Participation and ...](https://www.clinigengroup.com/media/3873/cms-cell-and-gene-therapy-access-model.pdf) - The CMS Cell and Gene Therapy (CGT) Access Model is a new Medicaid demonstration program testing out...

23. [Future of Gene Therapy Funding - The Actuary Magazine](https://www.theactuarymagazine.org/future-of-gene-therapy-funding/) - New gene therapies run counter to traditional payment models where costs and benefits are spread ove...

24. [Cell and Gene Therapies: Five Key Access and Reimbursement ...](https://clarivate.com/life-sciences-healthcare/blog/cell-gene-therapies-five-key-access-reimbursement-strategies/) - As of October 2019, Novartis has secured formulary coverage for Zolgensma with four large national p...

25. [Pros and Cons of Various Reimbursement Models for Cell and Gene ...](https://www.cgtlive.com/view/pros-cons-reimbursement-models-cell-gene-therapies) - Based on the arrangement, payers and/or patients can be reimbursed for their share of the costs for ...

26. [Innovative Payment Models: Outcomes‑Based, Annuity & Beyond](https://remapconsulting.com/emerging-developing-markets/pricing-emerging-developing-markets/innovative-payment-models-pharma/) - Manufacturers of high-cost gene therapies are increasingly offering national reimbursement systems a...

27. [Rethinking Policies for the Cost and Value of Cell and Gene Therapies](https://schaeffer.usc.edu/research/cell-gene-therapy-policies/) - Hospitals may negotiate higher reimbursement with private insurers to cover the fully loaded costs o...

28. [Data.Medicaid.gov - CMS Developer](https://developer.cms.gov/data-medicaid/) - Drug pricing and payment. Access data on the National Average Drug Acquisition Cost (NADAC), drug pr...

29. [NADAC (National Average Drug Acquisition Cost) 2024](https://data.medicaid.gov/dataset/99315a95-37ac-4eee-946a-3c523b4c481e) - National Average Drug Acquisition Cost (NADAC) weekly reference data for the calendar year. Data Tab...

30. [340B Drug Pricing Program - HRSA](https://www.hrsa.gov/opa) - Learn about HRSA's Office of Pharmacy Affairs (OPA), ensuring affordable medications through the 340...

31. [Hospital Price Transparency Machine-readable File: An Overview](https://www.rivethealth.com/blog/hospital-price-transparency-machine-readable-file-compliance-overview) - All hospitals are required by US federal regulation to provide a comprehensive, standardized machine...

32. [MRFs in 2025: Key Compliance and Strategic Insights for Providers](https://www.trekhealth.io/resources/what-is-an-enhanced-machine-readable-file-mrf) - An enhanced MRF is a standardized digital file, typically JSON or CSV (Wide or Tall) that hospitals ...

33. [Drug price transparency data FAQ | Turquoise Health Blog](https://turquoise.health/resources/blog/drug-price-transparency-data-faq) - Price transparency data is data mandated by a slew of regulations to be published via machine-readab...

34. [Analysis of Prescription Drug Prices in Hospitals - 3 Axis Advisors](https://www.3axisadvisors.com/projects/2026/3/5/analysis-of-prescription-drug-prices-in-hospitals) - The analysis reveals that hospitals typically report one gross charge and one cash price, but they y...

35. [Agencies Take Action on Healthcare Price Transparency - NFP](https://www.nfp.com/insights/agencies-take-action-on-healthcare-price-transparency/) - As enacted in 2020, the TiC final rule requires plans and insurers to publicly post MRFs with the ne...

36. [Turquoise Health - Price transparency reporting Software](https://intuitionlabs.ai/software/revenue-cycle-analytics-performance/price-transparency-reporting/turquoise-health) - An AI-powered healthcare pricing and contract intelligence platform for price transparency complianc...

37. [Serif Health on the Arcadia Marketplace](https://arcadia.io/marketplace/serif-health) - Serif Health provides validated healthcare price transparency data, helping orgs analyze reimburseme...

38. [Are Hospital Prices a Bigger Problem than Drug Prices? Congress ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC6487976/) - In a long letter to Alexander, AHA argued that drug prices and regulatory requirements had the bigge...

39. [Analyzing Inpatient Hospital Pricing Using Price Transparency Data](https://www.serifhealth.com/blog/analyzing-inpatient-hospital-pricing-using-price-transparency-data) - Commercially negotiated prices can vary dramatically—even in the same market. Some hospitals receive...

40. [[PDF] The 340B Drug Purchasing Program and Commercial Insurance ...](https://www.npcnow.org/sites/default/files/2025-05/340B%20and%20Employer%20Costs%20White%20Paper.pdf) - iv CEs earn profits on the spread between the reimbursed price of each drug and the 340B acquisition...

41. [[PDF] Examining 340B Hospital Price Transparency, Drug Profits, and ...](https://communityoncology.org/wp-content/uploads/2022/09/COA_340B_hospital_transparency_report_2_final.pdf) - 340B hospitals' own self-reported pricing data reveals that they price the top oncology drugs at 4.9...

42. [Examining Hospital Price Transparency, Drug Profits, and the 340B ...](https://mycoa.communityoncology.org/education-publications/studies/examining-hospital-price-transparency-drug-profits-and-the-340b-program-2022) - 340B hospitals' own self-reported pricing data reveals that they price the top oncology drugs at 4.9...

43. [Can MRF data be used for comparative benchmarking? - HFMA](https://www.hfma.org/can-mrf-data-be-used-for-comparative-benchmarking/) - A study identified disparities among machine readable files that limit their usefulness for comparat...

44. [[PDF] The burdens associated with receiving CAR T-cell therapy](https://www.cancersupportcommunity.org/sites/default/files/file/2025-12/CSC_CART_ASH2025.pdf) - next phase of this study will examine patients' experiences receiving therapy at community centers t...

45. [Total Cost of Care: Site-of-Care Shift and 340B Drive Total Cost](https://www.oncologynewscentral.com/article/total-cost-of-care-site-of-care-shift-and-340b-drive-total-cost) - Figure 3 shows a historical trend in Medicare reimbursement and 340B prices for oncology drugs, as w...

46. [Immune-Based Cancer Treatment: Addressing Disparities in Access ...](https://ascopubs.org/doi/10.1200/EDBK_323523) - Health care disparities emerge or widen with the advent of new therapeutic approaches to cancer, suc...

47. [340B Drug Pricing Program: How It Works, Why It's Controversial](https://www.commonwealthfund.org/publications/explainer/2025/aug/340b-drug-pricing-program-how-it-works-and-why-its-controversial) - The 340B program allows these providers, known as covered entities, to buy discounted outpatient pre...

48. [How Hospitals are Raising Drug Prices | Third Way](https://www.thirdway.org/report/how-hospitals-are-raising-drug-prices) - Hospital systems' growth in market power is leading to larger markups for outpatient drugs, where pa...

49. [Financial toxicity and implications for cancer care in the era of ... - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5985271/) - Patients with cancer spend a median of $1,730–$4,727 annually on out-of-pocket treatment-related exp...

50. [Immunotherapy Increases the Cost of Cancer Care but Reduces ...](https://www.nber.org/bh/20261/immunotherapy-increases-cost-cancer-care-reduces-mortality) - They are considered a breakthrough development in cancer care, but are very expensive, with a full c...

51. [Financial Toxicity High for Low-Income Patients in Early-Phase ...](https://jhoponline.com/interview-with-the-innovators?view=article&artid=17872%3Afinancial-toxicity-high-for-low-income-patients-in-early-phase-clinical-trials) - Analysis showed that patients had an average of $2100 monthly out-of-pocket costs to pay for their c...

52. [Socioeconomic disparities in immunotherapy use among advanced ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC10199935/) - Abstract. Socioeconomic and racial disparities exist in access to care among patients with non-small...

53. [Analysis: Hospital Price Transparency Data Lacks Standardization ...](https://www.kff.org/health-costs/analysis-hospital-price-transparency-data-lacks-standardization-limiting-its-use-to-insurers-employers-and-consumers/) - Using payer-negotiated rates from ten U.S. hospitals, the brief finds significant variation in the p...

54. [Limited utility of price transparency data for drugs - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC11953851/) - Since 2021, hospitals have been required to report the prices of common, shoppable services, includi...

55. [Turquoise Health CEO Talks Future of Healthcare Price Transparency](https://www.youtube.com/watch?v=Xwr1ohsN3pk) - ... healthcare services or large-scale market analysis for those without a computer engineering degr...

56. [Drug reimbursement trends report | ZS](https://www.zs.com/insights/zs-turquoise-analysis-variability-specialty-drug-reimbursement) - The findings uncover significant variation in reimbursement rates, varying by payer channel, provide...

57. [Healthcare price transparency resources - Turquoise Health](https://turquoise.health/resources-hub) - Turquoise Health and ZS's 2025 drug reimbursement trends report analyzes millions of hospital and pa...

58. [BuyandBill™ | HCPCS Drug Pricing Search Tool](https://pricing.buyandbill.com) - Office-Administered Drug Pricing. Search ASP, WAC, AWP, and other reimbursement data for HCPCS-coded...

59. [Administration Issues Cross-Agency Guidance Targeting Health ...](https://www.lathropgpm.com/insights/administration-issues-cross-agency-guidance-targeting-health-care-pricing-and-focusing-on-hospitals-and-health-plans/) - This cross-agency effort focuses on hospitals and health plans and takes steps to tighten requiremen...

60. [CMS Provides New Price Transparency Guidance](https://www.centaurihs.com/cms-provides-new-price-transparency-guidance/) - The guidance is brief, it centers around the use of average charges, which are used to calculate the...

