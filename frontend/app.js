const API_BASE = "";

const state = {
  drugs: [],
  selected: new Set(),
  hospitalsById: new Map(),
};

const PAYER_ALIAS_STOPWORDS = new Set(["inc", "llc", "corp", "corporation", "co", "company", "the", "of", "plan", "plans"]);

/** Words allowed to be the *only* difference between a short name and a
 * longer one for a subset-match to count as the same payer (e.g. "Superior"
 * vs "Superior Health"). Brand-distinguishing words (a second company name,
 * a state, a network name) must NOT be in here — otherwise two genuinely
 * different payers that both happen to be a substring of a third compound
 * name (e.g. "AETNA" and "KELSEY" both inside "Aetna-Kelsey Care") get
 * transitively merged into each other through that compound name. */
const PAYER_GENERIC_DESCRIPTORS = new Set([
  "health",
  "care",
  "network",
  "networks",
  "managed",
  "group",
  "insurance",
  "ppo",
  "hmo",
  "pos",
  "epo",
  "choice",
  "advantage",
  "preferred",
  "system",
  "systems",
]);

function tokenizePayerName(name) {
  let s = (name || "").toLowerCase();
  s = s.replace(/[.,\-&/]/g, " ");
  s = s.replace(/\bhealth\s*care\b/g, "health");
  s = s.replace(/\bhealthcare\b/g, "health");
  s = s.replace(/\bmed\b/g, "medical");
  s = s.replace(/\bmgmt\b/g, "management");
  s = s.replace(/\bins\b/g, "insurance");
  return s.split(/\s+/).filter((t) => t && !PAYER_ALIAS_STOPWORDS.has(t));
}

/** Alphanumeric-only key with no spaces, so "Unitedhealthcare" (one word) and
 * "United Health Care" (three words) collapse to the same string — the
 * token-level check above can't catch this since there's no word boundary
 * inside a concatenated name. */
function compactPayerKey(name) {
  let s = (name || "").toLowerCase();
  s = s.replace(/health\s*care/g, "health");
  s = s.replace(/[^a-z0-9]/g, "");
  return s;
}

/** Clusters raw payer names that are likely the same payer (case/whitespace
 * variants, "health"/"healthcare" spelling, or one name being an abbreviated
 * subset of another, e.g. "United" vs "United Healthcare"). Returns a Map of
 * trimmed raw name -> canonical display label (the most frequent/descriptive
 * variant seen). */
function buildPayerCanonicalMap(rawNames) {
  const groups = new Map(); // sorted-token-key -> { tokens: Set, compactKeys: Set, labels: Map<label, count> }
  for (const raw of rawNames) {
    const trimmed = (raw || "").trim();
    if (!trimmed) continue;
    const tokens = tokenizePayerName(trimmed);
    if (tokens.length === 0) continue;
    const key = [...tokens].sort().join(" ");
    if (!groups.has(key)) groups.set(key, { tokens: new Set(tokens), compactKeys: new Set(), labels: new Map() });
    const group = groups.get(key);
    group.compactKeys.add(compactPayerKey(trimmed));
    group.labels.set(trimmed, (group.labels.get(trimmed) || 0) + 1);
  }

  const keys = [...groups.keys()].sort((a, b) => groups.get(b).tokens.size - groups.get(a).tokens.size);
  const parent = new Map(keys.map((k) => [k, k]));
  function find(k) {
    while (parent.get(k) !== k) k = parent.get(k);
    return k;
  }
  function compactKeysMatch(setA, setB) {
    for (const ca of setA) {
      for (const cb of setB) {
        if (ca === cb) return true;
        const [shorter, longer] = ca.length <= cb.length ? [ca, cb] : [cb, ca];
        if (shorter.length < 4 || !longer.startsWith(shorter)) continue;
        // Same transitivity risk as the token check: only trust a prefix
        // match if what's left over is a generic descriptor, not another
        // brand's name concatenated on (e.g. "aetna" is a prefix of
        // "aetnakelseycare", but "kelseycare" isn't generic — that's a
        // second, different company, not a suffix on Aetna's name).
        const suffix = longer.slice(shorter.length);
        if (PAYER_GENERIC_DESCRIPTORS.has(suffix)) return true;
      }
    }
    return false;
  }
  for (let i = 0; i < keys.length; i++) {
    for (let j = i + 1; j < keys.length; j++) {
      const a = keys[i];
      const b = keys[j];
      const ta = groups.get(a).tokens;
      const tb = groups.get(b).tokens;
      const [smaller, larger] = ta.size <= tb.size ? [ta, tb] : [tb, ta];
      let isSubset = smaller.size > 0;
      for (const token of smaller) {
        if (!larger.has(token)) {
          isSubset = false;
          break;
        }
      }
      if (isSubset) {
        // The extra words the larger name has on top of the smaller one must
        // all be generic descriptors — otherwise this is two different
        // brands that happen to share a compound name (e.g. "AETNA" and
        // "KELSEY" both sitting inside "Aetna-Kelsey Care").
        for (const token of larger) {
          if (!smaller.has(token) && !PAYER_GENERIC_DESCRIPTORS.has(token)) {
            isSubset = false;
            break;
          }
        }
      }
      const isCompactMatch = compactKeysMatch(groups.get(a).compactKeys, groups.get(b).compactKeys);
      if (isSubset || isCompactMatch) {
        const ra = find(a);
        const rb = find(b);
        if (ra !== rb) {
          const bigger = groups.get(ra).tokens.size >= groups.get(rb).tokens.size ? ra : rb;
          const smallerRoot = bigger === ra ? rb : ra;
          parent.set(smallerRoot, bigger);
        }
      }
    }
  }

  const finalGroups = new Map(); // root -> Map<label, count>
  for (const key of keys) {
    const root = find(key);
    if (!finalGroups.has(root)) finalGroups.set(root, new Map());
    const labels = finalGroups.get(root);
    for (const [label, count] of groups.get(key).labels) {
      labels.set(label, (labels.get(label) || 0) + count);
    }
  }

  const rawToCanonical = new Map();
  for (const labels of finalGroups.values()) {
    let bestLabel = null;
    let bestScore = -1;
    for (const [label, count] of labels) {
      const score = count * 1000 + label.length;
      if (score > bestScore) {
        bestScore = score;
        bestLabel = label;
      }
    }
    for (const label of labels.keys()) rawToCanonical.set(label, bestLabel);
  }
  return rawToCanonical;
}

function canonicalPayerLabel(name, canonicalMap) {
  const trimmed = (name || "").trim();
  return canonicalMap.get(trimmed) || trimmed;
}

const payerPageState = {
  selectedDrugs: new Set(),
  selectedPayers: new Set(),
  allBreakdowns: [],
  payerCanonicalMap: new Map(),
};

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else node.setAttribute(k, v);
  }
  for (const child of children) {
    if (child === null || child === undefined) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

async function fetchDrugs() {
  const res = await fetch(`${API_BASE}/api/drugs`);
  if (!res.ok) throw new Error(`GET /api/drugs failed: ${res.status}`);
  const data = await res.json();
  return data.drugs;
}

async function fetchHospitals() {
  const res = await fetch(`${API_BASE}/api/hospitals`);
  if (!res.ok) throw new Error(`GET /api/hospitals failed: ${res.status}`);
  const data = await res.json();
  return data.hospitals;
}

async function fetchBreakdowns(codes) {
  const res = await fetch(`${API_BASE}/api/breakdowns?drugs=${encodeURIComponent(codes.join(","))}`);
  if (!res.ok) throw new Error(`GET /api/breakdowns failed: ${res.status}`);
  return res.json();
}

function renderDrugCategories(drugs) {
  const container = document.getElementById("drug-categories");
  container.innerHTML = "";

  const byCategory = new Map();
  for (const drug of drugs) {
    if (!byCategory.has(drug.category)) byCategory.set(drug.category, []);
    byCategory.get(drug.category).push(drug);
  }

  for (const [category, categoryDrugs] of [...byCategory.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    const card = el("div", { class: "category" }, el("h3", {}, category));
    for (const drug of categoryDrugs.sort((a, b) => a.name.localeCompare(b.name))) {
      const checkboxId = `drug-${drug.code}`;
      const checkbox = el("input", { type: "checkbox", id: checkboxId, "data-code": drug.code });
      checkbox.addEventListener("change", onSelectionChange);
      const row = el(
        "div",
        { class: "drug-row" },
        checkbox,
        el("label", { for: checkboxId }, drug.name)
      );
      card.append(row);
    }
    container.append(card);
  }
}

function onSelectionChange(event) {
  const code = event.target.dataset.code;
  if (event.target.checked) state.selected.add(code);
  else state.selected.delete(code);

  const rosterSection = document.getElementById("roster-section");

  if (state.selected.size === 0) {
    rosterSection.hidden = true;
    return;
  }

  rosterSection.hidden = false;
  loadBreakdowns();
}

function enrollmentEvidence(hospitalId) {
  const hospital = state.hospitalsById.get(hospitalId);
  if (!hospital || !hospital.enrollment_340b_checks || hospital.enrollment_340b_checks.length === 0) return null;
  return hospital.enrollment_340b_checks
    .map((c) => {
      const parts = [`${c.method || "check"}: ${c.result}`];
      if (c.matched_entity_name) parts.push(`matched "${c.matched_entity_name}"`);
      if (typeof c.match_score === "number") parts.push(`score ${c.match_score}`);
      if (c.medicare_provider_number) parts.push(`CCN ${c.medicare_provider_number}`);
      return parts.join(", ");
    })
    .join("\n");
}

function badgeForEnrollment(status, hospitalId) {
  const cls = status === "enrolled" ? "enrolled" : status === "not_enrolled" ? "not-enrolled" : "unverified";
  const label = status === "enrolled" ? "340B enrolled" : status === "not_enrolled" ? "not 340B enrolled" : "340B unverified";
  const attrs = { class: `badge ${cls}` };
  const evidence = hospitalId ? enrollmentEvidence(hospitalId) : null;
  if (evidence) attrs.title = evidence;
  return el("span", attrs, label);
}

function badgeForIngestion(status) {
  const raw = status || "not_ingested";
  const isFailure = raw.startsWith("failed");
  const cls = raw === "success" ? "enrolled" : isFailure ? "not-enrolled" : "unverified";
  const label = isFailure ? "failed" : raw;
  const attrs = { class: `badge ${cls}` };
  if (isFailure) attrs.title = raw;
  return el("span", attrs, label);
}

function renderStatsBar(hospitals) {
  const bar = document.getElementById("stats-bar");
  bar.innerHTML = "";
  const total = hospitals.length;
  const ingested = hospitals.filter((h) => h.ingestion_status === "success").length;
  const enrolled = hospitals.filter((h) => h.enrollment_340b === "enrolled").length;
  const stats = [
    [total, "hospitals in scope"],
    [ingested, "successfully ingested"],
    [enrolled, "confirmed 340B enrolled"],
  ];
  for (const [value, label] of stats) {
    bar.append(el("div", { class: "stat" }, el("div", { class: "stat-value" }, String(value)), el("div", { class: "stat-label" }, label)));
  }
}

function renderRoster(breakdowns, unavailableHospitals) {
  const rosterList = document.getElementById("roster-list");
  const unavailableList = document.getElementById("unavailable-list");
  rosterList.innerHTML = "";
  unavailableList.innerHTML = "";

  const hospitalIds = [...new Set(breakdowns.map((b) => b.hospital_id))];
  if (hospitalIds.length === 0) {
    rosterList.append(el("p", { class: "empty-state" }, "No hospitals publish a charge for the selected drugs."));
  }
  for (const hospitalId of hospitalIds) {
    const match = breakdowns.find((b) => b.hospital_id === hospitalId);
    const hospitalBreakdowns = breakdowns.filter((b) => b.hospital_id === hospitalId);

    const detail = el("div", { class: "hospital-detail", hidden: "" });
    for (const breakdown of hospitalBreakdowns) {
      detail.append(renderBreakdownCard(breakdown));
    }

    const chevron = el("span", { class: "chevron" }, "›");
    const header = el(
      "div",
      { class: "hospital-card-header" },
      el("div", { class: "name" }, match.hospital_name),
      badgeForEnrollment(match.enrollment_340b, match.hospital_id),
      chevron
    );
    header.addEventListener("click", () => {
      const isOpen = !detail.hidden;
      detail.hidden = isOpen;
      header.parentElement.classList.toggle("expanded", !isOpen);
    });

    rosterList.append(el("div", { class: "hospital-card expandable" }, header, detail));
  }

  if (unavailableHospitals.length > 0) {
    unavailableList.append(el("h3", {}, "Unavailable"));
    for (const hospital of unavailableHospitals) {
      unavailableList.append(
        el(
          "div",
          { class: "hospital-card" },
          el("div", { class: "name" }, hospital.name),
          el("div", { class: "meta" }, hospital.ingestion_status || "not yet ingested")
        )
      );
    }
  }
}

function sourceSpan(text) {
  if (!text) return el("span", { class: "field-source" });
  if (/^https?:\/\//.test(text)) {
    return el("a", { class: "field-source source-link", href: text, title: text, target: "_blank", rel: "noopener" }, "source ↗");
  }
  return el("span", { class: "field-source", title: text }, `source: ${text}`);
}

function renderPriceField(field, label) {
  if (field.available === false) {
    return el(
      "tr",
      {},
      el("td", {}, label),
      el("td", {}, fieldUnavailable(field))
    );
  }
  const valueText = typeof field.value === "number" ? `$${field.value.toFixed(2)}` : String(field.value);
  const cell = el("td", {}, valueText);
  if (field.formula) cell.append(el("span", { class: "formula" }, `formula: ${field.formula}`));
  if (field.source) {
    const src = field.source.source || field.source;
    cell.append(sourceSpan(src));
  }
  return el("tr", {}, el("td", {}, label), cell);
}

function renderGrossCharge(field) {
  if (field.available === false) {
    return el(
      "tr",
      {},
      el("td", {}, "Gross charge"),
      el("td", {}, fieldUnavailable(field))
    );
  }
  const cell = el("td", {}, `$${field.min?.toFixed(2) ?? "?"} – $${field.max?.toFixed(2) ?? "?"}`);
  cell.append(sourceSpan(field.source.source));
  return el("tr", {}, el("td", {}, "Gross charge"), cell);
}

function renderDose(dose) {
  const ref = dose.reference_dose;
  const cell = ref.available === false
    ? fieldUnavailable(ref)
    : el("span", {}, `${ref.value} (${dose.dose_pattern})`);
  const wrap = el("td", {}, cell);
  if (ref.formula) wrap.append(el("span", { class: "formula" }, `formula: ${ref.formula}`));
  if (dose.dose_regimen_cited) wrap.append(el("span", { class: "field-source", title: dose.dose_regimen_cited }, dose.dose_regimen_cited));
  return el("tr", {}, el("td", {}, "Reference dose"), wrap);
}

let payerFilterCounter = 0;

function renderPayerTable(payerRates, unverifiedExclusions, referenceDose) {
  const verifiedRates = payerRates.filter((row) => row.verified);
  if (verifiedRates.length === 0) {
    return el("p", { class: "empty-state" }, "No payer rates published for this drug at this hospital.");
  }
  const isPerDoseUnit = referenceDose && referenceDose.unit === "dose";
  const hasDoseScale = !isPerDoseUnit && referenceDose && referenceDose.available !== false;

  const canonicalMap = buildPayerCanonicalMap(verifiedRates.map((row) => row.payer_name));
  const payerLabels = [...new Set(verifiedRates.map((row) => canonicalPayerLabel(row.payer_name, canonicalMap)))].sort(
    (a, b) => a.localeCompare(b)
  );
  const selected = new Set();
  const checkboxes = [];

  const headerCells = [
    el("th", {}, "Payer"),
    el("th", {}, "Plan"),
    el("th", {}, "Setting"),
    el("th", {}, isPerDoseUnit ? "Rate (/dose)" : "Rate (/mg)"),
  ];
  if (hasDoseScale) headerCells.push(el("th", {}, "Rate (/dose)"));
  headerCells.push(el("th", {}, "Markup ratio"));

  const tableBody = el("tbody", {});
  const table = el("table", { class: "payer-table" }, el("thead", {}, el("tr", {}, ...headerCells)), tableBody);
  const countLabel = el("p", { class: "lede" }, "");

  function renderRows() {
    tableBody.innerHTML = "";
    let shown = 0;
    for (const row of verifiedRates) {
      if (!selected.has(canonicalPayerLabel(row.payer_name, canonicalMap))) continue;
      shown += 1;
      const ratioCell = row.markup_ratio.available === false
        ? el("span", { class: "field-value unavailable" }, row.markup_ratio.reason)
        : el("span", { class: row.markup_ratio_flag ? "field-value flagged" : "field-value" }, `${row.markup_ratio.value}x${row.markup_ratio_flag ? " ⚑" : ""}`);
      const cells = [
        el("td", {}, row.payer_name),
        el("td", {}, row.plan_name || "—"),
        el("td", {}, row.billing_setting || "—"),
        el("td", {}, `$${row.rate.value.toFixed(2)}`),
      ];
      if (hasDoseScale) cells.push(el("td", {}, `$${(row.rate.value * referenceDose.value).toFixed(2)}`));
      cells.push(el("td", {}, ratioCell));
      tableBody.append(el("tr", {}, ...cells));
    }
    countLabel.textContent = shown === verifiedRates.length
      ? `All ${verifiedRates.length} payer-specific negotiated rate(s) verified against the hospital's raw MRF.`
      : `Showing ${shown} of ${verifiedRates.length} verified payer-specific negotiated rate(s).`;
  }

  const checkboxGrid = el("div", { class: "payer-filter-grid" });
  for (const label of payerLabels) {
    const checkboxId = `payer-filter-${++payerFilterCounter}`;
    const checkbox = el("input", { type: "checkbox", id: checkboxId });
    checkbox.checked = false;
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) selected.add(label);
      else selected.delete(label);
      renderRows();
    });
    checkboxes.push(checkbox);
    checkboxGrid.append(el("label", { class: "payer-filter-item", for: checkboxId }, checkbox, el("span", {}, label)));
  }

  const selectAllBtn = el("button", { type: "button", class: "payer-filter-btn" }, "Select all");
  selectAllBtn.addEventListener("click", () => {
    checkboxes.forEach((checkbox) => (checkbox.checked = true));
    payerLabels.forEach((label) => selected.add(label));
    renderRows();
  });
  const clearAllBtn = el("button", { type: "button", class: "payer-filter-btn" }, "Clear all");
  clearAllBtn.addEventListener("click", () => {
    checkboxes.forEach((checkbox) => (checkbox.checked = false));
    selected.clear();
    renderRows();
  });

  const filterPanel = el(
    "div",
    { class: "payer-filter-panel" },
    el(
      "div",
      { class: "payer-filter-header" },
      el("div", { class: "payer-filter-title" }, "Filter by payer"),
      el("div", { class: "payer-filter-actions" }, selectAllBtn, clearAllBtn)
    ),
    checkboxGrid
  );

  renderRows();

  const wrap = el("div", { class: "payer-table-wrap" }, filterPanel, countLabel, table);
  if (unverifiedExclusions.length > 0) {
    wrap.append(
      el(
        "div",
        { class: "exclusion-note" },
        `${unverifiedExclusions.length} payer row(s) excluded from verified totals: could not be independently confirmed against the hospital's raw MRF.`
      )
    );
  }
  return wrap;
}

function fmtMoney(value) {
  return typeof value === "number" ? `$${value.toFixed(2)}` : String(value);
}

function fieldUnavailable(field) {
  return el("span", { class: "field-value unavailable", title: field.reason }, field.reason);
}

function statCard(label, field, opts) {
  opts = opts || {};
  const body = [];
  if (!field || field.available === false) {
    body.push(fieldUnavailable(field || { reason: "not available" }));
  } else if ("min" in field && "max" in field) {
    body.push(el("div", { class: "stat-value" }, `${fmtMoney(field.min)} – ${fmtMoney(field.max)}`));
  } else {
    body.push(el("div", { class: "stat-value" }, fmtMoney(field.value)));
  }
  if (opts.sub) body.push(el("div", { class: "stat-sub" }, opts.sub));
  return el("div", { class: "stat-tile" }, el("div", { class: "stat-tile-label" }, label), ...body);
}

function statCardText(label, text, sub) {
  const body = [el("div", { class: "stat-value" }, text)];
  if (sub) body.push(el("div", { class: "stat-sub" }, sub));
  return el("div", { class: "stat-tile" }, el("div", { class: "stat-tile-label" }, label), ...body);
}

function firstAvailableSetting(chargeRange) {
  if (!chargeRange || chargeRange.available === false) return null;
  if (chargeRange.outpatient) return ["outpatient", chargeRange.outpatient];
  const entries = Object.entries(chargeRange);
  return entries.length ? entries[0] : null;
}

function renderStatCards(breakdown) {
  const grid = el("div", { class: "stat-grid" });

  const settingDose = breakdown.per_dose ? firstAvailableSetting(breakdown.per_dose.hospital_charge_range) : null;
  grid.append(
    statCard(
      settingDose ? `Hospital charge range (${settingDose[0]}, /dose)` : "Hospital charge range (/dose)",
      settingDose ? settingDose[1] : { available: false, reason: "dose value not available" }
    )
  );
  grid.append(statCard("Medicare ASP payment limit (/dose)", breakdown.per_dose && breakdown.per_dose.asp));
  grid.append(statCard("List/WAC benchmark (/dose)", breakdown.per_dose && breakdown.per_dose.wac));
  const coinsurance = breakdown.medicare_coinsurance_split;
  if (coinsurance && coinsurance.available !== false) {
    grid.append(statCardText("Medicare coinsurance", `${coinsurance.coinsurance_pct}%`, "of ASP + 6% reimbursement"));
  } else {
    grid.append(statCard("Medicare coinsurance", { available: false, reason: coinsurance ? coinsurance.reason : "not available" }));
  }

  return grid;
}

function renderUnitNote(breakdown) {
  const parts = [];
  if (breakdown.billing_unit_dosage) {
    parts.push(`Hospital and CMS rates are published per billing unit (${breakdown.billing_unit_dosage}).`);
  }
  const ref = breakdown.dose.reference_dose;
  if (ref.available !== false) {
    parts.push(`A complete reference dose is ${ref.value} ${ref.unit || "mg"} (${breakdown.dose.dose_pattern}), so "/dose" figures below are calculated as billing-unit rate × ${ref.value}.`);
  }
  if (parts.length === 0) return null;
  return el("p", { class: "unit-note" }, parts.join(" "));
}

function renderLayersTable(breakdown) {
  const perDoseUnit = breakdown.dose.reference_dose.unit === "dose";
  const colCount = perDoseUnit ? 2 : 3;
  const table = el(
    "table",
    { class: perDoseUnit ? "layers-table layers-table--dose-only" : "layers-table" },
    perDoseUnit
      ? el("tr", {}, el("th", {}, "Layer"), el("th", {}, "/dose"), el("th", {}, "Source"))
      : el("tr", {}, el("th", {}, "Layer"), el("th", {}, "/mg"), el("th", {}, "/dose"), el("th", {}, "Source"))
  );

  function row(label, mgField, doseField) {
    const mgCell = mgField.available === false ? fieldUnavailable(mgField) : el("span", {}, fmtMoney(mgField.value ?? `${fmtMoney(mgField.min)} – ${fmtMoney(mgField.max)}`));
    const doseCell = !doseField || doseField.available === false
      ? fieldUnavailable(doseField || { reason: "dose value not available" })
      : el("span", {}, "min" in doseField ? `${fmtMoney(doseField.min)} – ${fmtMoney(doseField.max)}` : fmtMoney(doseField.value));
    const src = mgField.source ? (mgField.source.source || mgField.source) : null;
    const cells = perDoseUnit
      ? [el("td", {}, label), el("td", {}, doseCell), el("td", {}, src ? sourceSpan(src) : "—")]
      : [el("td", {}, label), el("td", {}, mgCell), el("td", {}, doseCell), el("td", {}, src ? sourceSpan(src) : "—")];
    table.append(el("tr", {}, ...cells));
  }

  const chargeRange = breakdown.hospital_charge_range;
  if (chargeRange && chargeRange.available === false) {
    table.append(
      el("tr", {}, el("td", {}, "Hospital MRF charge"), el("td", { colspan: String(colCount) }, fieldUnavailable(chargeRange)))
    );
  } else if (chargeRange) {
    for (const [setting, bucket] of Object.entries(chargeRange)) {
      const doseRange = breakdown.per_dose && breakdown.per_dose.hospital_charge_range;
      const doseBucket = doseRange && doseRange.available !== false ? doseRange[setting] : null;
      row(`Hospital MRF charge (${setting})`, bucket, doseBucket);
    }
  }

  row("CMS ASP", breakdown.asp, breakdown.per_dose && breakdown.per_dose.asp);
  row("WAC / List", breakdown.wac, breakdown.per_dose && breakdown.per_dose.wac);
  row("ASP + 6% (Medicare Part B)", breakdown.asp_plus6_line, breakdown.per_dose && breakdown.per_dose.asp_plus6_line);
  if (breakdown.asp_minus27_line) {
    row("ASP − 27% (340B ceiling est.)", breakdown.asp_minus27_line, breakdown.per_dose && breakdown.per_dose.asp_minus27_line);
  }

  const coinsurance = breakdown.medicare_coinsurance_split;
  if (coinsurance) {
    if (coinsurance.available === false) {
      table.append(el("tr", {}, el("td", {}, "Medicare coinsurance split"), el("td", { colspan: String(colCount) }, fieldUnavailable(coinsurance))));
    } else {
      const doseCoinsurance = breakdown.per_dose && breakdown.per_dose.medicare_coinsurance_split;
      row("Medicare share of reimbursement", coinsurance.medicare_share, doseCoinsurance && doseCoinsurance.medicare_share);
      row("Patient coinsurance share", coinsurance.patient_share, doseCoinsurance && doseCoinsurance.patient_share);
    }
  }

  return table;
}

function marginScenarioRow(label, scenario, unit) {
  if (!scenario || scenario.available === false) {
    return el("div", { class: "verdict-line" }, el("span", {}, label), fieldUnavailable(scenario || { reason: "not available" }));
  }
  const positive = scenario.profit >= 0;
  const payer = scenario.payer_name ? ` (${scenario.payer_name}${scenario.plan_name ? " — " + scenario.plan_name : ""})` : "";
  return el(
    "div",
    { class: "verdict-line" },
    el("span", {}, `${label}${payer}`),
    el("span", { class: positive ? "verdict-amount positive" : "verdict-amount negative" }, `${positive ? "+" : "-"}${fmtMoney(Math.abs(scenario.profit))}/${unit}`)
  );
}

function renderWacMarginBox(breakdown) {
  const doseVerdict = breakdown.per_dose && breakdown.per_dose.margin_verdict;
  const scenario = doseVerdict && doseVerdict.medicare_vs_wac;
  return el(
    "div",
    { class: "verdict-box" },
    el("h4", {}, "Margin vs. WAC acquisition cost (Medicare Part B)"),
    marginScenarioRow("Medicare buy-and-bill (ASP+6% vs. WAC)", scenario, "dose")
  );
}

function renderMarginVerdict(breakdown) {
  const verdict = breakdown.per_dose && breakdown.per_dose.margin_verdict;
  if (!verdict || !verdict.medicare_buy_and_bill) {
    return null;
  }
  return el(
    "div",
    { class: "verdict-box" },
    el("h4", {}, "Margin vs. estimated 340B acquisition cost (ASP − 27%)"),
    marginScenarioRow("Medicare buy-and-bill", verdict.medicare_buy_and_bill, "dose"),
    marginScenarioRow("Highest verified commercial rate", verdict.highest_commercial, "dose"),
    marginScenarioRow("Lowest verified Medicare-managed rate", verdict.lowest_medicare_managed, "dose")
  );
}


function renderBreakdownCard(breakdown, options = {}) {
  const ref = breakdown.dose.reference_dose;
  const scaleBadge = ref.available === false
    ? el("span", { class: "badge unverified" }, "dose scale unavailable")
    : ref.unit === "dose"
      ? el("span", { class: "badge enrolled" }, "1 dose")
      : el("span", { class: "badge enrolled" }, `${ref.value} ${ref.unit || "mg"} = 1 dose`);

  const doseDisclaimer = el(
    "span",
    { class: "dose-disclaimer" },
    "⚠ Heads up: this dose is a typical average, not yours — actual dosing depends on the patient's weight and what the doctor prescribes."
  );

  const header = el(
    "div",
    { class: "breakdown-header" },
    el("div", { class: "kicker" }, breakdown.drug_code),
    el("h3", {}, breakdown.hospital_description ? `${breakdown.drug_name} · ${breakdown.hospital_description}` : breakdown.drug_name),
    el(
      "div",
      { class: "subtitle" },
      badgeForEnrollment(breakdown.enrollment_340b, breakdown.hospital_id),
      scaleBadge,
      doseDisclaimer
    )
  );

  const unitNote = renderUnitNote(breakdown);
  const wacVerdict = renderWacMarginBox(breakdown);
  const verdict = renderMarginVerdict(breakdown);

  const card = el(
    "div",
    { class: "breakdown-card" },
    header,
    renderStatCards(breakdown)
  );
  if (unitNote) card.append(unitNote);
  card.append(el("h4", {}, "Pricing layers"));
  card.append(renderLayersTable(breakdown));
  if (wacVerdict) card.append(wacVerdict);
  if (verdict) card.append(verdict);
  if (options.gatePayerTable) {
    const toggleId = `payer-gate-${++payerFilterCounter}`;
    const toggle = el("input", { type: "checkbox", id: toggleId });
    const gatedSection = el(
      "div",
      { class: "payer-gate-section", hidden: "" },
      el("h4", {}, "All payer-specific negotiated rates"),
      renderPayerTable(breakdown.payer_rates, breakdown.unverified_exclusions, breakdown.dose.reference_dose)
    );
    toggle.addEventListener("change", () => {
      gatedSection.hidden = !toggle.checked;
    });
    card.append(
      el(
        "label",
        { class: "payer-gate-toggle", for: toggleId },
        toggle,
        el("span", {}, "Show other payers for this drug at this hospital")
      ),
      gatedSection
    );
  } else {
    card.append(el("h4", {}, "All payer-specific negotiated rates"));
    card.append(renderPayerTable(breakdown.payer_rates, breakdown.unverified_exclusions, breakdown.dose.reference_dose));
  }

  return card;
}

function renderPayerDrugCategories(drugs) {
  const container = document.getElementById("payer-drug-categories");
  container.innerHTML = "";

  const byCategory = new Map();
  for (const drug of drugs) {
    if (!byCategory.has(drug.category)) byCategory.set(drug.category, []);
    byCategory.get(drug.category).push(drug);
  }

  for (const [category, categoryDrugs] of [...byCategory.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    const card = el("div", { class: "category" }, el("h3", {}, category));
    for (const drug of categoryDrugs.sort((a, b) => a.name.localeCompare(b.name))) {
      const checkboxId = `payer-page-drug-${drug.code}`;
      const checkbox = el("input", { type: "checkbox", id: checkboxId, "data-code": drug.code });
      checkbox.addEventListener("change", onPayerPageDrugChange);
      card.append(el("div", { class: "drug-row" }, checkbox, el("label", { for: checkboxId }, drug.name)));
    }
    container.append(card);
  }
}

function onPayerPageDrugChange(event) {
  const code = event.target.dataset.code;
  if (event.target.checked) payerPageState.selectedDrugs.add(code);
  else payerPageState.selectedDrugs.delete(code);
  renderPayerPageResults();
}

function applyPayerDrugFilter(query) {
  const q = query.trim().toLowerCase();
  const container = document.getElementById("payer-drug-categories");
  for (const card of container.querySelectorAll(".category")) {
    let anyVisible = false;
    const categoryMatches = card.querySelector("h3").textContent.toLowerCase().includes(q);
    for (const row of card.querySelectorAll(".drug-row")) {
      const label = row.querySelector("label").textContent.toLowerCase();
      const visible = q === "" || categoryMatches || label.includes(q);
      row.style.display = visible ? "" : "none";
      if (visible) anyVisible = true;
    }
    card.style.display = anyVisible ? "" : "none";
  }
}

async function loadPayerPageData() {
  const codes = state.drugs.map((d) => d.code);
  const grid = document.getElementById("payer-page-payer-grid");
  if (codes.length === 0) {
    grid.innerHTML = "";
    grid.append(el("p", { class: "empty-state" }, "No drugs on file."));
    return;
  }
  try {
    const { breakdowns } = await fetchBreakdowns(codes);
    payerPageState.allBreakdowns = breakdowns;

    const verifiedRows = [];
    for (const breakdown of breakdowns) {
      for (const row of breakdown.payer_rates) {
        if (row.verified) verifiedRows.push(row);
      }
    }
    payerPageState.payerCanonicalMap = buildPayerCanonicalMap(verifiedRows.map((row) => row.payer_name));
    const payerLabels = [...new Set(verifiedRows.map((row) => canonicalPayerLabel(row.payer_name, payerPageState.payerCanonicalMap)))].sort(
      (a, b) => a.localeCompare(b)
    );
    renderPayerPagePayerCheckboxes(payerLabels);
  } catch (err) {
    grid.innerHTML = "";
    grid.append(el("p", { class: "empty-state" }, `Error loading payers: ${err.message}`));
  }
}

function renderPayerPagePayerCheckboxes(payerLabels) {
  const grid = document.getElementById("payer-page-payer-grid");
  grid.innerHTML = "";
  if (payerLabels.length === 0) {
    grid.append(el("p", { class: "empty-state" }, "No verified payer rates on file."));
    return;
  }

  const checkboxes = [];
  for (const label of payerLabels) {
    const checkboxId = `payer-page-payer-${++payerFilterCounter}`;
    const checkbox = el("input", { type: "checkbox", id: checkboxId });
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) payerPageState.selectedPayers.add(label);
      else payerPageState.selectedPayers.delete(label);
      renderPayerPageResults();
    });
    checkboxes.push(checkbox);
    grid.append(el("label", { class: "payer-filter-item", for: checkboxId }, checkbox, el("span", {}, label)));
  }

  document.getElementById("payer-page-select-all").onclick = () => {
    checkboxes.forEach((checkbox) => (checkbox.checked = true));
    payerLabels.forEach((label) => payerPageState.selectedPayers.add(label));
    renderPayerPageResults();
  };
  document.getElementById("payer-page-clear-all").onclick = () => {
    checkboxes.forEach((checkbox) => (checkbox.checked = false));
    payerPageState.selectedPayers.clear();
    renderPayerPageResults();
  };
}

function renderPayerPageResults() {
  const section = document.getElementById("payer-results-section");
  const list = document.getElementById("payer-roster-list");
  list.innerHTML = "";

  if (payerPageState.selectedDrugs.size === 0 || payerPageState.selectedPayers.size === 0) {
    section.hidden = true;
    return;
  }
  section.hidden = false;

  const matches = payerPageState.allBreakdowns.filter(
    (breakdown) =>
      payerPageState.selectedDrugs.has(breakdown.drug_code) &&
      breakdown.payer_rates.some(
        (row) => row.verified && payerPageState.selectedPayers.has(canonicalPayerLabel(row.payer_name, payerPageState.payerCanonicalMap))
      )
  );

  const hospitalIds = [...new Set(matches.map((b) => b.hospital_id))];
  if (hospitalIds.length === 0) {
    list.append(
      el("p", { class: "empty-state" }, "No hospital publishes a verified rate for the selected drug(s) and payer(s).")
    );
    return;
  }

  for (const hospitalId of hospitalIds) {
    const hospitalBreakdowns = matches.filter((b) => b.hospital_id === hospitalId);
    const first = hospitalBreakdowns[0];

    const detail = el("div", { class: "hospital-detail", hidden: "" });
    for (const breakdown of hospitalBreakdowns) detail.append(renderBreakdownCard(breakdown, { gatePayerTable: true }));

    const chevron = el("span", { class: "chevron" }, "›");
    const header = el(
      "div",
      { class: "hospital-card-header" },
      el("div", { class: "name" }, first.hospital_name),
      badgeForEnrollment(first.enrollment_340b, first.hospital_id),
      chevron
    );
    header.addEventListener("click", () => {
      const isOpen = !detail.hidden;
      detail.hidden = isOpen;
      header.parentElement.classList.toggle("expanded", !isOpen);
    });
    list.append(el("div", { class: "hospital-card expandable" }, header, detail));
  }
}

function initPayerPage() {
  document.getElementById("payer-drug-search").addEventListener("input", (e) => applyPayerDrugFilter(e.target.value));
}

async function loadBreakdowns() {
  const codes = [...state.selected];
  try {
    const { breakdowns, unavailable_hospitals } = await fetchBreakdowns(codes);
    renderRoster(breakdowns, unavailable_hospitals);
  } catch (err) {
    document.getElementById("roster-list").innerHTML = "";
    document.getElementById("roster-list").append(el("p", { class: "empty-state" }, `Error: ${err.message}`));
  }
}

function applyDrugFilter(query) {
  const q = query.trim().toLowerCase();
  const container = document.getElementById("drug-categories");
  for (const card of container.querySelectorAll(".category")) {
    let anyVisible = false;
    const categoryMatches = card.querySelector("h3").textContent.toLowerCase().includes(q);
    for (const row of card.querySelectorAll(".drug-row")) {
      const label = row.querySelector("label").textContent.toLowerCase();
      const visible = q === "" || categoryMatches || label.includes(q);
      row.style.display = visible ? "" : "none";
      if (visible) anyVisible = true;
    }
    card.style.display = anyVisible ? "" : "none";
  }
}

async function init() {
  try {
    const hospitals = await fetchHospitals();
    state.hospitalsById = new Map(hospitals.map((h) => [h.id, h]));
    renderStatsBar(hospitals);
  } catch (err) {
    console.error("Error loading hospitals:", err.message);
  }

  try {
    state.drugs = await fetchDrugs();
    renderDrugCategories(state.drugs);
    document.getElementById("drug-search").addEventListener("input", (e) => applyDrugFilter(e.target.value));
    renderPayerDrugCategories(state.drugs);
    loadPayerPageData();
  } catch (err) {
    document.getElementById("drug-categories").innerHTML = "";
    document.getElementById("drug-categories").append(el("p", { class: "empty-state" }, `Error loading drugs: ${err.message}`));
    document.getElementById("payer-drug-categories").innerHTML = "";
    document.getElementById("payer-drug-categories").append(el("p", { class: "empty-state" }, `Error loading drugs: ${err.message}`));
  }

  initTopTabs();
  initPayerPage();
}

function initTopTabs() {
  const tabs = document.querySelectorAll(".top-tab");
  for (const tab of tabs) {
    tab.addEventListener("click", () => {
      for (const t of tabs) t.classList.toggle("active", t === tab);
      for (const page of document.querySelectorAll(".page")) {
        page.hidden = page.id !== `page-${tab.dataset.page}`;
      }
    });
  }
}

init();
