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
  matrixFilter: null, // { companySlug?, theme? } | null
  explorerFilters: { company: "", status: "", stance: "" },
  selectedProjectId: null,
  explorerLoaded: false,
  leafletLoaded: false,
  map: null,
  markers: new Map(),
};

// --------------------------------------------------------------------------
// Boot
// --------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  applyStoredTheme();
  wireThemeToggle();
  wireTabs();
  loadComparisonData().catch((err) => {
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

function wireTabs() {
  const tabComparison = document.getElementById("tab-comparison");
  const tabExplorer = document.getElementById("tab-explorer");

  tabComparison.addEventListener("click", () => activateView("comparison"));
  tabExplorer.addEventListener("click", () => activateView("explorer"));

  // Allow URL hash to deep-link to explorer view.
  if (window.location.hash === "#explorer") {
    activateView("explorer");
  }
}

function activateView(name) {
  state.activeView = name;

  const tabComp = document.getElementById("tab-comparison");
  const tabExpl = document.getElementById("tab-explorer");
  const viewComp = document.getElementById("view-comparison");
  const viewExpl = document.getElementById("view-explorer");

  if (name === "comparison") {
    tabComp.setAttribute("aria-selected", "true");
    tabExpl.setAttribute("aria-selected", "false");
    viewComp.hidden = false;
    viewExpl.hidden = true;
    if (window.location.hash === "#explorer") {
      history.replaceState(null, "", window.location.pathname);
    }
  } else {
    tabComp.setAttribute("aria-selected", "false");
    tabExpl.setAttribute("aria-selected", "true");
    viewComp.hidden = true;
    viewExpl.hidden = false;
    history.replaceState(null, "", "#explorer");
    if (!state.explorerLoaded) {
      loadExplorerData().catch((err) => {
        console.error("Failed to load explorer data:", err);
        document.getElementById("explorer-meta").textContent =
          "Failed to load projects.";
      });
    }
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
}

async function loadExplorerData() {
  document.getElementById("explorer-meta").textContent = "Loading projects…";
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

  await ensureLeaflet();
  state.explorerLoaded = true;
  renderExplorerView();

  // Expose for e2e/debugging.
  window.__dcb = { state, THEMES, selectProject };
  document.dispatchEvent(new CustomEvent("dcb:explorer-ready"));
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
  renderClaimsList();
  renderClaimsFilterChips();
}

function renderMeta() {
  const c = state.claims.length;
  const co = state.companies.length;
  document.getElementById("meta").textContent = `${c} claims across ${co} companies · v0 curated`;
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

    const nameCell = document.createElement("th");
    nameCell.className = "col-company";
    nameCell.scope = "row";
    nameCell.style.setProperty("--co-color", `var(--co-${co.slug})`);
    nameCell.innerHTML = `
      <span class="company-name">
        <span class="company-dot" aria-hidden="true"></span>
        ${escapeHtml(co.name)}
      </span>
    `;
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
        // Single claim → checkmark glyph (binary "they have a claim" signal).
        // Multiple claims → numeric count (volume signal). Either way the
        // aria-label carries the precise count for screen readers.
        if (n === 1) {
          td.innerHTML = `<span class="count check" aria-hidden="true">✓</span>`;
        } else {
          td.innerHTML = `<span class="count">${n}</span>`;
        }
        td.setAttribute("role", "button");
        td.tabIndex = 0;
        td.setAttribute(
          "aria-label",
          `${n} ${co.name} ${THEME_LABELS[t]} claim${n === 1 ? "" : "s"} — click to filter`
        );
        td.addEventListener("click", () => onMatrixCellClick(co.slug, t));
        td.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onMatrixCellClick(co.slug, t);
          }
        });
      }
      tr.appendChild(td);
    }

    body.appendChild(tr);
  }
}

function onMatrixCellClick(companySlug, theme) {
  const cur = state.matrixFilter;
  if (cur && cur.companySlug === companySlug && cur.theme === theme) {
    state.matrixFilter = null;
  } else {
    state.matrixFilter = { companySlug, theme };
  }
  renderMatrix();
  highlightActiveCell();
  renderClaimsList();
  renderClaimsFilterChips();
  document
    .getElementById("claims-heading")
    .scrollIntoView({ behavior: "smooth", block: "start" });
}

function highlightActiveCell() {
  document
    .querySelectorAll("#comparison-matrix .cell.active")
    .forEach((el) => el.classList.remove("active"));
  if (!state.matrixFilter) return;
  const { companySlug, theme } = state.matrixFilter;
  const cell = document.querySelector(
    `#comparison-matrix td[data-company="${companySlug}"][data-theme="${theme}"]`
  );
  if (cell) cell.classList.add("active");
}

function renderClaimsList() {
  const list = document.getElementById("claims-list");
  list.innerHTML = "";

  const filtered = state.claims.filter((c) => {
    if (!state.matrixFilter) return true;
    const f = state.matrixFilter;
    if (f.companySlug && c.company_slug !== f.companySlug) return false;
    if (f.theme && c.theme !== f.theme) return false;
    return true;
  });

  if (filtered.length === 0) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "No claims match the current filter.";
    list.appendChild(li);
    return;
  }

  for (const c of filtered) {
    list.appendChild(renderClaimCard(c));
  }
}

function renderClaimCard(c) {
  const co = state.companiesBySlug.get(c.company_slug);
  const li = document.createElement("li");
  li.className = "claim-card";
  li.dataset.claimId = c.id;
  li.style.setProperty("--co-color", `var(--co-${c.company_slug})`);

  const meta = document.createElement("div");
  meta.className = "claim-meta";
  meta.innerHTML = `
    <span class="claim-company">${escapeHtml(co ? co.name : c.company_slug)}</span>
    <span class="claim-theme" style="--theme-color: var(--theme-${c.theme});">
      ${escapeHtml(THEME_LABELS[c.theme] || c.theme)}
    </span>
    <span>${escapeHtml(c.captured_at)}</span>
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
  return li;
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

function renderClaimsFilterChips() {
  const row = document.getElementById("claims-filter");
  row.innerHTML = "";
  if (!state.matrixFilter) return;

  const f = state.matrixFilter;
  const co = state.companiesBySlug.get(f.companySlug);
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "chip chip-clear";
  chip.innerHTML = `Filter: ${escapeHtml(co ? co.name : f.companySlug)} × ${escapeHtml(
    THEME_LABELS[f.theme] || f.theme
  )} <span aria-hidden="true">×</span>`;
  chip.setAttribute("aria-label", "Clear filter");
  chip.addEventListener("click", () => {
    state.matrixFilter = null;
    renderMatrix();
    highlightActiveCell();
    renderClaimsList();
    renderClaimsFilterChips();
  });
  row.appendChild(chip);
}

// --------------------------------------------------------------------------
// Explorer view rendering
// --------------------------------------------------------------------------

function renderExplorerView() {
  populateCompanyFilter();
  wireExplorerFilters();
  renderProjectList();
  renderProjectMap();
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

function wireExplorerFilters() {
  document.getElementById("f-company").addEventListener("change", (e) => {
    state.explorerFilters.company = e.target.value;
    refreshExplorer();
  });
  document.getElementById("f-status").addEventListener("change", (e) => {
    state.explorerFilters.status = e.target.value;
    refreshExplorer();
  });
  document.getElementById("f-stance").addEventListener("change", (e) => {
    state.explorerFilters.stance = e.target.value;
    refreshExplorer();
  });
  document.getElementById("f-reset").addEventListener("click", () => {
    state.explorerFilters = { company: "", status: "", stance: "" };
    document.getElementById("f-company").value = "";
    document.getElementById("f-status").value = "";
    document.getElementById("f-stance").value = "";
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
}

function filteredProjects() {
  const f = state.explorerFilters;
  return state.projects.filter((p) => {
    if (f.company && p.company_slug !== f.company) return false;
    if (f.status && p.status !== f.status) return false;
    if (f.stance) {
      const rs = state.responsesByProject.get(p.id) || [];
      if (!rs.some((r) => r.stance === f.stance)) return false;
    }
    return true;
  });
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
  resetDetailTabs();

  detail.hidden = false;
  // Focus management: move focus to the close button so screen readers
  // announce the panel.
  document.getElementById("detail-close").focus({ preventScroll: true });

  refreshProjectListSelection();

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
  document.getElementById("project-detail").hidden = true;
  refreshProjectListSelection();
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
};
