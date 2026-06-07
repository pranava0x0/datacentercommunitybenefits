/* ==========================================================================
 * Data Center Community Benefits Dashboard — app.js
 * ==========================================================================
 *
 * Two views: Comparison (default) + Explorer (lazy-loaded with Leaflet).
 * Per CLAUDE.md:
 *   - THEMES is the canonical vocabulary (test_themes_match_frontend enforces parity).
 *   - Colors are CSS-var-driven; never hard-coded here.
 *   - The Explorer view code-splits Leaflet so first paint is just the matrix.
 *   - [hidden] attribute is paired with `[hidden] { display: none !important }`.
 * ==========================================================================
 */

"use strict";

// --------------------------------------------------------------------------
// Canonical vocabularies (must match schema.py — guarded by tests)
// --------------------------------------------------------------------------

const THEMES = [
  "jobs",
  "tax_revenue",
  "energy",
  "water",
  "community_grants",
  "infrastructure",
  "education",
  "engagement",
];

const THEME_LABELS = {
  jobs: "Jobs",
  tax_revenue: "Tax revenue",
  energy: "Energy",
  water: "Water",
  community_grants: "Community grants",
  infrastructure: "Infrastructure",
  education: "Education",
  engagement: "Engagement",
};

const COMPANY_SLUGS = [
  "meta",
  "google",
  "microsoft",
  "amazon",
  "openai",
  "anthropic",
  "xai",
  "oracle",
  "wonder-valley",
  "qts",
  "crusoe",
  "coreweave",
  "prologis",
];

const STANCE_LABELS = {
  positive: "Positive",
  mixed: "Mixed",
  negative: "Negative",
};

const CONSTITUENCY_LABELS = {
  residents: "Residents",
  local_government: "Local government",
  ngo: "NGO",
  academic: "Academic",
  journalist: "Journalist",
  regulator: "Regulator",
};

const STATUS_LABELS = {
  announced: "Announced",
  construction: "Under construction",
  operational: "Operational",
};

// v1.13: Delivered-vs-promised vocabulary. Must mirror schema.DELIVERED_STATUSES.
// Frontend test `test_themes_match_frontend.py` enforces parity.
const DELIVERED_STATUSES = ["delivered", "partial", "contested", "shortfall"];
const DELIVERED_LABELS = {
  delivered: "Delivered",
  partial: "Partial",
  contested: "Contested",
  shortfall: "Shortfall",
};
// One-line tooltip explanations of each status — surfaced as the title=
// attribute on the badge.
const DELIVERED_DESCRIPTIONS = {
  delivered: "Independent reporting confirms the commitment was met.",
  partial: "Meaningful progress but short of the stated scope.",
  contested: "Company maintains delivery; another party documents shortfall.",
  shortfall: "Independent reporting documents the commitment was not delivered.",
};

// v1.15: Ratepayer Protection Pledge vocabulary. Must mirror
// schema.RATEPAYER_STATUSES / RATEPAYER_LABELS (parity test enforces it).
const RATEPAYER_STATUSES = ["affirmed", "pledge_only", "contested"];
const RATEPAYER_LABELS = {
  affirmed: "Site-specific commitment",
  pledge_only: "National pledge only",
  contested: "Contested",
};
const RATEPAYER_DESCRIPTIONS = {
  affirmed:
    "Company published a ratepayer / pay-our-own-way commitment for this exact site.",
  pledge_only:
    "Covered by the national pledge signature; no site-specific commitment captured.",
  contested:
    "A credible third party documents this site shifting costs to ratepayers despite the pledge.",
};

// v1.XX: Per-pledge-principle fulfillment breakdown. Must mirror
// schema.PLEDGE_PRINCIPLES / PLEDGE_PRINCIPLE_STATUSES.
const PLEDGE_PRINCIPLES = [
  "new_generation",
  "delivery_infra",
  "separate_rate",
  "local_jobs",
  "grid_resilience",
];
const PLEDGE_PRINCIPLE_LABELS = {
  new_generation: "Building, bringing, or buying new power supply",
  delivery_infra: "Paying for new power delivery infrastructure upgrades",
  separate_rate:  "Paying whether they use the power or not",
  local_jobs:     "Investing in local job creation and workforce development",
  grid_resilience:"Contributing to electric and community resilience",
};
const PLEDGE_PRINCIPLE_DESCRIPTIONS = {
  new_generation:
    "Building, bringing, or buying new generation — paying the full cost of the new generation and electricity needed to meet their demand.",
  delivery_infra:
    "Paying for all transmission and distribution infrastructure upgrades needed to serve their data centers so the expense isn't passed to ordinary households.",
  separate_rate:
    "Negotiating separate rate structures with utilities and states and paying those rates for the power and infrastructure brought online, used or not.",
  local_jobs:
    "Hiring from the local community and building skills-development programs where they operate.",
  grid_resilience:
    "Coordinating with grid operators and making backup generation available at times of scarcity to help prevent blackouts.",
};
const PLEDGE_PRINCIPLE_STATUSES = ["met", "partial", "not_met", "unknown"];
const PLEDGE_PRINCIPLE_STATUS_LABELS = {
  met: "Met",
  partial: "Partial / Pledge only",
  not_met: "Not met",
  unknown: "Not assessed",
};
// The seven White House pledge signatories (2026-03-04). Mirrors the
// ratepayer_pledge_signatory=true rows in companies.json; used only as a
// fallback ordering hint — the live truth is read from the company records.
const RATEPAYER_PLEDGE_SIGNATORIES = [
  "amazon",
  "google",
  "meta",
  "microsoft",
  "openai",
  "oracle",
  "xai",
];

// --------------------------------------------------------------------------
// Aggregate table sort state (v1.17)
// --------------------------------------------------------------------------
// Per-table sort: { key: string, dir: 1 | -1 }
// Default sort is by capex descending (highest investment first).
// 'responses' sorts by total (positive+mixed+negative).
// 'name' / 'state' sorts alphabetically.
const _aggSort = {
  company: { key: "capex", dir: -1 },
  state: { key: "capex", dir: -1 },
};

// Sort orders for the Explorer's project list. Each option is descending —
// the question the dashboard answers is always "where is the most benefit
// concentrated?" so the highest-scoring project belongs at the top.
//
// Composite is the default: equal-weight blend of normalized investment,
// jobs, and claim-count. Single-metric options surface what each axis
// looks like in isolation. Project name is the tie-breaker everywhere so
// sort order is stable on every render.
const SORT_OPTIONS = ["composite", "investment", "jobs", "claims"];
const SORT_LABELS = {
  composite: "Composite (most benefit)",
  investment: "Claimed investment ($)",
  jobs: "Claimed jobs",
  claims: "First-party claims",
};

// --------------------------------------------------------------------------
// State
// --------------------------------------------------------------------------

const state = {
  companies: [],
  claims: [],
  projects: [],
  responses: [],
  responsesByProject: new Map(),
  claimsByProject: new Map(),
  companiesBySlug: new Map(),
  activeView: "comparison",
  selectedCompanySlug: null,
  explorerFilters: {
    company: "",
    status: "",
    stance: "",
    state: "",
    theme: "",
    constituency: "",
  },
  explorerSort: "composite",
  selectedProjectId: null,
  pendingProjectId: null,
  explorerLoaded: false,
  ratepayerLoaded: false,
  aggregateLoaded: false,
  leafletLoaded: false,
  map: null,
  markers: new Map(),
};

// Default Explorer filter shape — single source of truth for init + reset so
// the six dimensions stay in sync everywhere.
const EMPTY_EXPLORER_FILTERS = {
  company: "",
  status: "",
  stance: "",
  state: "",
  theme: "",
  constituency: "",
};

// --------------------------------------------------------------------------
// Boot
// --------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  applyStoredTheme();
  wireThemeToggle();
  readFiltersFromUrl();
  wireTabs();
  loadComparisonData()
    .then(() => {
      // Idle-preload projects + responses JSON (NOT Leaflet) so the
      // summary-stats bar can fill in projects / GW / investment / responses
      // without waiting for the user to open the Explorer tab. Runs after the
      // Comparison view has rendered and uses loadProjectData (data-only), so
      // the two-payload first-paint strategy is preserved.
      if (state.explorerLoaded || state.projects.length) return;
      const preload = () =>
        loadProjectData()
          .then(renderSummaryStats)
          .catch((err) =>
            console.error("Idle preload of project data failed:", err)
          );
      if ("requestIdleCallback" in window) {
        window.requestIdleCallback(preload, { timeout: 2000 });
      } else {
        setTimeout(preload, 800);
      }
    })
    .catch((err) => {
      console.error("Failed to load comparison data:", err);
      document.getElementById("meta").textContent =
        "Failed to load data. Check the console.";
    });
});

// --------------------------------------------------------------------------
// Theme
// --------------------------------------------------------------------------

function applyStoredTheme() {
  const stored = localStorage.getItem("dcb-theme");
  if (stored === "dark" || stored === "light") {
    document.documentElement.setAttribute("data-theme", stored);
  } else if (
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    document.documentElement.setAttribute("data-theme", "dark");
  }
}

function wireThemeToggle() {
  const btn = document.getElementById("theme-toggle");
  btn.addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") || "light";
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("dcb-theme", next);
  });
}

// --------------------------------------------------------------------------
// Tabs
// --------------------------------------------------------------------------

// The three views, each backed by a tab button + a <section>. The hash maps
// 1:1 to the view name; comparison is the default (no hash). Iterate this
// table everywhere so adding a 4th view stays a one-line change.
const VIEWS = [
  { name: "comparison", tab: "tab-comparison", section: "view-comparison", hash: "" },
  { name: "explorer", tab: "tab-explorer", section: "view-explorer", hash: "#explorer" },
  { name: "ratepayer", tab: "tab-ratepayer", section: "view-ratepayer", hash: "#ratepayer" },
  { name: "aggregate", tab: "tab-aggregate", section: "view-aggregate", hash: "#aggregate" },
];

// Scroll a tab button into the visible portion of the tabbar. Called both
// synchronously (on tab click) and deferred (on page-load) so the active tab
// is always visible on mobile where the bar overflows horizontally.
function scrollTabIntoView(tabEl) {
  const bar = tabEl.closest(".tabbar");
  if (!bar) return;
  const tabLeft = tabEl.offsetLeft - bar.offsetLeft;
  const tabRight = tabLeft + tabEl.offsetWidth;
  if (tabLeft < bar.scrollLeft) {
    bar.scrollLeft = tabLeft - 12;
  } else if (tabRight > bar.scrollLeft + bar.clientWidth) {
    bar.scrollLeft = tabRight - bar.clientWidth + 12;
  }
}

function wireTabs() {
  for (const v of VIEWS) {
    document
      .getElementById(v.tab)
      .addEventListener("click", () => activateView(v.name));
  }

  // Allow URL hash to deep-link to a non-default view on load. Also activate
  // the Explorer when filter query params are present (even without the
  // #explorer hash) so a deep-linked filtered Explorer round-trips.
  const fromHash = VIEWS.find((v) => v.hash && v.hash === window.location.hash);
  if (fromHash) {
    activateView(fromHash.name);
  } else if (anyExplorerFilterSet() || state.pendingProjectId) {
    activateView("explorer");
  }
}

// True when any of the six Explorer filter dimensions is set.
function anyExplorerFilterSet() {
  const f = state.explorerFilters;
  return Boolean(
    f.company || f.state || f.status || f.stance || f.theme || f.constituency
  );
}

const URL_FILTER_KEYS = [
  "company",
  "state",
  "status",
  "stance",
  "theme",
  "constituency",
];

// Parse window.location.search into state.explorerFilters + pendingProjectId.
// Called once on boot, before any render, so the Explorer paints with the
// URL-encoded filters already applied. Unknown keys are ignored.
function readFiltersFromUrl() {
  try {
    const params = new URLSearchParams(window.location.search);
    for (const k of URL_FILTER_KEYS) {
      const v = params.get(k);
      if (v) state.explorerFilters[k] = v;
    }
    const pid = params.get("project");
    if (pid) state.pendingProjectId = pid;
  } catch (err) {
    console.warn("Could not parse URL filter state:", err);
  }
}

// Serialize Explorer filters + open project back to the URL via
// history.replaceState (not pushState — no new history entry per change).
// Keeps the #explorer hash while the Explorer is active so deep-links
// round-trip cleanly. Only writes when the Explorer is the active view, so
// it doesn't clobber the #ratepayer hash.
function writeFiltersToUrl() {
  if (state.activeView !== "explorer") return;
  try {
    const params = new URLSearchParams();
    const f = state.explorerFilters;
    for (const k of URL_FILTER_KEYS) {
      if (f[k]) params.set(k, f[k]);
    }
    const pid = state.selectedProjectId || state.pendingProjectId;
    if (pid) params.set("project", pid);
    const qs = params.toString();
    const url = window.location.pathname + (qs ? "?" + qs : "") + "#explorer";
    history.replaceState(null, "", url);
  } catch (err) {
    console.warn("Could not write URL filter state:", err);
  }
}

function activateView(name) {
  const target = VIEWS.find((v) => v.name === name) || VIEWS[0];
  state.activeView = target.name;

  for (const v of VIEWS) {
    const isActive = v.name === target.name;
    const tabEl = document.getElementById(v.tab);
    tabEl.setAttribute("aria-selected", String(isActive));
    document.getElementById(v.section).hidden = !isActive;
    // Scroll the active tab into view within the tabbar (important on mobile
    // where the bar overflows horizontally). scrollIntoView scrolls the page;
    // instead manually adjust the tabbar container's scrollLeft.
    // Use a helper so it can be called both immediately (tab click) and
    // deferred (page-load, when layout isn't ready yet during DOMContentLoaded).
    if (isActive) {
      scrollTabIntoView(tabEl);
      // Deferred pass covers page-load: offsetLeft is often 0 during the
      // first synchronous DOMContentLoaded run; a macrotask fires after paint.
      setTimeout(() => scrollTabIntoView(tabEl), 0);
    }
  }

  // Keep the URL in sync so views are deep-linkable / back-button friendly.
  // The Explorer serializes its full filter state (via writeFiltersToUrl);
  // the other views use a bare hash and drop any stale query string.
  if (target.name === "explorer") {
    writeFiltersToUrl();
  } else if (target.hash) {
    history.replaceState(null, "", target.hash);
  } else if (window.location.hash || window.location.search) {
    history.replaceState(null, "", window.location.pathname);
  }

  // The Explorer and Ratepayer views both need the projects/responses payload.
  if (target.name === "explorer" && !state.explorerLoaded) {
    loadExplorerData().catch((err) => {
      console.error("Failed to load explorer data:", err);
      document.getElementById("explorer-meta").textContent =
        "Failed to load projects.";
    });
  } else if (target.name === "ratepayer") {
    loadRatepayerView().catch((err) => {
      console.error("Failed to load ratepayer view:", err);
    });
  } else if (target.name === "aggregate") {
    loadAggregateView().catch((err) => {
      console.error("Failed to load aggregate view:", err);
    });
  }
}

// --------------------------------------------------------------------------
// Data loading
// --------------------------------------------------------------------------

async function loadComparisonData() {
  const [companies, claims] = await Promise.all([
    fetchJson("data/companies.json"),
    fetchJson("data/claims.json"),
  ]);
  state.companies = companies.companies;
  state.claims = claims.claims;
  state.companiesBySlug = new Map(state.companies.map((c) => [c.slug, c]));
  updateDraftBanner(companies.generated_at);
  renderComparisonView();
  renderSummaryStats();
}

// Fetch + index the projects/responses payload. Shared by the Explorer and
// Ratepayer views; safe to call repeatedly (fetches at most once). Does NOT
// touch Leaflet — that's the Explorer's concern alone.
let _projectDataPromise = null;
function loadProjectData() {
  if (!_projectDataPromise) {
    _projectDataPromise = (async () => {
      const [projects, responses] = await Promise.all([
        fetchJson("data/projects.json"),
        fetchJson("data/responses.json"),
      ]);
      state.projects = projects.projects;
      state.responses = responses.responses;

      state.responsesByProject = new Map();
      for (const r of state.responses) {
        if (!state.responsesByProject.has(r.project_id)) {
          state.responsesByProject.set(r.project_id, []);
        }
        state.responsesByProject.get(r.project_id).push(r);
      }

      state.claimsByProject = new Map();
      for (const c of state.claims) {
        if (!c.project_id) continue;
        if (!state.claimsByProject.has(c.project_id)) {
          state.claimsByProject.set(c.project_id, []);
        }
        state.claimsByProject.get(c.project_id).push(c);
      }
      // Fill in the projects / GW / investment / responses tiles now that the
      // lazy payload is in hand (companies + claims tiles already showed).
      renderSummaryStats();
    })();
  }
  return _projectDataPromise;
}

async function loadExplorerData() {
  document.getElementById("explorer-meta").textContent = "Loading projects…";
  await loadProjectData();
  await ensureLeaflet();
  state.explorerLoaded = true;
  renderExplorerView();

  // Expose for e2e/debugging.
  window.__dcb = { state, THEMES, selectProject };
  document.dispatchEvent(new CustomEvent("dcb:explorer-ready"));
}

// Ratepayer view: needs the project payload (for the scorecard) but not
// Leaflet. Renders once data is in hand.
async function loadRatepayerView() {
  await loadProjectData();
  state.ratepayerLoaded = true;
  renderRatepayerView();
  document.dispatchEvent(new CustomEvent("dcb:ratepayer-ready"));
}

// Aggregate view: needs the project payload but not Leaflet.
async function loadAggregateView() {
  if (state.aggregateLoaded) return;
  await loadProjectData();
  state.aggregateLoaded = true;
  renderAggregateView();
}

async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return await res.json();
}

// --------------------------------------------------------------------------
// Comparison view rendering
// --------------------------------------------------------------------------

function renderComparisonView() {
  renderMeta();
  renderThemeLegend();
  renderMatrix();
  wireCompanyDetail();
  wireMatrixCsvExport();
}

function renderMeta() {
  // Sub-heading shows last refresh date (set when companies.json loads).
  const el = document.getElementById("meta");
  if (!el) return;
  if (el.dataset.refreshDate) {
    el.textContent = `Last refreshed: ${el.dataset.refreshDate}`;
  }
}

function updateDraftBanner(generatedAt) {
  // Banner removed (v1.16). Wire the date into the topbar sub-heading instead.
  const el = document.getElementById("meta");
  if (el && generatedAt) {
    el.dataset.refreshDate = generatedAt;
    el.textContent = `Last refreshed: ${generatedAt}`;
  }
}

// Aggregate dataset stats shown in the topbar strip. Progressively enhances:
// called after companies+claims load (companies / claims tiles), and again
// after the lazy projects/responses payload lands (projects / GW / investment
// / responses). Never blocks first paint on the lazy payload.
function renderSummaryStats() {
  const setNum = (id, txt) => {
    const el = document.getElementById(id);
    if (el) el.textContent = txt;
  };

  if (state.companies.length) setNum("ss-companies", state.companies.length);
  if (state.claims.length) setNum("ss-claims", state.claims.length);

  if (state.projects.length) {
    setNum("ss-projects", state.projects.length);
    const mw = state.projects.reduce((s, p) => s + (p.power_mw || 0), 0);
    setNum("ss-power", formatSummaryGW(mw));
    const usd = state.projects.reduce(
      (s, p) => s + (p.claimed_investment_usd || 0),
      0
    );
    setNum("ss-investment", formatSummaryUsd(usd));
  }

  if (state.responses.length) {
    setNum("ss-responses", state.responses.length);
    const byStance = { positive: 0, mixed: 0, negative: 0 };
    for (const r of state.responses) {
      if (byStance[r.stance] !== undefined) byStance[r.stance] += 1;
    }
    const breakdown = document.getElementById("ss-stance-breakdown");
    if (breakdown) {
      breakdown.innerHTML =
        `<span class="stance-dot positive"></span>${byStance.positive}` +
        `<span class="stance-dot mixed"></span>${byStance.mixed}` +
        `<span class="stance-dot negative"></span>${byStance.negative}`;
      breakdown.hidden = false;
    }
  }
}

function formatSummaryGW(mw) {
  if (!mw) return "—";
  const gw = mw / 1000;
  if (gw >= 100) return `${Math.round(gw)} GW`;
  if (gw >= 10) return `${gw.toFixed(1)} GW`;
  return `${gw.toFixed(2)} GW`;
}

function formatSummaryUsd(usd) {
  if (!usd) return "—";
  if (usd >= 1e12) return `$${(usd / 1e12).toFixed(2)} T`;
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(usd >= 100e9 ? 0 : 1)} B`;
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(0)} M`;
  return `$${usd}`;
}

// Download CSV button on the Comparison view. Long format: one row per
// company × theme (slug, name, theme key, theme label, claim count).
function wireMatrixCsvExport() {
  const btn = document.getElementById("matrix-csv");
  if (!btn || btn.dataset.wired === "1") return;
  btn.dataset.wired = "1";
  btn.addEventListener("click", downloadMatrixCsv);
}

function downloadMatrixCsv() {
  const counts = new Map();
  for (const c of state.claims) {
    const key = `${c.company_slug}|${c.theme}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  const rows = [
    ["company_slug", "company_name", "theme", "theme_label", "claim_count"],
  ];
  for (const co of state.companies) {
    for (const t of THEMES) {
      const n = counts.get(`${co.slug}|${t}`) || 0;
      rows.push([co.slug, co.name, t, THEME_LABELS[t] || t, String(n)]);
    }
  }
  const csv = rows.map((r) => r.map(csvCell).join(",")).join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const today = new Date().toISOString().slice(0, 10);
  const a = document.createElement("a");
  a.href = url;
  a.download = `dcb-matrix-${today}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// Minimal RFC-4180 cell quoter.
function csvCell(v) {
  const s = String(v == null ? "" : v);
  if (/[",\r\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function renderThemeLegend() {
  const ul = document.getElementById("theme-legend");
  ul.innerHTML = "";
  for (const t of THEMES) {
    const li = document.createElement("li");
    li.className = "theme-chip";
    li.style.setProperty("--theme-color", `var(--theme-${t})`);
    li.textContent = THEME_LABELS[t];
    ul.appendChild(li);
  }
}

function renderMatrix() {
  const headRow = document.getElementById("matrix-head-row");
  const body = document.getElementById("matrix-body");
  headRow.innerHTML = "";
  body.innerHTML = "";

  const corner = document.createElement("th");
  corner.className = "col-company";
  corner.textContent = "Company";
  headRow.appendChild(corner);

  for (const t of THEMES) {
    const th = document.createElement("th");
    th.className = "col-theme-head";
    th.style.setProperty("--theme-color", `var(--theme-${t})`);
    th.textContent = THEME_LABELS[t];
    th.scope = "col";
    headRow.appendChild(th);
  }

  // Index claim counts: company × theme
  const counts = new Map();
  for (const c of state.claims) {
    const key = `${c.company_slug}|${c.theme}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  }

  for (const co of state.companies) {
    const tr = document.createElement("tr");
    tr.dataset.company = co.slug;

    // Whole-row click + keyboard activation opens the company pop-out.
    // We also expose role=button on the company-name <th> so the row reads
    // as a single interactive unit to assistive tech.
    const openCompany = () => selectCompany(co.slug);

    const nameCell = document.createElement("th");
    nameCell.className = "col-company";
    nameCell.scope = "row";
    nameCell.style.setProperty("--co-color", `var(--co-${co.slug})`);
    nameCell.setAttribute("role", "button");
    nameCell.tabIndex = 0;
    nameCell.setAttribute(
      "aria-label",
      `${co.name} — click to view community-engagement summary`
    );
    nameCell.innerHTML = `
      <span class="company-name">
        <span class="company-dot" aria-hidden="true"></span>
        ${escapeHtml(co.name)}
      </span>
    `;
    nameCell.addEventListener("click", openCompany);
    nameCell.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openCompany();
      }
    });
    tr.appendChild(nameCell);

    for (const t of THEMES) {
      const td = document.createElement("td");
      const n = counts.get(`${co.slug}|${t}`) || 0;
      td.dataset.company = co.slug;
      td.dataset.theme = t;

      if (n === 0) {
        td.className = "cell empty";
        td.innerHTML = `<span aria-hidden="true">—</span><span class="visually-hidden">no claims</span>`;
      } else {
        td.className = "cell";
        // Binary checkmark — see CLAUDE.md > "Matrix is checkmark-only".
        // Cells are also clickable as a richer affordance: clicking any
        // populated cell opens the same company pop-out the row name does.
        td.innerHTML = `<span class="count check" aria-hidden="true">✓</span>`;
        td.setAttribute("role", "button");
        td.tabIndex = 0;
        td.setAttribute(
          "aria-label",
          `${n} ${co.name} ${THEME_LABELS[t]} claim${n === 1 ? "" : "s"} — click to view ${co.name} summary`
        );
        td.addEventListener("click", openCompany);
        td.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openCompany();
          }
        });
        // Hover tooltip: show first claim statement for this company×theme.
        td.addEventListener("mouseenter", (e) => showMatrixTooltip(e.currentTarget, co.slug, t));
        td.addEventListener("mouseleave", hideMatrixTooltip);
        td.addEventListener("focus", (e) => showMatrixTooltip(e.currentTarget, co.slug, t));
        td.addEventListener("blur", hideMatrixTooltip);
      }
      tr.appendChild(td);
    }

    body.appendChild(tr);
  }
}

// --------------------------------------------------------------------------
// Matrix cell tooltip (v1.17)
// --------------------------------------------------------------------------
// Shows the first claim statement for a company × theme cell on hover/focus.
// A single #matrix-tooltip div is reused (created lazily, never duplicated).

function _getMatrixTooltipEl() {
  return document.getElementById("matrix-tooltip");
}

function showMatrixTooltip(cellEl, slug, theme) {
  const tooltip = _getMatrixTooltipEl();
  if (!tooltip) return;

  // Find the first claim for this company/theme
  const claim = state.claims.find((c) => c.company_slug === slug && c.theme === theme);
  if (!claim) return;

  const MAX = 160;
  const stmt = claim.statement.length > MAX
    ? claim.statement.slice(0, MAX).trimEnd() + "…"
    : claim.statement;

  tooltip.innerHTML = `
    <span class="mtt-theme" style="--theme-color:var(--theme-${escapeAttr(theme)})">${escapeHtml(THEME_LABELS[theme] || theme)}</span>
    <p class="mtt-quote">${escapeHtml(stmt)}</p>
    <span class="mtt-hint">Click to view all ${escapeHtml(THEME_LABELS[theme] || theme)} claims</span>
  `;
  tooltip.hidden = false;

  // Position below the cell, clamped inside the matrix-wrap
  const wrap = cellEl.closest(".matrix-wrap") || cellEl.offsetParent;
  const wrapRect = wrap ? wrap.getBoundingClientRect() : { left: 0, top: 0 };
  const cellRect = cellEl.getBoundingClientRect();

  const left = Math.min(
    cellRect.left - wrapRect.left,
    (wrap ? wrap.clientWidth : 600) - tooltip.offsetWidth - 8
  );
  const top = cellRect.bottom - wrapRect.top + 6;

  tooltip.style.left = `${Math.max(4, left)}px`;
  tooltip.style.top = `${top}px`;
}

function hideMatrixTooltip() {
  const tooltip = _getMatrixTooltipEl();
  if (tooltip) tooltip.hidden = true;
}

// --------------------------------------------------------------------------
// Company pop-out (Comparison view) — opens on company-row / cell click
// --------------------------------------------------------------------------

function wireCompanyDetail() {
  const closeBtn = document.getElementById("company-detail-close");
  if (closeBtn && !closeBtn.dataset.wired) {
    closeBtn.addEventListener("click", closeCompanyDetail);
    closeBtn.dataset.wired = "1";
  }

  const viewProjectsBtn = document.getElementById("cd-view-projects");
  if (viewProjectsBtn && !viewProjectsBtn.dataset.wired) {
    viewProjectsBtn.addEventListener("click", () => {
      const slug = state.selectedCompanySlug;
      if (!slug) return;
      // Pre-set the explorer company filter, switch view. If the explorer
      // is already loaded (subsequent visit), sync the select UI + refresh
      // the list/map. On first load, renderExplorerView() will pick up the
      // pre-set state.explorerFilters.company itself.
      state.explorerFilters.company = slug;
      closeCompanyDetail();
      activateView("explorer");
      if (state.explorerLoaded) {
        syncExplorerFilterUIToState();
        refreshExplorer();
      }
    });
    viewProjectsBtn.dataset.wired = "1";
  }

  // Esc closes the pop-out, but only when comparison is the active view
  // (the explorer view has its own Esc binding for the project detail).
  if (!document._dcbCompanyEscWired) {
    document.addEventListener("keydown", (e) => {
      if (
        e.key === "Escape" &&
        state.activeView === "comparison" &&
        state.selectedCompanySlug
      ) {
        closeCompanyDetail();
      }
    });
    document._dcbCompanyEscWired = true;
  }
}

function selectCompany(slug) {
  const co = state.companiesBySlug.get(slug);
  if (!co) return;
  state.selectedCompanySlug = slug;

  const panel = document.getElementById("company-detail");
  panel.style.setProperty("--co-color", `var(--co-${slug})`);

  document.getElementById("cd-hq").textContent = co.hq;
  document.getElementById("cd-name").textContent = co.name;

  const summaryEl = document.getElementById("cd-summary");
  if (co.summary) {
    summaryEl.textContent = co.summary;
    summaryEl.classList.remove("muted");
  } else {
    summaryEl.textContent =
      "No community-impact summary captured for this company yet.";
    summaryEl.classList.add("muted");
  }

  setKvLink(
    "cd-page-link",
    co.dedicated_page_url,
    co.dedicated_page_url ? "Open page →" : null
  );

  const claimCount = state.claims.filter((c) => c.company_slug === slug).length;
  setKv(
    "cd-claim-count",
    claimCount === 0 ? null : `${claimCount} claim${claimCount === 1 ? "" : "s"}`
  );

  // Project count requires the explorer payload, which may not be loaded yet.
  // Populate optimistically; if not loaded, show "Open Project Explorer to view".
  const projects = state.projects.filter((p) => p.company_slug === slug);
  if (state.explorerLoaded) {
    setKv(
      "cd-project-count",
      projects.length === 0
        ? null
        : `${projects.length} project${projects.length === 1 ? "" : "s"}`
    );
  } else {
    setKv("cd-project-count", "Open Project Explorer to load");
  }

  setKv("cd-last-reviewed", co.last_reviewed);

  // Constituency breakdown — populate if project data is already loaded;
  // otherwise lazy-load and update once it arrives.
  const breakdownSection = document.getElementById("cd-responses-breakdown");
  if (state.projects.length > 0) {
    renderConstituencyBreakdown(slug);
  } else {
    if (breakdownSection) breakdownSection.hidden = true;
    loadProjectData().then(() => {
      if (state.selectedCompanySlug === slug) renderConstituencyBreakdown(slug);
    });
  }

  panel.hidden = false;
  document.getElementById("company-detail-close").focus({ preventScroll: true });
  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });

  refreshActiveCompanyRow();
}

function closeCompanyDetail() {
  state.selectedCompanySlug = null;
  const panel = document.getElementById("company-detail");
  if (panel) panel.hidden = true;
  refreshActiveCompanyRow();
}

// Build and render the constituency × stance breakdown for a company in
// the company detail pop-out. Shows how different groups have responded
// to this company's projects. Requires project + responses data to be loaded.
function renderConstituencyBreakdown(slug) {
  const section = document.getElementById("cd-responses-breakdown");
  const body = document.getElementById("cd-breakdown-body");
  if (!section || !body) return;

  // Collect all responses for projects owned by this company
  const coProjects = new Set(
    state.projects.filter((p) => p.company_slug === slug).map((p) => p.id)
  );
  const resps = state.responses.filter((r) => coProjects.has(r.project_id));

  if (resps.length === 0) {
    section.hidden = true;
    return;
  }

  // Tally by constituency
  const tally = {};
  for (const r of resps) {
    if (!tally[r.constituency]) tally[r.constituency] = { positive: 0, mixed: 0, negative: 0 };
    tally[r.constituency][r.stance]++;
  }

  // Sort by total responses desc
  const sorted = Object.entries(tally).sort(
    (a, b) => (b[1].positive + b[1].mixed + b[1].negative) - (a[1].positive + a[1].mixed + a[1].negative)
  );

  body.innerHTML = sorted
    .map(([constituency, counts]) => {
      const total = counts.positive + counts.mixed + counts.negative;
      const label = CONSTITUENCY_LABELS[constituency] || constituency;
      return `<div class="cb-row">
        <span class="cb-label">${escapeHtml(label)}</span>
        <span class="cb-bars">
          ${counts.positive ? `<span class="cb-seg positive" style="flex:${counts.positive}" title="${counts.positive} positive"></span>` : ""}
          ${counts.mixed ? `<span class="cb-seg mixed" style="flex:${counts.mixed}" title="${counts.mixed} mixed"></span>` : ""}
          ${counts.negative ? `<span class="cb-seg negative" style="flex:${counts.negative}" title="${counts.negative} negative"></span>` : ""}
        </span>
        <span class="cb-total">${total}</span>
      </div>`;
    })
    .join("");

  const totalAll = resps.length;
  body.insertAdjacentHTML(
    "beforeend",
    `<p class="cb-summary">${totalAll} total response${totalAll === 1 ? "" : "s"} across ${coProjects.size} project${coProjects.size === 1 ? "" : "s"}</p>`
  );

  section.hidden = false;
}

function refreshActiveCompanyRow() {
  document
    .querySelectorAll("#matrix-body tr.active")
    .forEach((el) => el.classList.remove("active"));
  if (!state.selectedCompanySlug) return;
  const row = document.querySelector(
    `#matrix-body tr[data-company="${state.selectedCompanySlug}"]`
  );
  if (row) row.classList.add("active");
}

function renderClaimCard(c) {
  const co = state.companiesBySlug.get(c.company_slug);
  const li = document.createElement("li");
  li.className = "claim-card";
  li.dataset.claimId = c.id;
  li.style.setProperty("--co-color", `var(--co-${c.company_slug})`);

  const meta = document.createElement("div");
  meta.className = "claim-meta";
  // Prefer the source's own publication date when known; fall back to the
  // curator's capture date. The visible date is "when was this said?",
  // which is rarely the same day we recorded it.
  const displayDate = c.published_at || c.captured_at;
  meta.innerHTML = `
    <span class="claim-company">${escapeHtml(co ? co.name : c.company_slug)}</span>
    <span class="claim-theme" style="--theme-color: var(--theme-${c.theme});">
      ${escapeHtml(THEME_LABELS[c.theme] || c.theme)}
    </span>
    <span title="${c.published_at ? 'Published' : 'Recorded'}: ${escapeHtml(displayDate)}">${escapeHtml(displayDate)}</span>
    ${c.metric ? renderMetricBadge(c.metric) : ""}
    ${c.formal_agreement ? `<span class="claim-cba-badge" title="Backed by a formally published pledge or signed community benefit agreement">Formal agreement</span>` : ""}
  `;

  const quote = document.createElement("p");
  quote.className = "claim-quote";
  quote.textContent = c.statement;

  // Use wayback_url as fallback when the original source is known-dead.
  const sourceHref = escapeAttr(c.wayback_url || c.source_url);
  const sourceLabel = c.wayback_url
    ? `${escapeHtml(c.source_title)} (archived)`
    : escapeHtml(c.source_title);
  const source = document.createElement("p");
  source.className = "claim-source";
  source.innerHTML = `Source: <a href="${sourceHref}" target="_blank" rel="noopener noreferrer">${sourceLabel}</a>`;

  li.appendChild(meta);
  li.appendChild(quote);
  li.appendChild(source);
  if (c.delivered) li.appendChild(renderDeliveredPanel(c.delivered));
  return li;
}

// Render the delivery-assessment panel attached to a claim. Status is
// surfaced as a badge with a CSS-var-driven color (per stance palette
// precedent — see CLAUDE.md "Color tokens are CSS-var-driven").
function renderDeliveredPanel(d) {
  const div = document.createElement("div");
  div.className = `claim-delivered delivered-${d.status}`;
  const label = DELIVERED_LABELS[d.status] || d.status;
  const tip = DELIVERED_DESCRIPTIONS[d.status] || "";
  const assessed = d.assessed_at || "";
  div.innerHTML = `
    <div class="delivered-header">
      <span class="delivered-badge" title="${escapeAttr(tip)}">${escapeHtml(label)}</span>
      <span class="delivered-label">Delivered vs promised</span>
      ${assessed ? `<span class="delivered-date" title="Curator assessed on">${escapeHtml(assessed)}</span>` : ""}
    </div>
    <p class="delivered-summary">${escapeHtml(d.summary)}</p>
    <p class="delivered-source">Evidence: <a href="${escapeAttr(d.source_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(d.source_title)}</a></p>
  `;
  return div;
}

function renderMetricBadge(m) {
  const formatted = formatMetric(m);
  return `<span class="claim-metric" title="Structured value attached to this claim">${escapeHtml(
    formatted
  )}</span>`;
}

function formatMetric(m) {
  const v = m.value;
  if (m.unit === "usd") {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B${m.kind ? ` ${m.kind}` : ""}`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M${m.kind ? ` ${m.kind}` : ""}`;
    return `$${v.toLocaleString()}${m.kind ? ` ${m.kind}` : ""}`;
  }
  return `${v.toLocaleString()} ${m.unit}${m.kind ? ` (${m.kind})` : ""}`;
}

// --------------------------------------------------------------------------
// Explorer view rendering
// --------------------------------------------------------------------------

function renderExplorerView() {
  populateCompanyFilter();
  populateStateFilter();
  renderThemeFilterChips();
  renderHotRail();
  wireExplorerFilters();
  syncExplorerFilterUIToState();
  renderProjectList();
  renderProjectMap();

  // If the page loaded with ?project=<id>, open that project's detail panel
  // now that data + DOM are ready. selectProject is a no-op for unknown ids.
  if (state.pendingProjectId) {
    const pid = state.pendingProjectId;
    state.pendingProjectId = null;
    selectProject(pid);
  }
}

function syncExplorerFilterUIToState() {
  const f = state.explorerFilters;
  const co = document.getElementById("f-company");
  const stt = document.getElementById("f-state");
  const st = document.getElementById("f-status");
  const sn = document.getElementById("f-stance");
  const cn = document.getElementById("f-constituency");
  const so = document.getElementById("f-sort");
  if (co) co.value = f.company || "";
  if (stt) stt.value = f.state || "";
  if (st) st.value = f.status || "";
  if (sn) sn.value = f.stance || "";
  if (cn) cn.value = f.constituency || "";
  if (so) so.value = state.explorerSort || "composite";
  // Reflect the active theme into the chip row.
  const row = document.getElementById("theme-filter-row");
  if (row) {
    for (const btn of row.querySelectorAll(".theme-filter-chip")) {
      const active = btn.dataset.theme === (f.theme || "");
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    }
  }
}

function populateStateFilter() {
  const sel = document.getElementById("f-state");
  if (!sel || sel.options.length > 1) return;
  const states = Array.from(
    new Set(state.projects.map((p) => p.state).filter(Boolean))
  ).sort();
  for (const s of states) {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    sel.appendChild(opt);
  }
}

// Theme-filter chip row. Click a chip to narrow the Explorer to projects with
// ≥1 claim under that theme; click the active chip again to clear. Reads the
// canonical THEMES vocab so a new theme auto-gets a chip.
function renderThemeFilterChips() {
  const row = document.getElementById("theme-filter-row");
  if (!row || row.childElementCount > 0) return;
  for (const t of THEMES) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "theme-filter-chip";
    btn.dataset.theme = t;
    btn.setAttribute("aria-pressed", "false");
    btn.style.setProperty("--theme-color", `var(--theme-${t})`);
    btn.innerHTML = `<span class="theme-filter-dot" aria-hidden="true"></span>${escapeHtml(
      THEME_LABELS[t] || t
    )}`;
    btn.addEventListener("click", () => {
      const cur = state.explorerFilters.theme || "";
      state.explorerFilters.theme = cur === t ? "" : t;
      syncExplorerFilterUIToState();
      refreshExplorer();
    });
    row.appendChild(btn);
  }
}

function populateCompanyFilter() {
  const sel = document.getElementById("f-company");
  // Skip if already populated (re-renders).
  if (sel.options.length > 1) return;
  const present = new Set(state.projects.map((p) => p.company_slug));
  for (const co of state.companies) {
    if (!present.has(co.slug)) continue;
    const opt = document.createElement("option");
    opt.value = co.slug;
    opt.textContent = co.name;
    sel.appendChild(opt);
  }
}

// --------------------------------------------------------------------------
// Recently-contested rail (auto-derived, no curator featured flag)
// --------------------------------------------------------------------------
// A project belongs on the rail when it has (a) negative/mixed-stance
// responses in the last ~180 days, or (b) claims with delivered status
// "contested" / "shortfall". Score = weighted sum; the most-actively
// contested sites surface first.
const HOT_RAIL_WINDOW_DAYS = 180;
const HOT_RAIL_MAX_CARDS = 6;

function renderHotRail() {
  const rail = document.getElementById("hot-rail");
  const list = document.getElementById("hot-rail-list");
  if (!rail || !list) return;
  list.innerHTML = "";

  const now = Date.now();
  const windowMs = HOT_RAIL_WINDOW_DAYS * 24 * 60 * 60 * 1000;

  const scored = [];
  for (const p of state.projects) {
    const responses = state.responsesByProject.get(p.id) || [];
    const claims = state.claimsByProject.get(p.id) || [];

    let recentNeg = 0;
    let recentMixed = 0;
    let latestNeg = null;
    for (const r of responses) {
      const t = Date.parse(r.date);
      if (Number.isNaN(t) || now - t > windowMs) continue;
      if (r.stance === "negative") {
        recentNeg += 1;
        if (!latestNeg || Date.parse(r.date) > Date.parse(latestNeg.date)) {
          latestNeg = r;
        }
      } else if (r.stance === "mixed") {
        recentMixed += 1;
      }
    }

    const contestedClaims = claims.filter(
      (c) =>
        c.delivered &&
        (c.delivered.status === "contested" ||
          c.delivered.status === "shortfall")
    );

    const score =
      recentNeg * 2 + recentMixed * 0.5 + contestedClaims.length * 1.5;
    if (score <= 0) continue;

    let hint;
    if (latestNeg) {
      hint = latestNeg.summary;
    } else if (contestedClaims.length) {
      hint = contestedClaims[0].delivered.summary;
    } else if (recentMixed) {
      hint = "Recent mixed community response on the record.";
    } else {
      hint = "Contested delivery on the record.";
    }

    scored.push({ project: p, score, hint, latestNeg });
  }

  if (!scored.length) {
    rail.hidden = true;
    return;
  }

  scored.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    const aT = a.latestNeg ? Date.parse(a.latestNeg.date) : 0;
    const bT = b.latestNeg ? Date.parse(b.latestNeg.date) : 0;
    return bT - aT;
  });

  for (const item of scored.slice(0, HOT_RAIL_MAX_CARDS)) {
    list.appendChild(renderHotRailCard(item));
  }
  rail.hidden = false;
}

function renderHotRailCard({ project: p, hint }) {
  const co = state.companiesBySlug
    ? state.companiesBySlug.get(p.company_slug)
    : null;
  const coName = co ? co.name : p.company_slug;
  const li = document.createElement("li");
  li.className = "hot-card";
  li.style.setProperty("--co-color", `var(--co-${p.company_slug})`);
  li.tabIndex = 0;
  li.setAttribute("role", "button");
  li.setAttribute("aria-label", `Open ${p.name} — recently contested case`);

  const statusLabel = STATUS_LABELS[p.status] || p.status;
  li.innerHTML = `
    <p class="hot-card-eyebrow">${escapeHtml(coName)} · ${escapeHtml(statusLabel)}</p>
    <h4 class="hot-card-title">${escapeHtml(p.name)}</h4>
    <p class="hot-card-loc">${escapeHtml(p.city)}, ${escapeHtml(p.state)}</p>
    <p class="hot-card-hint">${escapeHtml(truncate(hint, 180))}</p>
    <p class="hot-card-cta" aria-hidden="true">View record →</p>
  `;

  const open = () => selectProject(p.id);
  li.addEventListener("click", open);
  li.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      open();
    }
  });
  return li;
}

function truncate(s, n) {
  if (!s) return "";
  return s.length <= n ? s : s.slice(0, n - 1).trimEnd() + "…";
}

function wireExplorerFilters() {
  // Guard against double-wiring on Explorer re-render.
  const root = document.querySelector(".explorer-filters");
  if (root && root.dataset.wired === "1") return;
  if (root) root.dataset.wired = "1";

  document.getElementById("f-company").addEventListener("change", (e) => {
    state.explorerFilters.company = e.target.value;
    refreshExplorer();
  });
  const stateSel = document.getElementById("f-state");
  if (stateSel) {
    stateSel.addEventListener("change", (e) => {
      state.explorerFilters.state = e.target.value;
      refreshExplorer();
    });
  }
  document.getElementById("f-status").addEventListener("change", (e) => {
    state.explorerFilters.status = e.target.value;
    refreshExplorer();
  });
  document.getElementById("f-stance").addEventListener("change", (e) => {
    state.explorerFilters.stance = e.target.value;
    refreshExplorer();
  });
  const constituencySel = document.getElementById("f-constituency");
  if (constituencySel) {
    constituencySel.addEventListener("change", (e) => {
      state.explorerFilters.constituency = e.target.value;
      refreshExplorer();
    });
  }
  const sortSel = document.getElementById("f-sort");
  if (sortSel) {
    sortSel.addEventListener("change", (e) => {
      const v = e.target.value;
      state.explorerSort = SORT_OPTIONS.includes(v) ? v : "composite";
      renderProjectList();
    });
  }
  document.getElementById("f-reset").addEventListener("click", () => {
    state.explorerFilters = { ...EMPTY_EXPLORER_FILTERS };
    state.explorerSort = "composite";
    if (sortSel) sortSel.value = "composite";
    syncExplorerFilterUIToState();
    refreshExplorer();
  });
  document.getElementById("detail-close").addEventListener("click", closeDetail);
  document.addEventListener("keydown", (e) => {
    if (
      e.key === "Escape" &&
      state.activeView === "explorer" &&
      state.selectedProjectId
    ) {
      closeDetail();
    }
  });
  wireDetailTabs();
}

// --------------------------------------------------------------------------
// Detail-panel tabs (Overview / Claims / Community)
// --------------------------------------------------------------------------

// The user's last explicitly-clicked detail tab persists *within session*.
// Page reload resets to "overview". Per CLAUDE.md cross-project lesson —
// hardcoded snap-back to Overview on every selectProject() forces users
// browsing the same tab across projects to re-click on every selection.
let _lastDetailTab = "overview";

const DETAIL_TABS = ["overview", "claims", "responses"];

function wireDetailTabs() {
  for (const name of DETAIL_TABS) {
    const btn = document.getElementById(`dtab-${name}`);
    if (!btn) continue;
    btn.addEventListener("click", () => {
      _lastDetailTab = name;
      setActiveDetailTab(name);
    });
  }
}

function setActiveDetailTab(name) {
  if (!DETAIL_TABS.includes(name)) name = "overview";
  for (const t of DETAIL_TABS) {
    const btn = document.getElementById(`dtab-${t}`);
    const pane = document.getElementById(`dpane-${t}`);
    const active = t === name;
    if (btn) btn.setAttribute("aria-selected", active ? "true" : "false");
    if (pane) pane.hidden = !active;
  }
}

function resetDetailTabs() {
  setActiveDetailTab(_lastDetailTab);
}

function updateDetailTabCounts(claimsCount, responsesCount) {
  const claimsBadge = document.getElementById("dtab-claims-count");
  const respBadge = document.getElementById("dtab-responses-count");
  if (claimsBadge) {
    if (claimsCount > 0) {
      claimsBadge.textContent = String(claimsCount);
      claimsBadge.hidden = false;
    } else {
      claimsBadge.hidden = true;
    }
  }
  if (respBadge) {
    if (responsesCount > 0) {
      respBadge.textContent = String(responsesCount);
      respBadge.hidden = false;
    } else {
      respBadge.hidden = true;
    }
  }
}

function refreshExplorer() {
  renderProjectList();
  refreshMapMarkers();
  writeFiltersToUrl();
}

function filteredProjects() {
  const f = state.explorerFilters;
  const items = state.projects.filter((p) => {
    if (f.company && p.company_slug !== f.company) return false;
    if (f.state && p.state !== f.state) return false;
    if (f.status && p.status !== f.status) return false;
    if (f.theme) {
      const cs = state.claimsByProject.get(p.id) || [];
      if (!cs.some((c) => c.theme === f.theme)) return false;
    }
    if (f.stance) {
      const rs = state.responsesByProject.get(p.id) || [];
      if (!rs.some((r) => r.stance === f.stance)) return false;
    }
    if (f.constituency) {
      const rs = state.responsesByProject.get(p.id) || [];
      if (!rs.some((r) => r.constituency === f.constituency)) return false;
    }
    return true;
  });
  return sortProjects(items, state.explorerSort);
}

// Per-project benefit metric extractors. Null/undefined investment or jobs
// counts as 0 — projects that haven't disclosed a number rank below ones
// that have, which matches the "most benefit" framing (undisclosed = not
// yet visible to the public).
function projectInvestment(p) {
  return p.claimed_investment_usd || 0;
}
function projectJobs(p) {
  return p.claimed_jobs || 0;
}
function projectClaimsCount(p) {
  const cs = state.claimsByProject.get(p.id);
  return cs ? cs.length : 0;
}

// Composite score = equal-weight average of three normalized axes
// (investment, jobs, claim count). Normalization is min-max against the
// full dataset (not the filtered subset) so a project's score doesn't
// shift as the user filters — the ranking represents the project's
// standing in the catalog as a whole. Returns [0, 1].
function buildCompositeScorer() {
  const maxInv = Math.max(1, ...state.projects.map(projectInvestment));
  const maxJobs = Math.max(1, ...state.projects.map(projectJobs));
  const maxClaims = Math.max(1, ...state.projects.map(projectClaimsCount));
  return (p) => {
    const inv = projectInvestment(p) / maxInv;
    const jobs = projectJobs(p) / maxJobs;
    const claims = projectClaimsCount(p) / maxClaims;
    return (inv + jobs + claims) / 3;
  };
}

function sortProjects(items, sortKey) {
  let scoreFn;
  switch (sortKey) {
    case "investment":
      scoreFn = projectInvestment;
      break;
    case "jobs":
      scoreFn = projectJobs;
      break;
    case "claims":
      scoreFn = projectClaimsCount;
      break;
    case "composite":
    default:
      scoreFn = buildCompositeScorer();
      break;
  }
  // Descending by score; stable tiebreaker on project name so
  // re-renders don't reshuffle equal-scoring items.
  return items
    .map((p) => ({ p, score: scoreFn(p) }))
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.p.name.localeCompare(b.p.name);
    })
    .map((x) => x.p);
}

function renderProjectList() {
  const list = document.getElementById("project-list");
  const meta = document.getElementById("explorer-meta");
  list.innerHTML = "";
  const items = filteredProjects();
  meta.textContent = `${items.length} of ${state.projects.length} projects`;

  if (items.length === 0) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "No projects match the current filter.";
    list.appendChild(li);
    return;
  }

  for (const p of items) {
    list.appendChild(renderProjectCard(p));
  }
}

function renderProjectCard(p) {
  const co = state.companiesBySlug.get(p.company_slug);
  const responses = state.responsesByProject.get(p.id) || [];
  const stances = new Set(responses.map((r) => r.stance));

  const li = document.createElement("li");
  li.className = "project-card";
  li.dataset.projectId = p.id;
  li.style.setProperty("--co-color", `var(--co-${p.company_slug})`);
  li.tabIndex = 0;
  li.setAttribute("role", "button");
  li.setAttribute("aria-label", `${p.name} — view details`);

  if (state.selectedProjectId === p.id) li.classList.add("active");

  const stanceDots = ["positive", "mixed", "negative"]
    .filter((s) => stances.has(s))
    .map((s) => `<span class="stance-dot ${s}" title="${STANCE_LABELS[s]} response"></span>`)
    .join("");

  li.innerHTML = `
    <p class="project-name">${escapeHtml(p.name)}</p>
    <div class="project-meta">
      <span>${escapeHtml(co ? co.name : p.company_slug)}</span>
      <span>${escapeHtml(p.city)}, ${escapeHtml(p.state)}</span>
      <span>${escapeHtml(STATUS_LABELS[p.status] || p.status)}</span>
    </div>
    ${stanceDots ? `<div class="project-stance-row">${stanceDots}</div>` : ""}
  `;

  li.addEventListener("click", () => selectProject(p.id));
  li.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      selectProject(p.id);
    }
  });
  return li;
}

// --------------------------------------------------------------------------
// Map (Leaflet, lazy-loaded)
// --------------------------------------------------------------------------

async function ensureLeaflet() {
  if (state.leafletLoaded) return;
  await Promise.all([loadCss(LEAFLET_CSS_URL), loadScript(LEAFLET_JS_URL)]);
  state.leafletLoaded = true;
}

const LEAFLET_CSS_URL = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
const LEAFLET_JS_URL = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

function loadCss(href) {
  return new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.crossOrigin = "anonymous";
    link.onload = () => resolve();
    link.onerror = () => reject(new Error("Failed to load " + href));
    document.head.appendChild(link);
  });
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.crossOrigin = "anonymous";
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Failed to load " + src));
    document.head.appendChild(s);
  });
}

function renderProjectMap() {
  const el = document.getElementById("map");
  if (!window.L) {
    el.innerHTML = `<div class="map-empty">Map library failed to load.</div>`;
    return;
  }
  if (state.map) {
    refreshMapMarkers();
    return;
  }

  state.map = L.map(el, {
    center: [38.5, -97.0],
    zoom: 4,
    minZoom: 3,
    maxZoom: 12,
    worldCopyJump: false,
    tap: false,
  });

  L.tileLayer(
    "https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 18,
      subdomains: "abcd",
    }
  ).addTo(state.map);

  refreshMapMarkers();
}

function refreshMapMarkers() {
  if (!state.map || !window.L) return;
  for (const m of state.markers.values()) state.map.removeLayer(m);
  state.markers.clear();

  const items = filteredProjects();
  for (const p of items) {
    const color = cssVar(`--co-${p.company_slug}`) || cssVar("--accent");
    const marker = L.circleMarker([p.lat, p.lon], {
      radius: 8,
      color: color,
      fillColor: color,
      fillOpacity: 0.65,
      weight: 2,
    });
    marker.bindTooltip(`${p.name}<br><small>${p.city}, ${p.state}</small>`, {
      direction: "top",
    });
    marker.on("click", () => selectProject(p.id));
    marker.addTo(state.map);
    state.markers.set(p.id, marker);
  }

  if (items.length > 0) {
    const bounds = L.latLngBounds(items.map((p) => [p.lat, p.lon]));
    state.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 7 });
  }
}

function cssVar(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

// --------------------------------------------------------------------------
// Ratepayer Protection Pledge view (v1.15)
//
// Three blocks, all derived from data already in state:
//   1. Stat tiles — signatories, post-pledge sites, site-specific commitments.
//   2. Signatory roster — who signed; non-signatory ratepayer commitments flagged.
//   3. Per-site scorecard — every signatory site announced since the pledge,
//      with its curated `project.ratepayer` assessment + evidence quote.
//
// The pledge date is read from the data (the assessed sites + a fallback const)
// rather than hard-coded in two places.
// --------------------------------------------------------------------------

const RATEPAYER_PLEDGE_DATE = "2026-03-04";
// Canonical source: the White House proclamation. The five commitments quoted
// in index.html are pulled verbatim from this page.
const RATEPAYER_PLEDGE_URL =
  "https://www.whitehouse.gov/releases/2026/03/ratepayer-protection-pledge/";

function renderRatepayerView() {
  // Pledge date + source link in the hero.
  const dateEl = document.getElementById("rp-pledge-date");
  if (dateEl) dateEl.textContent = formatLongDate(RATEPAYER_PLEDGE_DATE);
  // Both the hero link and the commitments-source link point at the canonical
  // White House proclamation.
  for (const id of ["rp-pledge-link", "rp-commitments-link"]) {
    const el = document.getElementById(id);
    if (el) el.href = RATEPAYER_PLEDGE_URL;
  }

  renderRatepayerStats();
  renderRatepayerRoster();
  renderRatepayerScorecard();
}

// Signatory companies, in roster order (signatories first, by claim presence).
function ratepayerSignatories() {
  return state.companies.filter((c) => c.ratepayer_pledge_signatory);
}

// Projects that carry a curated ratepayer assessment (the post-pledge cohort).
function ratepayerAssessedProjects() {
  return state.projects
    .filter((p) => p.ratepayer)
    .sort((a, b) => {
      // affirmed first, then by company, then name — stable, scannable order.
      const rank = (s) => RATEPAYER_STATUSES.indexOf(s);
      const d = rank(a.ratepayer.status) - rank(b.ratepayer.status);
      if (d !== 0) return d;
      if (a.company_slug !== b.company_slug)
        return a.company_slug.localeCompare(b.company_slug);
      return a.name.localeCompare(b.name);
    });
}

// Signatory sites announced before the pledge with no post-pledge commitment
// captured. Shown in a separate section beneath the assessed cohort.
function ratepayerPrePledgeProjects() {
  const signatorySlugs = new Set(ratepayerSignatories().map((c) => c.slug));
  return state.projects
    .filter((p) => signatorySlugs.has(p.company_slug) && !p.ratepayer)
    .sort((a, b) => {
      if (a.company_slug !== b.company_slug)
        return a.company_slug.localeCompare(b.company_slug);
      return a.name.localeCompare(b.name);
    });
}

// Format an announced date for display. Uses announced_date (ISO) when
// present, falling back to announced_year as a plain string.
function formatAnnouncedDate(p) {
  if (p.announced_date) return formatLongDate(p.announced_date);
  return String(p.announced_year);
}

function renderRatepayerStats() {
  const ul = document.getElementById("rp-stats");
  if (!ul) return;
  ul.innerHTML = "";

  const signatories = ratepayerSignatories();
  const assessed = ratepayerAssessedProjects();
  const affirmed = assessed.filter((p) => p.ratepayer.status === "affirmed");

  const tiles = [
    {
      value: String(signatories.length),
      label: "signatories",
    },
    {
      value: String(assessed.length),
      label: "sites tracked",
    },
    {
      value: String(affirmed.length),
      label: "site-specific commitments",
      accent: "affirmed",
    },
  ];

  for (const t of tiles) {
    const li = document.createElement("li");
    li.className = "rp-stat";
    if (t.accent) li.style.setProperty("--rp-color", `var(--ratepayer-${t.accent})`);
    li.innerHTML = `
      <span class="rp-stat-value">${escapeHtml(t.value)}</span>
      <span class="rp-stat-label">${escapeHtml(t.label)}</span>
    `;
    ul.appendChild(li);
  }
}

// Companies that did NOT sign the pledge but have at least one claim using
// ratepayer / pay-our-own-way language (e.g. QTS, Anthropic). Surfaced as a
// stat + flagged in the roster so the view doesn't imply the pledge is the
// only path to ratepayer protection.
const RATEPAYER_CLAIM_KEYWORDS = [
  "ratepayer",
  "pay our own way",
  "pay our way",
  "100% of the power",
  "100% of the cost of power",
  "100% of the energy",
  "fund 100%",
  "pay the full cost",
  "pay the full costs",
  "full costs of",
  "cover the infrastructure",
  "without raising power costs",
  "don't increase",
  "do not increase",
  "electricity prices",
];

function companyHasRatepayerClaim(slug) {
  return state.claims.some(
    (c) =>
      c.company_slug === slug &&
      RATEPAYER_CLAIM_KEYWORDS.some((k) => c.statement.toLowerCase().includes(k))
  );
}

function renderRatepayerRoster() {
  const ul = document.getElementById("rp-roster");
  if (!ul) return;
  ul.innerHTML = "";

  // Signatories first, then non-signatories who have their own commitment,
  // then the rest. Within each group, alphabetical by name.
  const signatories = ratepayerSignatories();
  const nonSigWithClaim = state.companies.filter(
    (c) => !c.ratepayer_pledge_signatory && companyHasRatepayerClaim(c.slug)
  );

  const byName = (a, b) => a.name.localeCompare(b.name);
  const ordered = [
    ...signatories.slice().sort(byName),
    ...nonSigWithClaim.slice().sort(byName),
  ];

  for (const co of ordered) {
    const signed = !!co.ratepayer_pledge_signatory;
    const li = document.createElement("li");
    li.className = `rp-roster-item${signed ? " signed" : " unsigned"}`;
    li.style.setProperty("--co-color", `var(--co-${co.slug})`);

    const noteMap = {
      qts: "Signed (DOE track)",
      anthropic: "Own commitment",
    };
    const note = signed
      ? "Signed the pledge"
      : (noteMap[co.slug] || "Own commitment");
    const mark = "✓";

    li.innerHTML = `
      <span class="rp-roster-mark" aria-hidden="true">${mark}</span>
      <span class="rp-roster-name">${escapeHtml(co.name)}</span>
      <span class="rp-roster-note">${escapeHtml(note)}</span>
    `;
    ul.appendChild(li);
  }
}

function renderRatepayerLegend() {
  const wrap = document.getElementById("rp-legend");
  if (!wrap) return;
  wrap.innerHTML = "";
  // Only show statuses that actually appear in the cohort, so the legend
  // doesn't promise a "contested" chip with no backing card (honest-absence
  // principle, same as the delivered legend).
  const present = new Set(
    ratepayerAssessedProjects().map((p) => p.ratepayer.status)
  );
  for (const status of RATEPAYER_STATUSES) {
    if (!present.has(status)) continue;
    const chip = document.createElement("span");
    chip.className = "rp-legend-chip";
    chip.style.setProperty("--rp-color", `var(--ratepayer-${status})`);
    chip.title = RATEPAYER_DESCRIPTIONS[status];
    chip.textContent = RATEPAYER_LABELS[status];
    wrap.appendChild(chip);
  }
}

// --------------------------------------------------------------------------
// CSV export
// --------------------------------------------------------------------------

function escapeCSV(val) {
  if (val == null) return "";
  const s = String(val);
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

function buildRatepayerCSV() {
  const PRINCIPLE_KEYS = [
    "new_generation",
    "delivery_infra",
    "separate_rate",
    "local_jobs",
    "grid_resilience",
  ];

  const headers = [
    "Company",
    "Project Name",
    "City",
    "State",
    "Project Status",
    "Announced Date",
    "First Pledge Reference",
    "Claimed Investment (USD)",
    "Claimed Power (MW)",
    "Acreage",
    "Claimed Jobs",
    "Water / Cooling Type",
    "Pledge Assessment",
    "Assessment Summary",
    "Evidence Source Title",
    "Evidence Source URL",
    "Assessment Date",
    "Building, bringing, or buying new power supply",
    "Paying for new power delivery infrastructure upgrades",
    "Paying whether they use the power or not",
    "Investing in local job creation and workforce development",
    "Contributing to electric and community resilience",
  ];

  const rows = [headers.map(escapeCSV).join(",")];

  // Assessed projects (post-pledge or pre-pledge with confirmed adherence).
  for (const p of ratepayerAssessedProjects()) {
    const co = state.companiesBySlug.get(p.company_slug);
    const rp = p.ratepayer;

    // Evidence source (affirmed only)
    let evidenceTitle = "";
    let evidenceUrl = "";
    if (rp.evidence_claim_id) {
      const claim = state.claims.find((c) => c.id === rp.evidence_claim_id);
      if (claim) {
        evidenceTitle = claim.source_title;
        evidenceUrl = String(claim.source_url);
      }
    }

    // Water/cooling from at_a_glance
    const waterNote = p.at_a_glance?.water || "";

    // Announced date: prefer announced_date, fall back to announced_year
    const announcedDate = p.announced_date || String(p.announced_year);

    // Per-principle: met → note text; anything else → N/A
    const principleVals = PRINCIPLE_KEYS.map((key) => {
      const assessment = rp.principles?.[key];
      if (assessment?.status === "met") return assessment.note;
      return "N/A";
    });

    const row = [
      co ? co.name : p.company_slug,
      p.name,
      p.city,
      p.state,
      p.status,
      announcedDate,
      rp.assessed_at || "",
      p.claimed_investment_usd,
      p.power_mw,
      p.acreage,
      p.claimed_jobs,
      waterNote,
      rp.status,
      rp.summary,
      evidenceTitle,
      evidenceUrl,
      rp.assessed_at,
      ...principleVals,
    ];
    rows.push(row.map(escapeCSV).join(","));
  }

  // Pre-pledge signatory sites (no assessment captured).
  for (const p of ratepayerPrePledgeProjects()) {
    const co = state.companiesBySlug.get(p.company_slug);
    const announcedDate = p.announced_date || String(p.announced_year);
    const row = [
      co ? co.name : p.company_slug,
      p.name,
      p.city,
      p.state,
      p.status,
      announcedDate,
      "", // First Pledge Reference — not captured
      p.claimed_investment_usd,
      p.power_mw,
      p.acreage,
      p.claimed_jobs,
      p.at_a_glance?.water || "",
      "pre-pledge", // Pledge Assessment
      "Announced before the pledge; no site-specific commitment captured.",
      "", "", "", // Evidence Title, URL, Assessment Date
      ...PRINCIPLE_KEYS.map(() => "N/A"),
    ];
    rows.push(row.map(escapeCSV).join(","));
  }

  return rows.join("\r\n");
}

function downloadRatepayerCSV() {
  const csv = buildRatepayerCSV();
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "ratepayer-pledge-scorecard.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function renderRatepayerScorecard() {
  const ul = document.getElementById("rp-scorecard");
  if (ul) {
    ul.innerHTML = "";
    const assessed = ratepayerAssessedProjects();
    if (assessed.length === 0) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "No assessed data centers yet.";
      ul.appendChild(li);
    } else {
      for (const p of assessed) {
        ul.appendChild(renderRatepayerCard(p));
      }
    }
  }

  // Wire export button (includes both assessed + pre-pledge rows).
  const exportBtn = document.getElementById("rp-export-csv");
  if (exportBtn) {
    exportBtn.onclick = downloadRatepayerCSV;
  }

  // Pre-pledge section.
  const prePledgeUl = document.getElementById("rp-pre-pledge");
  if (prePledgeUl) {
    prePledgeUl.innerHTML = "";
    const prePledge = ratepayerPrePledgeProjects();
    if (prePledge.length === 0) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "No pre-pledge sites found.";
      prePledgeUl.appendChild(li);
    } else {
      for (const p of prePledge) {
        prePledgeUl.appendChild(renderPrePledgeCard(p));
      }
    }
  }
}

function renderRatepayerCard(p) {
  const co = state.companiesBySlug.get(p.company_slug);
  const rp = p.ratepayer;
  const li = document.createElement("li");
  li.className = "rp-card";
  li.dataset.status = rp.status;
  li.style.setProperty("--co-color", `var(--co-${p.company_slug})`);
  li.style.setProperty("--rp-color", `var(--ratepayer-${rp.status})`);

  // Evidence quote (for `affirmed`): collapsed into a <details> so cards stay
  // compact. The summary line shows the source title as the disclosure label.
  let evidenceHtml = "";
  if (rp.evidence_claim_id) {
    const claim = state.claims.find((c) => c.id === rp.evidence_claim_id);
    if (claim) {
      evidenceHtml = `
        <details class="rp-evidence-details">
          <summary class="rp-evidence-summary">
            <a href="${escapeAttr(String(claim.source_url))}" target="_blank" rel="noopener noreferrer" class="rp-evidence-src-link">
              ${escapeHtml(claim.source_title)} →
            </a>
          </summary>
          <blockquote class="rp-evidence">${escapeHtml(claim.statement)}</blockquote>
        </details>
      `;
    }
  }

  const loc = `${escapeHtml(p.city)}, ${escapeHtml(p.state)}`;

  // X/5 met pill — count principles with status === 'met'
  const metCount = PLEDGE_PRINCIPLES.filter(
    (key) => rp.principles?.[key]?.status === "met"
  ).length;
  const metClass =
    metCount === 5 ? "met" : metCount >= 3 ? "partial" : "low";

  // Per-principle rows — one row per pledge commitment, only when data present.
  let principlesHtml = "";
  if (rp.principles && Object.keys(rp.principles).length > 0) {
    const rows = PLEDGE_PRINCIPLES.map((key) => {
      const assessment = rp.principles[key] || {};
      const status = assessment.status || "unknown";
      const note = assessment.note || "";
      const label = PLEDGE_PRINCIPLE_LABELS[key];
      const statusLabel = PLEDGE_PRINCIPLE_STATUS_LABELS[status] || status;
      const noteHtml = note
        ? `<span class="pp-row-note">${escapeHtml(note)}</span>`
        : "";
      return `<li class="pp-row pp-row--${escapeAttr(status)}">
        <div class="pp-row-body">
          <span class="pp-row-label">${escapeHtml(label)}</span>
          ${noteHtml}
        </div>
        <span class="pp-row-status">${escapeHtml(statusLabel)}</span>
      </li>`;
    }).join("");
    principlesHtml = `<ul class="rp-principles" aria-label="Pledge principles fulfillment">${rows}</ul>`;
  }

  // Date metadata row: announced date + first pledge reference.
  const announcedStr = formatAnnouncedDate(p);
  const pledgeRefStr = rp.assessed_at ? formatLongDate(rp.assessed_at) : "";
  const datesHtml = `<span class="rp-card-dates">Announced: ${escapeHtml(announcedStr)}${pledgeRefStr ? ` · First pledge ref: ${escapeHtml(pledgeRefStr)}` : ""}</span>`;

  // Collapsible card — header is always visible; body expands on click.
  li.innerHTML = `
    <details class="rp-card-details">
      <summary class="rp-card-head">
        <div class="rp-card-title">
          <span class="rp-card-company">${escapeHtml(co ? co.name : p.company_slug)}</span>
          <span class="rp-card-name">${escapeHtml(p.name)}</span>
          <span class="rp-card-loc">${loc} · ${escapeHtml(STATUS_LABELS[p.status] || p.status)}</span>
          ${datesHtml}
        </div>
        <span class="rp-met-pill rp-met-pill--${escapeAttr(metClass)}">${metCount}/5 met</span>
      </summary>
      <div class="rp-card-body">
        <p class="rp-card-summary">${escapeHtml(rp.summary)}</p>
        ${principlesHtml}
        ${evidenceHtml}
      </div>
    </details>
  `;
  return li;
}

// Compact card for pre-pledge signatory sites (no ratepayer assessment).
function renderPrePledgeCard(p) {
  const co = state.companiesBySlug.get(p.company_slug);
  const li = document.createElement("li");
  li.className = "rp-pre-card";
  li.style.setProperty("--co-color", `var(--co-${p.company_slug})`);
  const announcedStr = formatAnnouncedDate(p);
  li.innerHTML = `
    <span class="rp-pre-company">${escapeHtml(co ? co.name : p.company_slug)}</span>
    <span class="rp-pre-name">${escapeHtml(p.name)}</span>
    <span class="rp-pre-loc">${escapeHtml(p.city)}, ${escapeHtml(p.state)} · ${escapeHtml(STATUS_LABELS[p.status] || p.status)}</span>
    <span class="rp-pre-dates">Announced: ${escapeHtml(announcedStr)} · National pledge — no site assessment</span>
  `;
  return li;
}

// "2026-03-04" -> "March 4, 2026". Parsed as UTC to avoid TZ off-by-one.
function formatLongDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return iso;
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
}

// --------------------------------------------------------------------------
// Aggregate view
// --------------------------------------------------------------------------

function renderAggregateView() {
  renderAggregateStats();
  renderCompanyRollup();
  renderStateRollup();
  wireAggSort();
}

// Wire click-to-sort on all [data-sort-key] <th> in both aggregate tables.
// Called once after first render; handlers re-render the relevant tbody only.
function wireAggSort() {
  document.querySelectorAll(".agg-table th[data-sort-key]").forEach((th) => {
    if (th.dataset.sortWired) return;
    th.dataset.sortWired = "1";
    th.style.cursor = "pointer";
    th.setAttribute("role", "columnheader");
    th.addEventListener("click", () => {
      const table = th.dataset.sortTable; // "company" | "state"
      const key = th.dataset.sortKey;
      if (_aggSort[table].key === key) {
        _aggSort[table].dir *= -1; // flip direction
      } else {
        _aggSort[table].key = key;
        _aggSort[table].dir = key === "name" || key === "state" ? 1 : -1;
      }
      if (table === "company") renderCompanyRollup();
      else renderStateRollup();
      updateAggSortIndicators();
    });
  });
  updateAggSortIndicators();
}

function updateAggSortIndicators() {
  document.querySelectorAll(".agg-table th[data-sort-key]").forEach((th) => {
    const table = th.dataset.sortTable;
    const key = th.dataset.sortKey;
    const ind = th.querySelector(".sort-ind");
    if (!ind) return;
    const isCurrent = _aggSort[table].key === key;
    ind.textContent = isCurrent ? (_aggSort[table].dir === 1 ? " ▲" : " ▼") : "";
    th.setAttribute("aria-sort", isCurrent ? (_aggSort[table].dir === 1 ? "ascending" : "descending") : "none");
  });
}

function sortAggRows(rows, tableKey) {
  const { key, dir } = _aggSort[tableKey];
  return [...rows].sort((a, b) => {
    let av = key === "responses" ? (a.positive + a.mixed + a.negative) : (a[key] ?? null);
    let bv = key === "responses" ? (b.positive + b.mixed + b.negative) : (b[key] ?? null);
    // Nulls always sort last regardless of direction
    if (av === null && bv === null) return 0;
    if (av === null) return 1;
    if (bv === null) return -1;
    if (typeof av === "string") return dir * av.localeCompare(bv);
    return dir * (av - bv);
  });
}

// Build per-company rollup from state.projects + state.responses + state.claims.
function buildCompanyRollups() {
  const map = new Map();
  for (const co of state.companies) {
    map.set(co.slug, {
      slug: co.slug,
      name: co.name,
      projects: 0,
      announced: 0,
      construction: 0,
      operational: 0,
      capex: 0,
      jobs: 0,
      power_mw: 0,
      claims: 0,
      positive: 0,
      mixed: 0,
      negative: 0,
    });
  }
  for (const p of state.projects) {
    const r = map.get(p.company_slug);
    if (!r) continue;
    r.projects++;
    if (p.status === "announced") r.announced++;
    else if (p.status === "construction") r.construction++;
    else if (p.status === "operational") r.operational++;
    if (p.claimed_investment_usd) r.capex += p.claimed_investment_usd;
    if (p.claimed_jobs) r.jobs += p.claimed_jobs;
    if (p.power_mw) r.power_mw += p.power_mw;
  }
  for (const c of state.claims) {
    const r = map.get(c.company_slug);
    if (r) r.claims++;
  }
  for (const resp of state.responses) {
    const proj = state.projects.find((p) => p.id === resp.project_id);
    if (!proj) continue;
    const r = map.get(proj.company_slug);
    if (!r) continue;
    if (resp.stance === "positive") r.positive++;
    else if (resp.stance === "mixed") r.mixed++;
    else if (resp.stance === "negative") r.negative++;
  }
  return [...map.values()].filter((r) => r.projects > 0).sort((a, b) => b.capex - a.capex);
}

// Build per-state rollup.
function buildStateRollups() {
  const map = new Map();
  for (const p of state.projects) {
    if (!p.state) continue;
    if (!map.has(p.state)) {
      map.set(p.state, {
        state: p.state,
        companySlugs: new Set(),
        projects: 0,
        announced: 0,
        construction: 0,
        operational: 0,
        capex: 0,
        jobs: 0,
        power_mw: 0,
        positive: 0,
        mixed: 0,
        negative: 0,
      });
    }
    const r = map.get(p.state);
    r.companySlugs.add(p.company_slug);
    r.projects++;
    if (p.status === "announced") r.announced++;
    else if (p.status === "construction") r.construction++;
    else if (p.status === "operational") r.operational++;
    if (p.claimed_investment_usd) r.capex += p.claimed_investment_usd;
    if (p.claimed_jobs) r.jobs += p.claimed_jobs;
    if (p.power_mw) r.power_mw += p.power_mw;
  }
  for (const resp of state.responses) {
    const proj = state.projects.find((p) => p.id === resp.project_id);
    if (!proj || !proj.state) continue;
    const r = map.get(proj.state);
    if (!r) continue;
    if (resp.stance === "positive") r.positive++;
    else if (resp.stance === "mixed") r.mixed++;
    else if (resp.stance === "negative") r.negative++;
  }
  return [...map.values()]
    .map((r) => ({ ...r, companies: r.companySlugs.size }))
    .sort((a, b) => b.capex - a.capex);
}

function aggTotals(rows) {
  return rows.reduce(
    (t, r) => {
      t.capex += r.capex;
      t.jobs += r.jobs;
      t.power_mw += r.power_mw;
      t.positive += r.positive;
      t.mixed += r.mixed;
      t.negative += r.negative;
      return t;
    },
    { capex: 0, jobs: 0, power_mw: 0, positive: 0, mixed: 0, negative: 0 }
  );
}

function renderAggregateStats() {
  const ul = document.getElementById("agg-stats");
  if (!ul) return;
  ul.innerHTML = "";

  const coRows = buildCompanyRollups();
  const stRows = buildStateRollups();
  const tot = aggTotals(coRows);

  const tiles = [
    { value: formatSummaryUsd(tot.capex), label: "total claimed investment" },
    { value: tot.jobs.toLocaleString(), label: "total claimed jobs" },
    { value: formatSummaryGW(tot.power_mw), label: "total announced power" },
    { value: String(stRows.length), label: "states with projects" },
  ];

  for (const t of tiles) {
    const li = document.createElement("li");
    li.className = "rp-stat";
    li.innerHTML = `
      <span class="rp-stat-value">${escapeHtml(t.value)}</span>
      <span class="rp-stat-label">${escapeHtml(t.label)}</span>
    `;
    ul.appendChild(li);
  }
}

function stanceSpan(pos, mix, neg) {
  return (
    `<span class="stance-dot positive" title="Positive"></span>${pos} ` +
    `<span class="stance-dot mixed" title="Mixed"></span>${mix} ` +
    `<span class="stance-dot negative" title="Negative"></span>${neg}`
  );
}

function fmtJobs(n) {
  return n ? n.toLocaleString() : "—";
}

function renderCompanyRollup() {
  const tbody = document.getElementById("agg-company-tbody");
  const tfoot = document.getElementById("agg-company-tfoot");
  if (!tbody || !tfoot) return;

  const rows = sortAggRows(buildCompanyRollups(), "company");
  const tot = aggTotals(rows);

  tbody.innerHTML = rows
    .map(
      (r) => `<tr>
      <td class="name-col">
        <span class="co-dot" style="background:var(--co-${escapeAttr(r.slug)})"></span>
        ${escapeHtml(r.name)}
      </td>
      <td class="num">
        ${r.projects}
        <span class="agg-status-pills">
          ${r.announced ? `<span class="agg-pill announced">${r.announced}A</span>` : ""}
          ${r.construction ? `<span class="agg-pill construction">${r.construction}C</span>` : ""}
          ${r.operational ? `<span class="agg-pill operational">${r.operational}O</span>` : ""}
        </span>
      </td>
      <td class="num">${r.power_mw ? formatSummaryGW(r.power_mw) : "—"}</td>
      <td class="num">${r.capex ? formatSummaryUsd(r.capex) : "—"}</td>
      <td class="num">${fmtJobs(r.jobs)}</td>
      <td class="num">${r.claims}</td>
      <td class="num responses-col">${stanceSpan(r.positive, r.mixed, r.negative)}</td>
    </tr>`
    )
    .join("");

  tfoot.innerHTML = `<tr class="agg-total-row">
    <td class="name-col"><strong>Total</strong></td>
    <td class="num"><strong>${rows.reduce((s, r) => s + r.projects, 0)}</strong></td>
    <td class="num"><strong>${formatSummaryGW(tot.power_mw)}</strong></td>
    <td class="num"><strong>${formatSummaryUsd(tot.capex)}</strong></td>
    <td class="num"><strong>${tot.jobs.toLocaleString()}</strong></td>
    <td class="num"><strong>${rows.reduce((s, r) => s + r.claims, 0)}</strong></td>
    <td class="num responses-col">${stanceSpan(tot.positive, tot.mixed, tot.negative)}</td>
  </tr>`;
}

function renderStateRollup() {
  const tbody = document.getElementById("agg-state-tbody");
  const tfoot = document.getElementById("agg-state-tfoot");
  if (!tbody || !tfoot) return;

  const rows = sortAggRows(buildStateRollups(), "state");
  const tot = aggTotals(rows);

  tbody.innerHTML = rows
    .map(
      (r) => `<tr>
      <td class="name-col">${escapeHtml(r.state)}</td>
      <td class="num">${r.companies}</td>
      <td class="num">
        ${r.projects}
        <span class="agg-status-pills">
          ${r.announced ? `<span class="agg-pill announced">${r.announced}A</span>` : ""}
          ${r.construction ? `<span class="agg-pill construction">${r.construction}C</span>` : ""}
          ${r.operational ? `<span class="agg-pill operational">${r.operational}O</span>` : ""}
        </span>
      </td>
      <td class="num">${r.power_mw ? formatSummaryGW(r.power_mw) : "—"}</td>
      <td class="num">${r.capex ? formatSummaryUsd(r.capex) : "—"}</td>
      <td class="num">${fmtJobs(r.jobs)}</td>
      <td class="num responses-col">${stanceSpan(r.positive, r.mixed, r.negative)}</td>
    </tr>`
    )
    .join("");

  tfoot.innerHTML = `<tr class="agg-total-row">
    <td class="name-col"><strong>Total</strong></td>
    <td class="num"><strong>${new Set(state.projects.map((p) => p.company_slug)).size}</strong></td>
    <td class="num"><strong>${rows.reduce((s, r) => s + r.projects, 0)}</strong></td>
    <td class="num"><strong>${formatSummaryGW(tot.power_mw)}</strong></td>
    <td class="num"><strong>${formatSummaryUsd(tot.capex)}</strong></td>
    <td class="num"><strong>${tot.jobs.toLocaleString()}</strong></td>
    <td class="num responses-col">${stanceSpan(tot.positive, tot.mixed, tot.negative)}</td>
  </tr>`;
}

// --------------------------------------------------------------------------
// Project detail
// --------------------------------------------------------------------------

function selectProject(id) {
  const p = state.projects.find((x) => x.id === id);
  if (!p) return;
  state.selectedProjectId = id;
  const co = state.companiesBySlug.get(p.company_slug);

  const detail = document.getElementById("project-detail");
  detail.style.setProperty("--co-color", `var(--co-${p.company_slug})`);
  document.getElementById("d-company").textContent = co ? co.name : p.company_slug;
  document.getElementById("d-name").textContent = p.name;
  document.getElementById("d-location").textContent = `${p.city}, ${p.state}`;
  document.getElementById("d-status").textContent =
    STATUS_LABELS[p.status] || p.status;
  document.getElementById("d-year").textContent = p.announced_year;

  setKv("d-investment", formatUsd(p.claimed_investment_usd));
  setKv("d-jobs", p.claimed_jobs == null ? null : p.claimed_jobs.toLocaleString());
  setKv("d-acreage", formatAcreage(p.acreage));
  setKv("d-power", formatPower(p.power_mw));
  setKv("d-gpus", formatGpuCount(p.gpu_count));
  setKv("d-offtaker", p.offtaker || null);
  setKvLink(
    "d-project-page",
    p.project_page_url,
    p.project_page_url ? `${p.name} (official)` : null
  );
  setKvLink("d-source", p.source_url, p.source_title);
  setKv("d-notes", p.notes || null);

  const claimsCount = renderProjectClaims(p);
  const responsesCount = renderProjectResponses(p);
  updateDetailTabCounts(claimsCount, responsesCount);
  renderAtAGlance(p);
  resetDetailTabs();

  detail.hidden = false;
  // Focus management: move focus to the close button so screen readers
  // announce the panel.
  document.getElementById("detail-close").focus({ preventScroll: true });

  refreshProjectListSelection();
  writeFiltersToUrl();

  detail.scrollIntoView({ behavior: "smooth", block: "start" });
}

function refreshProjectListSelection() {
  document
    .querySelectorAll("#project-list .project-card.active")
    .forEach((el) => el.classList.remove("active"));
  if (!state.selectedProjectId) return;
  const el = document.querySelector(
    `#project-list .project-card[data-project-id="${state.selectedProjectId}"]`
  );
  if (el) el.classList.add("active");
}

function setKv(id, value) {
  const el = document.getElementById(id);
  if (value == null || value === "") {
    el.textContent = "Not disclosed";
    el.classList.add("muted-cell");
  } else {
    el.textContent = value;
    el.classList.remove("muted-cell");
  }
}

function setKvLink(id, href, title) {
  const el = document.getElementById(id);
  if (!href) {
    el.textContent = "—";
    el.classList.add("muted-cell");
    return;
  }
  el.classList.remove("muted-cell");
  el.innerHTML = `<a href="${escapeAttr(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
    title || href
  )}</a>`;
}

function formatUsd(v) {
  if (v == null) return null;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${v.toLocaleString()}`;
}

function formatAcreage(v) {
  if (v == null) return null;
  // Round to whole acres for display; preserve decimals only below 10.
  const rounded = v >= 10 ? Math.round(v) : Math.round(v * 10) / 10;
  return `${rounded.toLocaleString()} acres`;
}

function formatPower(v) {
  if (v == null) return null;
  // Express ≥1000 MW as GW for legibility (Wonder Valley territory).
  if (v >= 1000) return `${(v / 1000).toFixed(1)} GW`;
  return `${v.toLocaleString()} MW`;
}

function formatGpuCount(v) {
  if (v == null) return null;
  // Round large counts: 450,000 → "450K", 1,200,000 → "1.2M".
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return v.toLocaleString();
}

// --------------------------------------------------------------------------
// At-a-glance: per-theme summary on the project Overview tab.
// Curator-written `project.at_a_glance` (theme → string) wins; otherwise
// auto-derive a one-liner from the project's project-tied claims.
// --------------------------------------------------------------------------

function renderAtAGlance(p) {
  const section = document.getElementById("d-at-a-glance");
  const list = document.getElementById("d-at-a-glance-list");
  list.innerHTML = "";

  const summaries = buildAtAGlanceSummaries(p);
  if (summaries.length === 0) {
    section.hidden = true;
    return;
  }
  section.hidden = false;

  for (const { theme, text, isCurated } of summaries) {
    const li = document.createElement("li");
    li.className = "at-a-glance-row";
    li.innerHTML = `
      <span class="at-a-glance-theme" style="--theme-color: var(--theme-${theme});">
        ${escapeHtml(THEME_LABELS[theme] || theme)}
      </span>
      <span class="at-a-glance-text${isCurated ? " curator-override" : ""}">
        ${escapeHtml(text)}
      </span>
    `;
    list.appendChild(li);
  }
}

function buildAtAGlanceSummaries(p) {
  // 1. Group project-tied claims by theme.
  const projectClaims = state.claimsByProject.get(p.id) || [];
  const byTheme = new Map();
  for (const c of projectClaims) {
    if (!byTheme.has(c.theme)) byTheme.set(c.theme, []);
    byTheme.get(c.theme).push(c);
  }

  // 2. For each canonical theme (in canonical order), build a one-liner.
  // Curator override (project.at_a_glance) WINS over auto-derivation.
  const curated = p.at_a_glance || {};
  const out = [];
  for (const theme of THEMES) {
    if (curated[theme]) {
      out.push({ theme, text: curated[theme], isCurated: true });
      continue;
    }
    const claims = byTheme.get(theme);
    if (!claims || claims.length === 0) continue;
    out.push({ theme, text: autoSummarizeClaims(claims), isCurated: false });
  }
  return out;
}

function autoSummarizeClaims(claims) {
  // Prefer the highest-signal metric across the theme's claims.
  const withMetric = claims.filter((c) => c.metric);
  if (withMetric.length > 0) {
    // Show up to 2 metric strings joined by " · ".
    const top = withMetric.slice(0, 2).map((c) => formatMetric(c.metric));
    return top.join(" · ");
  }
  // Fall back to a truncated first claim's statement.
  const stmt = claims[0].statement;
  const max = 90;
  return stmt.length > max ? stmt.slice(0, max).trim() + "…" : stmt;
}

function renderProjectClaims(p) {
  const ol = document.getElementById("d-claims");
  ol.innerHTML = "";

  // Claims tied directly to this project + claims tied at company level.
  const direct = state.claimsByProject.get(p.id) || [];
  const companyLevel = state.claims.filter(
    (c) => c.company_slug === p.company_slug && !c.project_id
  );
  const all = [...direct, ...companyLevel];

  if (all.length === 0) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "No claims captured for this site or company.";
    ol.appendChild(li);
    return 0;
  }

  for (const c of all) ol.appendChild(renderClaimCard(c));
  return all.length;
}

function renderProjectResponses(p) {
  const ol = document.getElementById("d-responses");
  ol.innerHTML = "";
  const items = state.responsesByProject.get(p.id) || [];
  if (items.length === 0) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "No community responses captured for this site yet.";
    ol.appendChild(li);
    return 0;
  }
  for (const r of items) ol.appendChild(renderResponseCard(r));
  return items.length;
}

function renderResponseCard(r) {
  const li = document.createElement("li");
  li.className = `response-card ${r.stance}`;
  li.dataset.responseId = r.id;

  const meta = document.createElement("div");
  meta.className = "response-meta";
  meta.innerHTML = `
    <span class="response-stance">${escapeHtml(STANCE_LABELS[r.stance] || r.stance)}</span>
    <span>${escapeHtml(CONSTITUENCY_LABELS[r.constituency] || r.constituency)}</span>
    <span>${escapeHtml(r.date)}</span>
    ${r.single_source ? `<span class="badge-single-source" title="Only one source documents this">single source</span>` : ""}
  `;

  const summary = document.createElement("p");
  summary.className = "response-summary";
  summary.textContent = r.summary;

  const src = document.createElement("p");
  src.className = "response-source";
  const respHref = escapeAttr(r.wayback_url || r.source_url);
  const respLabel = r.wayback_url
    ? `${escapeHtml(r.source_title)} (archived)`
    : escapeHtml(r.source_title);
  src.innerHTML = `Source: <a href="${respHref}" target="_blank" rel="noopener noreferrer">${respLabel}</a>`;

  li.appendChild(meta);
  li.appendChild(summary);
  li.appendChild(src);
  return li;
}

function closeDetail() {
  state.selectedProjectId = null;
  state.pendingProjectId = null;
  document.getElementById("project-detail").hidden = true;
  refreshProjectListSelection();
  writeFiltersToUrl();
}

// --------------------------------------------------------------------------
// Helpers
// --------------------------------------------------------------------------

function escapeHtml(s) {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttr(s) {
  return escapeHtml(s);
}

function showToast(message, ms = 2400) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.add("visible");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.remove("visible"), ms);
}

// Expose a tiny API for tests / debugging without polluting the global
// namespace at first paint. The Explorer view also exposes window.__dcb.
window.__dcb_ready = new Promise((resolve) => {
  document.addEventListener("dcb:explorer-ready", () => resolve(window.__dcb), {
    once: true,
  });
});

// Surface canonical vocabularies for the parity test that compares to
// schema.py.
window.__DCB_CONST = {
  THEMES,
  THEME_LABELS,
  COMPANY_SLUGS,
  STANCE_LABELS,
  CONSTITUENCY_LABELS,
  STATUS_LABELS,
  DELIVERED_STATUSES,
  DELIVERED_LABELS,
  RATEPAYER_STATUSES,
  RATEPAYER_LABELS,
};

// Resolve a second readiness promise once the Ratepayer view has rendered, so
// e2e tests can await it the same way they await the Explorer.
window.__dcb_ratepayer_ready = new Promise((resolve) => {
  document.addEventListener(
    "dcb:ratepayer-ready",
    () => resolve({ state, ratepayerAssessedProjects, ratepayerSignatories }),
    { once: true }
  );
});
