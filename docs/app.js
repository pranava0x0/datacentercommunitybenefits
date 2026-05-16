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
  explorerFilters: { company: "", status: "", stance: "" },
  explorerSort: "composite",
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
  wireCompanyDetail();
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

// --------------------------------------------------------------------------
// Explorer view rendering
// --------------------------------------------------------------------------

function renderExplorerView() {
  populateCompanyFilter();
  wireExplorerFilters();
  syncExplorerFilterUIToState();
  renderProjectList();
  renderProjectMap();
}

function syncExplorerFilterUIToState() {
  const f = state.explorerFilters;
  const co = document.getElementById("f-company");
  const st = document.getElementById("f-status");
  const sn = document.getElementById("f-stance");
  const so = document.getElementById("f-sort");
  if (co) co.value = f.company || "";
  if (st) st.value = f.status || "";
  if (sn) sn.value = f.stance || "";
  if (so) so.value = state.explorerSort || "composite";
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
  const sortSel = document.getElementById("f-sort");
  if (sortSel) {
    sortSel.addEventListener("change", (e) => {
      const v = e.target.value;
      state.explorerSort = SORT_OPTIONS.includes(v) ? v : "composite";
      renderProjectList();
    });
  }
  document.getElementById("f-reset").addEventListener("click", () => {
    state.explorerFilters = { company: "", status: "", stance: "" };
    state.explorerSort = "composite";
    document.getElementById("f-company").value = "";
    document.getElementById("f-status").value = "";
    document.getElementById("f-stance").value = "";
    if (sortSel) sortSel.value = "composite";
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
  const items = state.projects.filter((p) => {
    if (f.company && p.company_slug !== f.company) return false;
    if (f.status && p.status !== f.status) return false;
    if (f.stance) {
      const rs = state.responsesByProject.get(p.id) || [];
      if (!rs.some((r) => r.stance === f.stance)) return false;
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
