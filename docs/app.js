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
  "nebius",
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
  new_generation: "New power supply",
  delivery_infra: "Grid upgrade costs",
  separate_rate: "Pay-whether-used",
  local_jobs: "Local jobs & workforce",
  grid_resilience: "Grid resilience",
};
const PLEDGE_PRINCIPLE_DESCRIPTIONS = {
  new_generation:
    "Building, bringing, or buying new generation — paying the full cost of new power needed.",
  delivery_infra:
    "Paying for all transmission and distribution infrastructure upgrades.",
  separate_rate:
    "Negotiating separate rate structures and paying those rates, used or not.",
  local_jobs:
    "Hiring locally and building skills-development programs in the community.",
  grid_resilience:
    "Coordinating with grid operators; making backup power available during scarcity.",
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
];

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
    document.getElementById(v.tab).setAttribute("aria-selected", String(isActive));
    document.getElementById(v.section).hidden = !isActive;
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
  const c = state.claims.length;
  const co = state.companies.length;
  document.getElementById("meta").textContent = `${c} claims across ${co} companies · v0 curated`;
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
      }
      tr.appendChild(td);
    }

    body.appendChild(tr);
  }
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
  `;

  const quote = document.createElement("p");
  quote.className = "claim-quote";
  quote.textContent = c.statement;

  const source = document.createElement("p");
  source.className = "claim-source";
  source.innerHTML = `Source: <a href="${escapeAttr(c.source_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
    c.source_title
  )}</a>`;

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
  renderRatepayerLegend();
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
      label: "companies signed the pledge",
    },
    {
      value: String(assessed.length),
      label: "data centers announced since the pledge",
    },
    {
      value: String(affirmed.length),
      label: "carry a site-specific ratepayer commitment",
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

    const note = signed
      ? "Signed the pledge"
      : "Own ratepayer commitment (not a pledge signatory)";
    const mark = signed ? "✓" : "○";

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

function renderRatepayerScorecard() {
  const ul = document.getElementById("rp-scorecard");
  if (!ul) return;
  ul.innerHTML = "";

  const projects = ratepayerAssessedProjects();
  if (projects.length === 0) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "No assessed data centers yet.";
    ul.appendChild(li);
    return;
  }

  for (const p of projects) {
    ul.appendChild(renderRatepayerCard(p));
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

  // Evidence quote (for `affirmed`): pull the cited claim's verbatim statement.
  let evidenceHtml = "";
  if (rp.evidence_claim_id) {
    const claim = state.claims.find((c) => c.id === rp.evidence_claim_id);
    if (claim) {
      evidenceHtml = `
        <blockquote class="rp-evidence">${escapeHtml(claim.statement)}</blockquote>
        <p class="rp-evidence-src">
          <a href="${escapeAttr(String(claim.source_url))}" target="_blank" rel="noopener noreferrer">
            ${escapeHtml(claim.source_title)} →
          </a>
        </p>
      `;
    }
  }

  const loc = `${escapeHtml(p.city)}, ${escapeHtml(p.state)}`;
  const statusLabel = RATEPAYER_LABELS[rp.status] || rp.status;

  // Per-principle rows — one row per pledge commitment, only when data present.
  let principlesHtml = "";
  if (rp.principles && Object.keys(rp.principles).length > 0) {
    const rows = PLEDGE_PRINCIPLES.map((key) => {
      const status = rp.principles[key] || "unknown";
      const label = PLEDGE_PRINCIPLE_LABELS[key];
      const statusLabel = PLEDGE_PRINCIPLE_STATUS_LABELS[status] || status;
      const principleDesc = PLEDGE_PRINCIPLE_DESCRIPTIONS[key] || "";
      const tooltip = escapeAttr(`${principleDesc}`);
      return `<li class="pp-row pp-row--${escapeAttr(status)}" title="${tooltip}">
        <span class="pp-row-label">${escapeHtml(label)}</span>
        <span class="pp-row-status">${escapeHtml(statusLabel)}</span>
      </li>`;
    }).join("");
    principlesHtml = `<ul class="rp-principles" aria-label="Pledge principles fulfillment">${rows}</ul>`;
  }

  li.innerHTML = `
    <div class="rp-card-head">
      <div class="rp-card-title">
        <span class="rp-card-company">${escapeHtml(co ? co.name : p.company_slug)}</span>
        <span class="rp-card-name">${escapeHtml(p.name)}</span>
        <span class="rp-card-loc">${loc} · ${escapeHtml(STATUS_LABELS[p.status] || p.status)}</span>
      </div>
      <span class="rp-status-badge" title="${escapeAttr(RATEPAYER_DESCRIPTIONS[rp.status] || "")}">
        ${escapeHtml(statusLabel)}
      </span>
    </div>
    <p class="rp-card-summary">${escapeHtml(rp.summary)}</p>
    ${principlesHtml}
    ${evidenceHtml}
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
  src.innerHTML = `Source: <a href="${escapeAttr(r.source_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
    r.source_title
  )}</a>`;

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
