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

const MORATORIUM_STATUSES = ["enacted", "proposed", "failed"];
const MORATORIUM_REASON_TYPES = [
  "energy",
  "water",
  "air_quality",
  "noise",
  "transparency",
  "equity",
];
const MORATORIUM_REASON_LABELS = {
  energy: "Grid & Power",
  water: "Water & Depletion",
  air_quality: "Air Quality",
  noise: "Noise & Turbines",
  transparency: "Community Process & Transparency",
  equity: "Ratepayer Protection",
};

// v1.17: State large-load utility tariff vocabulary. Must mirror
// schema.TARIFF_STATUSES / TARIFF_PARAMETERS / TARIFF_PARAMETER_* exactly;
// `test_tariff_constants_match_frontend` enforces parity.
const TARIFF_STATUSES = ["approved", "proposed", "rejected"];
const TARIFF_STATUS_LABELS = {
  approved: "Approved",
  proposed: "Proposed",
  rejected: "Rejected / Withdrawn",
};
// The five LBL element groups, in the brief's order: [group_key, label].
const TARIFF_PARAMETER_GROUPS = [
  ["eligibility", "Eligibility & Applicability"],
  ["contract_size", "Contract Size"],
  ["duration", "Contract Duration & Exit"],
  ["energy_source", "Energy Source"],
  ["other", "Other Elements"],
];
// The 17 large-load rate-design elements from the LBL brief, in order.
const TARIFF_PARAMETERS = [
  "min_load",
  "monthly_demand_charge",
  "customer_type",
  "study_cost_recovery",
  "credit_collateral",
  "contracted_capacity",
  "resize_reassign",
  "btm_backup",
  "load_factor",
  "contract_duration",
  "ramp_times",
  "duration_flexibility",
  "exit_fee",
  "clean_energy",
  "specific_generation",
  "marginal_pricing",
  "econ_dev_payments",
];
const TARIFF_PARAMETER_LABELS = {
  min_load: "Minimum load requirement",
  monthly_demand_charge: "Minimum demand charge",
  customer_type: "Customer-type applicability",
  study_cost_recovery: "Study-cost recovery",
  credit_collateral: "Credit rating / collateral",
  contracted_capacity: "Contracted capacity & energy",
  resize_reassign: "Resizing / reassignment",
  btm_backup: "Behind-the-meter backup",
  load_factor: "Minimum load factor",
  contract_duration: "Contract duration",
  ramp_times: "Ramp times",
  duration_flexibility: "Duration flexibility",
  exit_fee: "Exit fee",
  clean_energy: "Clean-energy requirements",
  specific_generation: "Specific generation technologies",
  marginal_pricing: "Marginal pricing / cost-sharing",
  econ_dev_payments: "Economic-development payments",
};
const TARIFF_PARAMETER_DESCRIPTIONS = {
  min_load: "A lower-bound MW load threshold to qualify for the tariff.",
  monthly_demand_charge: "Minimum charge tied to a percentage of forecasted maximum demand.",
  customer_type: "Tariff scoped to a specific large-load customer type (e.g., data centers).",
  study_cost_recovery: "Customer pays for interconnection / system-impact studies.",
  credit_collateral: "Minimum credit rating and/or collateral / deposit requirements.",
  contracted_capacity: "Defined MW / MWh the customer is obligated to buy.",
  resize_reassign: "Terms to resize, reassign, or sell unused contracted capacity / energy.",
  btm_backup: "Treatment of behind-the-meter generation / storage as backup or supplemental power.",
  load_factor: "A minimum average-to-peak load ratio the customer must maintain.",
  contract_duration: "Minimum contract term to back long-lived utility investment.",
  ramp_times: "An extended period to reach full contracted load.",
  duration_flexibility: "Modifications / renewals to the contract term.",
  exit_fee: "Charge for exiting the tariff or terminating service early.",
  clean_energy: "Requirements / options to serve the load with clean or renewable energy.",
  specific_generation: "Utility procures specific named generation on the customer's behalf.",
  marginal_pricing: "Marginal-cost pricing / cost-sharing to limit cross-subsidization.",
  econ_dev_payments: "Direct payments for workforce, community, or low-income programs.",
};
// Maps each parameter key to its group key (for grouped rendering).
const TARIFF_PARAMETER_GROUP_OF = {
  min_load: "eligibility",
  monthly_demand_charge: "eligibility",
  customer_type: "eligibility",
  study_cost_recovery: "eligibility",
  credit_collateral: "eligibility",
  contracted_capacity: "contract_size",
  resize_reassign: "contract_size",
  btm_backup: "contract_size",
  load_factor: "contract_size",
  contract_duration: "duration",
  ramp_times: "duration",
  duration_flexibility: "duration",
  exit_fee: "duration",
  clean_energy: "energy_source",
  specific_generation: "energy_source",
  marginal_pricing: "other",
  econ_dev_payments: "other",
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
// VERBATIM commitment text from the White House pledge. The band's own footnote
// tells the reader these are quoted, and the project's editorial rule is
// quote-don't-paraphrase — so these are the source's sentences, not summaries.
//
// They were paraphrases until 2026-07-28, and two of the paraphrases were
// materially wrong in the direction that flatters the pledge:
//   separate_rate  — asserted companies pay "for the power and infrastructure
//                    brought online, used or not". The source body says only
//                    that they will negotiate separate rate structures; the
//                    pay-anyway framing is the section's TITLE, not a
//                    commitment the body makes. We were quoting the headline
//                    back as if it were the text.
//   grid_resilience — dropped the source's "whenever possible" hedge on backup
//                    generation, which made a qualified commitment read as
//                    unconditional.
// Don't re-tighten these into snappier lines. If they need shortening for a
// layout, shorten the LAYOUT — PLEDGE_PRINCIPLE_SHORT already exists for that.
const PLEDGE_PRINCIPLE_DESCRIPTIONS = {
  new_generation:
    "Companies will build, bring, or buy the new generation resources and electricity needed to satisfy their new energy demands, paying the full cost of those resources whether by building, or buying from, new or otherwise additive power plants.",
  delivery_infra:
    "Companies will pay for all new power delivery infrastructure upgrades required to service their data centers, including adequate network upgrade costs to ensure that these expenses are not passed on to the ordinary household.",
  separate_rate:
    "Companies will voluntarily negotiate new, separate rate structures with their utilities and relevant State governments wherever they build data centers.",
  local_jobs:
    "Companies will invest in the local communities in which they build data centers. This includes hiring from within the local community and establishing programs to develop relevant skills.",
  grid_resilience:
    "Companies will coordinate with grid operators to contribute to a more reliable grid and, whenever possible, make available their backup generation resources at times of scarcity to prevent blackouts and power shortages in their communities.",
};
// Short forms for the landing-page meters, where the full label wraps to three
// lines and stops being scannable. Purely presentational — the full label is
// what renders anywhere the commitment is actually being quoted.
const PLEDGE_PRINCIPLE_SHORT = {
  new_generation: "New power supply",
  delivery_infra: "Delivery infrastructure",
  separate_rate: "Pay used or not",
  local_jobs: "Local jobs",
  grid_resilience: "Grid resilience",
};
const PLEDGE_PRINCIPLE_STATUSES = ["met", "partial", "not_met", "unknown"];
const PLEDGE_PRINCIPLE_STATUS_LABELS = {
  met: "Met",
  partial: "Partial / Pledge only",
  not_met: "Not met",
  unknown: "Not assessed",
};
// The eight pledge signatories: seven signed at the White House (2026-03-04),
// QTS signed via the DOE companion track (2026-04-24). Mirrors the
// ratepayer_pledge_signatory=true rows in companies.json; used only as a
// fallback ordering hint — the live truth is read from the company records.
const RATEPAYER_PLEDGE_SIGNATORIES = [
  "amazon",
  "google",
  "meta",
  "microsoft",
  "openai",
  "oracle",
  "qts",
  "xai",
];
const RATEPAYER_PLEDGE_DOE_DATE = "2026-04-24";

// --------------------------------------------------------------------------
// Pledge roster (v2 — the 2026-07-23 expansion)
// --------------------------------------------------------------------------
// Mirrors SIGNATORY_CATEGORIES / SIGNATORY_TRACKS in schema.py; parity is
// asserted by test_signatory_categories_match + test_signatory_tracks_match,
// same drill as THEMES and every other frozen vocabulary here.
const SIGNATORY_CATEGORIES = [
  "hyperscaler",
  "utility",
  "cooperative",
  "developer",
  "governor",
];
const SIGNATORY_CATEGORY_LABELS = {
  hyperscaler: "Hyperscaler / AI company",
  utility: "Utility",
  cooperative: "Cooperative",
  developer: "Data-center developer",
  governor: "Governor",
};
// Short forms for filter chips, where the full label is too wide on mobile.
const SIGNATORY_CATEGORY_SHORT = {
  hyperscaler: "Hyperscalers",
  utility: "Utilities",
  cooperative: "Cooperatives",
  developer: "Developers",
  governor: "Governors",
};
const SIGNATORY_TRACKS = [
  "white-house-2026-03-04",
  "doe-2026-04-24",
  "expansion-2026-07-23",
  "rolling",
];
const SIGNATORY_TRACK_LABELS = {
  "white-house-2026-03-04": "White House, March 4, 2026",
  "doe-2026-04-24": "DOE companion track, April 24, 2026",
  "expansion-2026-07-23": "Expansion, July 23, 2026",
  rolling: "Added to the roster after July 23, 2026",
};
const RATEPAYER_PLEDGE_EXPANSION_DATE = "2026-07-23";

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

// Declared here rather than alongside VIEWS because `state` initializes from
// it and is defined first — referencing the VIEWS-adjacent const would hit the
// temporal dead zone. VIEWS resolves DEFAULT_VIEW from this name, so the two
// cannot disagree.
//
// "overview" (v2.1) rather than "ratepayer": the pledge landing band used to
// be always-visible header chrome sitting above the tab bar, which pushed the
// tabs below the fold on load. It is now the Overview tab's own content, so
// it needs to be the default view to keep behaving as the front door.
const DEFAULT_VIEW_NAME = "overview";

const state = {
  companies: [],
  claims: [],
  projects: [],
  responses: [],
  moratoriums: [],
  tariffs: [],
  signatories: [],
  coverage: {},
  coverageLoaded: false,
  rosterAsOf: null,
  rosterCountsStated: {},
  rosterDriftNote: null,
  pledgePdfUrl: null,
  signatoriesById: new Map(),
  signatoryByCompany: new Map(),
  governorByState: new Map(),
  signatoryByUtilityAlias: new Map(),
  themeRecommendations: {},
  responsesByProject: new Map(),
  claimsByProject: new Map(),
  companiesBySlug: new Map(),
  projectMoratoriums: new Map(),
  activeView: DEFAULT_VIEW_NAME,
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
  signatoriesLoaded: false,
  responsesLoaded: false,
  moratoriumsLoaded: false,
  tariffsLoaded: false,
  aggregateLoaded: false,
  leafletLoaded: false,
  map: null,
  markers: new Map(),
  chinaContext: null,
  _moratoriumReturnFocus: null,
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
  // The hero's pathway cards are static markup, so they wire once on boot;
  // the stat tiles are re-rendered from data and re-wire themselves.
  wirePledgeTargets(document.getElementById("view-overview"));
  wireStatePanel();
  ensureComparisonData()
    .then(() => {
      // Idle-preload projects + responses JSON (NOT Leaflet) so the
      // summary-stats bar can fill in projects / GW / investment / responses
      // without waiting for the user to open the Explorer tab. Runs after the
      // Comparison view has rendered and uses loadProjectData (data-only), so
      // the two-payload first-paint strategy is preserved.
      if (state.explorerLoaded || state.projects.length) return;
      const preload = () =>
        Promise.all([loadProjectData(), loadResponseData()])
          .then(() => {
            renderSummaryStats();
            renderPledgeHero();
          })
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

// Every view, each backed by a tab button + a <section>. The hash maps 1:1 to
// the view name. Iterate this table everywhere so adding a view stays a
// one-line change.
//
// Overview is the default landing view as of v2.1 (DEFAULT_VIEW_NAME), not
// Comparison, and not Ratepayer either.
// The pledge became the organizing frame for the whole "who pays for data
// center power" question, so it is the front door — but as of v2.1 it lives in
// its own Overview tab rather than as header chrome above the tab bar (see
// DEFAULT_VIEW_NAME). Comparison keeps its full behaviour one click away and
// has an explicit `#comparison` hash — it had been the bare-root view before
// v2, and demoting it without giving it a hash would have left it un-linkable.
const VIEWS = [
  { name: "overview", tab: "tab-overview", section: "view-overview", hash: "#overview" },
  { name: "ratepayer", tab: "tab-ratepayer", section: "view-ratepayer", hash: "#ratepayer" },
  { name: "comparison", tab: "tab-comparison", section: "view-comparison", hash: "#comparison" },
  { name: "moratoriums", tab: "tab-moratoriums", section: "view-moratoriums", hash: "#moratoriums" },
  { name: "tariffs", tab: "tab-tariffs", section: "view-tariffs", hash: "#tariffs" },
  { name: "explorer", tab: "tab-explorer", section: "view-explorer", hash: "#explorer" },
  { name: "aggregate", tab: "tab-aggregate", section: "view-aggregate", hash: "#aggregate" },
];

const DEFAULT_VIEW =
  VIEWS.find((v) => v.name === DEFAULT_VIEW_NAME) || VIEWS[0];

// #state/TX deep-links straight to a state panel over the Ratepayer view.
const STATE_DEEP_LINK = /^#state\/[A-Za-z]{2}$/;

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
  } else if (STATE_DEEP_LINK.test(window.location.hash)) {
    // #state/TX — open the Ratepayer view, then the panel on top of it.
    // Read the code BEFORE activating: activateView rewrites the hash to
    // "#ratepayer", so reading it afterwards yields "yer" instead of "TX".
    const code = window.location.hash.slice("#state/".length).toUpperCase();
    activateView("ratepayer");
    openStatePanel(code);
  } else {
    // No hash and no filters: land on the pledge, not on whatever section
    // happens to be first in the DOM.
    activateView(DEFAULT_VIEW.name);
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
  const target = VIEWS.find((v) => v.name === name) || DEFAULT_VIEW;
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
  // Overview needs the same payload (projects + signatories + coverage) for
  // its stat tiles / coverage bar / meters / state strip, so it shares the
  // Ratepayer loader rather than duplicating the fetch-and-index logic.
  if (target.name === "explorer" && !state.explorerLoaded) {
    loadExplorerData().catch((err) => {
      console.error("Failed to load explorer data:", err);
      document.getElementById("explorer-meta").textContent =
        "Failed to load projects.";
    });
  } else if (target.name === "ratepayer" || target.name === "overview") {
    loadRatepayerView().catch((err) => {
      console.error("Failed to load ratepayer view:", err);
    });
  } else if (target.name === "aggregate") {
    loadAggregateView().catch((err) => {
      console.error("Failed to load aggregate view:", err);
    });
  } else if (target.name === "moratoriums") {
    loadMoratoriumsData().catch((err) => {
      console.error("Failed to load moratoriums data:", err);
    });
  } else if (target.name === "tariffs") {
    loadTariffsData().catch((err) => {
      console.error("Failed to load tariffs data:", err);
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
  renderPledgeHero();
}

// Memoized handle on the companies + claims payload. loadProjectData awaits
// this before indexing claimsByProject, so a cold deep-link to a claim-
// dependent view (#ratepayer / #explorer) never races claims.json — without
// it, wireTabs activates the deep-linked view (and starts loadProjectData)
// before boot's loadComparisonData has even been called, leaving claimsByProject
// empty. Returns the same promise on repeat calls; never double-fetches.
let _comparisonDataPromise = null;
function ensureComparisonData() {
  if (!_comparisonDataPromise) _comparisonDataPromise = loadComparisonData();
  return _comparisonDataPromise;
}

// Fetch + index the projects/responses payload. Shared by the Explorer and
// Ratepayer views; safe to call repeatedly (fetches at most once). Does NOT
// touch Leaflet — that's the Explorer's concern alone.
let _projectDataPromise = null;
function loadProjectData() {
  if (!_projectDataPromise) {
    _projectDataPromise = (async () => {
      // Guarantee state.claims is populated before we index claimsByProject —
      // otherwise a cold #ratepayer/#explorer deep-link builds an empty index.
      const [, projects] = await Promise.all([
        ensureComparisonData(),
        fetchJson("data/projects.json"),
      ]);
      state.projects = projects.projects;

      state.claimsByProject = new Map();
      for (const c of state.claims) {
        if (!c.project_id) continue;
        if (!state.claimsByProject.has(c.project_id)) {
          state.claimsByProject.set(c.project_id, []);
        }
        state.claimsByProject.get(c.project_id).push(c);
      }
      // Fill in the projects / GW / investment tiles now that the lazy payload
      // is in hand (companies + claims tiles already showed).
      renderSummaryStats();
    })();
  }
  return _projectDataPromise;
}

// Community responses are a SEPARATE fetch from projects (43 KB gzipped).
//
// The landing view needs projects for the scorecard and the principle tallies,
// but responses only decorate cards that are below the fold — the ⚠ concern
// flags. Bundling the two put first paint at 246.5 KB against a 250 KB budget.
// Splitting them buys back ~43 KB, at the cost of a concern flag that appears a
// beat after the card it belongs to.
//
// Views that actually render response CONTENT (Explorer, Aggregate, the project
// detail pane) await this; the Ratepayer view kicks it off and re-renders.
let _responseDataPromise = null;
function loadResponseData() {
  if (!_responseDataPromise) {
    _responseDataPromise = (async () => {
      const responses = await fetchJson("data/responses.json");
      state.responses = responses.responses;
      state.responsesByProject = new Map();
      for (const r of state.responses) {
        if (!state.responsesByProject.has(r.project_id)) {
          state.responsesByProject.set(r.project_id, []);
        }
        state.responsesByProject.get(r.project_id).push(r);
      }
      state.responsesLoaded = true;
      renderSummaryStats();
    })();
  }
  return _responseDataPromise;
}


// Build a map of which projects are affected by which moratoriums.
// Projects match moratoriums by: (1) state-level moratoriums match by state,
// (2) city/county-level match by city name + state code.
function buildMoratoriumAffectanceMap() {
  state.projectMoratoriums = new Map();

  if (!state.moratoriums || !state.projects) return;

  state.projects.forEach((project) => {
    const affected = [];

    state.moratoriums.forEach((moratorium) => {
      let matches = false;

      if (moratorium.jurisdiction_type === "state") {
        // State moratorium: match by state code
        matches = project.state === moratorium.jurisdiction.split(",")[0].trim();
      } else if (moratorium.jurisdiction_type === "city" || moratorium.jurisdiction_type === "county") {
        // City/county moratorium: match by city name (fuzzy) + state
        // Extract state abbreviation if present (e.g., "Denver, CO" -> "CO")
        const jurisdParts = moratorium.jurisdiction.split(",").map((s) => s.trim());
        const moratoriumCity = jurisdParts[0];
        const moratoriumState = jurisdParts[1];

        // Match if city names are similar (case-insensitive) and states match
        if (
          moratoriumCity.toLowerCase().includes(project.city.toLowerCase()) ||
          project.city.toLowerCase().includes(moratoriumCity.toLowerCase())
        ) {
          if (!moratoriumState || moratoriumState === project.state) {
            matches = true;
          }
        }
      }

      if (matches) {
        affected.push(moratorium);
      }
    });

    if (affected.length > 0) {
      state.projectMoratoriums.set(project.id, affected);
    }
  });
}

async function loadExplorerData() {
  document.getElementById("explorer-meta").textContent = "Loading projects…";
  await Promise.all([loadProjectData(), loadResponseData()]);
  await ensureLeaflet();
  state.explorerLoaded = true;
  renderExplorerView();

  // Expose for e2e/debugging.
  window.__dcb = { state, THEMES, selectProject };
  document.dispatchEvent(new CustomEvent("dcb:explorer-ready"));
}

// Fetch + index the pledge roster (~120 KB — the largest single payload, and
// the reason it is lazy). Only the Ratepayer view needs it, so it never
// touches first paint. Safe to call repeatedly; fetches at most once.
let _signatoryDataPromise = null;
function loadSignatoryData() {
  if (!_signatoryDataPromise) {
    _signatoryDataPromise = (async () => {
      const payload = await fetchJson("data/signatories.json");
      state.signatories = payload.signatories;
      state.rosterAsOf = payload.roster_as_of;
      state.rosterCountsStated = payload.roster_counts_stated || {};
      state.rosterDriftNote = payload.drift_note || null;
      state.pledgePdfUrl = payload.pledge_pdf_url || null;

      state.signatoriesById = new Map(state.signatories.map((s) => [s.id, s]));
      // company slug -> roster record, for signatory-date-aware eligibility.
      state.signatoryByCompany = new Map();
      // governor state code -> roster record, for the state panel.
      state.governorByState = new Map();
      // tariff `utility` string -> roster record, exact-match joins only.
      state.signatoryByUtilityAlias = new Map();
      for (const s of state.signatories) {
        if (s.matched_company_slug) state.signatoryByCompany.set(s.matched_company_slug, s);
        if (s.category === "governor" && s.state) state.governorByState.set(s.state, s);
        for (const alias of s.utility_aliases || []) {
          state.signatoryByUtilityAlias.set(alias, s);
        }
      }
      state.signatoriesLoaded = true;
    })();
  }
  return _signatoryDataPromise;
}

// Per-state record counts, precomputed by refresh.py (~2 KB). Without this the
// landing would have to download moratoriums.json + tariffs.json (~50 KB gz)
// just to draw a state grid, and until it did it reported site counts only —
// so CA, NY and FL, which have moratoriums but no tracked site, rendered as
// "No records yet".
let _coverageDataPromise = null;
function loadCoverageData() {
  if (!_coverageDataPromise) {
    _coverageDataPromise = fetchJson("data/coverage.json")
      .then((payload) => {
        state.coverage = payload.states || {};
        state.coverageLoaded = true;
      })
      .catch((err) => {
        // Non-fatal: coverageStates() falls back to whatever live arrays are
        // loaded, which is the pre-v2 behaviour rather than a broken grid.
        console.error("Failed to load coverage rollup:", err);
      });
  }
  return _coverageDataPromise;
}

// Roster counts derived from the list we actually hold — never from the
// source page's advertised chip numbers, which drift from its own list.
function signatoryCounts() {
  const out = {};
  for (const cat of SIGNATORY_CATEGORIES) out[cat] = 0;
  for (const s of state.signatories || []) {
    if (out[s.category] !== undefined) out[s.category] += 1;
  }
  out.organizations = (state.signatories || []).filter(
    (s) => s.category !== "governor"
  ).length;
  out.total = (state.signatories || []).length;
  return out;
}

// The date a company's operator joined the pledge, or null if it never did.
// This is what makes eligibility roster-driven rather than hardcoded to the
// original eight: CoreWeave signed on 2026-07-23, so its sites announced
// before that date are "pre-their-pledge", not "not a signatory".
function signatorySignedDate(companySlug) {
  const rec = state.signatoryByCompany && state.signatoryByCompany.get(companySlug);
  return rec && rec.signed_date ? rec.signed_date : null;
}

// Ratepayer view: needs the project payload (for the scorecard) and the pledge
// roster (for the coverage + roster sections). Renders once data is in hand.
async function loadRatepayerView() {
  await Promise.all([loadProjectData(), loadSignatoryData(), loadCoverageData()]);
  state.ratepayerLoaded = true;
  renderRatepayerView();
  renderPledgeHero();

  // Concern flags need responses, which are deliberately not part of first
  // paint. Fetch them straight after and re-render the scorecard in place.
  // Awaited (not fire-and-forget) so `dcb:ratepayer-ready` still means the view
  // is complete — several e2e tests and the concern-first sort depend on that.
  if (!state.responsesLoaded) {
    await loadResponseData().catch((err) =>
      console.error("Failed to load community responses:", err)
    );
    renderRatepayerScorecard();
  }
  document.dispatchEvent(new CustomEvent("dcb:ratepayer-ready"));
}

// Aggregate view: needs the project payload but not Leaflet.
async function loadAggregateView() {
  if (state.aggregateLoaded) return;
  // The by-signatory-category rollup needs the roster; without it every
  // company would fall into "Did not sign". The responses-by-stance column
  // needs the response payload.
  await Promise.all([loadProjectData(), loadSignatoryData(), loadResponseData()]);
  state.aggregateLoaded = true;
  renderAggregateView();
}


// Moratoriums view: fetch and render moratorium data with filtering
async function loadMoratoriumsData() {
  if (state.moratoriumsLoaded) return;
  const payload = await fetchJson("data/moratoriums.json");
  state.moratoriums = payload.moratoriums;
  state.chinaContext = payload.china_anti_datacenter_messaging;
  state.themeRecommendations = payload.theme_recommendations || {};
  state.moratoriumsLoaded = true;
  renderMoratoriumsView();
  document.dispatchEvent(new CustomEvent("dcb:moratoriums-ready"));
}

// The directory shows a scannable short duration; the full `duration_description`
// (which some records carry at paragraph length) stays in the detail modal + the
// cell's title tooltip. Take the leading clause up to the first sentence break /
// parenthetical / semicolon, then word-boundary cap.
function shortDuration(d) {
  if (!d) return "—";
  const full = String(d).trim();
  let s = full;
  const b = s.search(/[;(]|\.\s/);
  if (b > 0) s = s.slice(0, b);
  s = s.replace(/[\s,;:–—-]+$/, "").trim();
  if (s.length > 46) {
    const cut = s.slice(0, 46);
    const sp = cut.lastIndexOf(" ");
    s = (sp > 20 ? cut.slice(0, sp) : cut).replace(/[,;:]$/, "").trim();
  }
  return s.length < full.length ? s + "…" : s;
}

function renderMoratoriumsView() {
  wireMoratoriumsFilters();
  wireMoratoriumDetail();

  const tbody = document.getElementById("moratoriums-tbody");
  if (!tbody) return;

  if (!state.moratoriums || !Array.isArray(state.moratoriums) || state.moratoriums.length === 0) {
    tbody.innerHTML = "<tr><td colspan='5'>No moratoriums loaded</td></tr>";
    return;
  }

  // Render stats and themes at the top (using ALL moratoriums, not filtered)
  renderMoratoriumStats(state.moratoriums);
  renderMoratoriumCharts(state.moratoriums);
  renderReasonBreakdown(state.moratoriums);
  renderChinaContext();

  const statusFilter = document.getElementById("moratorium-status-filter")?.value || "";
  const typeFilter = document.getElementById("moratorium-type-filter")?.value || "";

  let filtered = [...state.moratoriums];
  if (statusFilter) {
    filtered = filtered.filter((m) => m.status === statusFilter);
  }
  if (typeFilter) {
    filtered = filtered.filter((m) => m.jurisdiction_type === typeFilter);
  }

  setAccCount("moratoriums-count", filtered.length, "record");

  // Sort: enacted first (by date desc), then proposed, then failed
  filtered.sort((a, b) => {
    const statusOrder = { enacted: 0, proposed: 1, failed: 2 };
    if (statusOrder[a.status] !== statusOrder[b.status]) {
      return statusOrder[a.status] - statusOrder[b.status];
    }
    if (a.enacted_date && b.enacted_date) {
      return new Date(b.enacted_date) - new Date(a.enacted_date);
    }
    return a.jurisdiction.localeCompare(b.jurisdiction);
  });

  // Render table rows
  tbody.innerHTML = "";

  filtered.forEach((m) => {
    const tr = document.createElement("tr");
    tr.className = `moratorium-status-${m.status}`;

    const reasonBadges = m.key_reasons
      .map((r) => `<span class="badge badge-reason-${r}" title="${escapeAttr(MORATORIUM_REASON_LABELS[r] || r)}">${escapeHtml(MORATORIUM_REASON_LABELS[r] || r)}</span>`)
      .join("");

    // Jurisdiction cell carries only the bill/ordinance number (a consistent
    // identifier). Sponsors are detail-level — they render in the modal as
    // "Introduced by", not here (mixing names + bill#s in one column reads as
    // inconsistent and the name looks like part of the jurisdiction).
    const billHtml = m.bill_number ? `<br><span class="moratorium-bill-id">${escapeHtml(m.bill_number)}</span>` : "";

    tr.innerHTML = `
      <td>${escapeHtml(m.jurisdiction)}${billHtml}</td>
      <td><span class="badge badge-jurisdiction-type">${escapeHtml(m.jurisdiction_type)}</span></td>
      <td><span class="badge badge-moratorium-status-${m.status}">${escapeHtml(m.status)}</span></td>
      <td title="${escapeAttr(m.duration_description || "")}">${escapeHtml(shortDuration(m.duration_description))}</td>
      <td>${reasonBadges}</td>
    `;

    tr.addEventListener("click", () => {
      showMoratoriumDetail(m);
    });
    tbody.appendChild(tr);
  });
}

function _jurtypeBreakdown(moratoriums) {
  const counts = { state: 0, county: 0, city: 0, federal: 0 };
  moratoriums.forEach((m) => { if (m.jurisdiction_type in counts) counts[m.jurisdiction_type]++; });
  return ["city", "county", "state", "federal"]
    .filter((t) => counts[t] > 0)
    .map((t) => `${counts[t]} ${t}`)
    .join(" · ");
}

function renderMoratoriumStats(moratoriums) {
  if (!moratoriums || !Array.isArray(moratoriums)) return;

  const total = moratoriums.length;
  const enacted = moratoriums.filter((m) => m.status === "enacted");
  const proposed = moratoriums.filter((m) => m.status === "proposed");
  const failed = moratoriums.filter((m) => m.status === "failed");

  const statsList = document.getElementById("moratorium-stats");
  if (!statsList) return;

  statsList.innerHTML = `
    <li class="rp-stat">
      <span class="rp-stat-value">${total}</span>
      <span class="rp-stat-label">Total Moratoriums</span>
      <span class="rp-stat-breakdown">${_jurtypeBreakdown(moratoriums)}</span>
    </li>
    <li class="rp-stat">
      <span class="rp-stat-value">${enacted.length}</span>
      <span class="rp-stat-label">Enacted</span>
      <span class="rp-stat-breakdown">${_jurtypeBreakdown(enacted)}</span>
    </li>
    <li class="rp-stat">
      <span class="rp-stat-value">${proposed.length}</span>
      <span class="rp-stat-label">Proposed</span>
      <span class="rp-stat-breakdown">${_jurtypeBreakdown(proposed)}</span>
    </li>
    ${failed.length > 0 ? `
    <li class="rp-stat">
      <span class="rp-stat-value">${failed.length}</span>
      <span class="rp-stat-label">Failed/Rejected</span>
      <span class="rp-stat-breakdown">${_jurtypeBreakdown(failed)}</span>
    </li>
    ` : ""}
  `;
}

// ---- Summary charts (above the directory table) -------------------------
// All charts are pure DOM + CSS custom properties so they re-theme on the
// light/dark swap without JS and carry no chart-library weight (DESIGN.md §10).
// Every interpolated value below is a numeric count, a hardcoded label
// constant, or escapeHtml()'d — no untrusted content reaches innerHTML.
const MOR_STATUS_LABELS = { enacted: "Enacted", proposed: "Proposed", failed: "Failed" };

function _morRefDate(m) {
  // Best available date for placing a record on the activity timeline.
  const s = m.enacted_date || m.effective_date || m.captured_at;
  if (!s) return null;
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
}

function _morQuarterKey(d) {
  return d.getFullYear() * 4 + Math.floor(d.getMonth() / 3); // sortable integer
}

function _morQuarterLabel(key) {
  const year = Math.floor(key / 4);
  const q = (key % 4) + 1;
  return `Q${q}'${String(year).slice(2)}`;
}

// One combined bar per quarter (colour = status). Jurisdiction level is a FILTER,
// not a second visual encoding — a segmented toggle above the chart.
const MOR_TIMELINE_LEVELS = [
  ["all", "All"],
  ["local", "City / County"],
  ["state", "State"],
  ["federal", "Federal"],
];
const MOR_LEVEL_LABEL = Object.fromEntries(MOR_TIMELINE_LEVELS);

// Selected level persists within the session, resets on reload (same rule as the
// project-detail tabs — don't localStorage a transient view filter).
let _morTimelineLevel = "all";

function _morMatchesLevel(m, level) {
  if (level === "all") return true;
  if (level === "local") {
    return m.jurisdiction_type === "city" || m.jurisdiction_type === "county";
  }
  return m.jurisdiction_type === level;
}

function _morStatusLegend() {
  return `<div class="mor-legend" aria-hidden="true">${MORATORIUM_STATUSES.map(
    (s) =>
      `<span class="mor-legend-item"><span class="mor-legend-dot" style="background:var(--moratorium-${s})"></span>${MOR_STATUS_LABELS[s]}</span>`
  ).join("")}</div>`;
}

function _morTimelineChart(moratoriums) {
  // The x-axis range AND the y-scale are derived from the FULL dataset, never the
  // filtered subset. So the toggle filters *in place*: quarters don't shift and bar
  // heights stay comparable between levels. (Rescaling per filter would render
  // Federal's single record as a full-height bar — a lie. It should read as the
  // sliver it is.)
  const allTotals = new Map();
  moratoriums.forEach((m) => {
    const d = _morRefDate(m);
    if (!d) return;
    const k = _morQuarterKey(d);
    allTotals.set(k, (allTotals.get(k) || 0) + 1);
  });
  if (!allTotals.size) return "";
  const keys = [...allTotals.keys()];
  const min = Math.min(...keys);
  const max = Math.max(...keys);
  const scaleMax = Math.max(1, ...allTotals.values());

  const level = _morTimelineLevel;
  const buckets = new Map();
  moratoriums
    .filter((m) => _morMatchesLevel(m, level))
    .forEach((m) => {
      const d = _morRefDate(m);
      if (!d) return;
      const k = _morQuarterKey(d);
      if (!buckets.has(k)) buckets.set(k, { enacted: 0, proposed: 0, failed: 0 });
      const b = buckets.get(k);
      if (b[m.status] !== undefined) b[m.status] += 1;
    });

  const PLOT_H = 150; // px
  const cols = [];
  for (let k = min; k <= max; k++) {
    const b = buckets.get(k) || { enacted: 0, proposed: 0, failed: 0 };
    cols.push({
      key: k,
      b,
      total: MORATORIUM_STATUSES.reduce((sum, s) => sum + b[s], 0),
    });
  }

  const colsHtml = cols
    .map((c) => {
      const segs = MORATORIUM_STATUSES.map((s) => {
        if (!c.b[s]) return "";
        const h = Math.max(2, Math.round((c.b[s] / scaleMax) * PLOT_H)); // keep slivers visible
        return `<div class="mtl-seg" style="height:${h}px;background:var(--moratorium-${s})" title="${c.b[s]} ${MOR_STATUS_LABELS[s]} · ${_morQuarterLabel(c.key)}"></div>`;
      }).join("");
      return `<div class="mtl-col">
        <span class="mtl-total">${c.total || ""}</span>
        <div class="mtl-bar">${segs}</div>
        <span class="mtl-label">${_morQuarterLabel(c.key)}</span>
      </div>`;
    })
    .join("");

  const toggle = MOR_TIMELINE_LEVELS.map(([lv, label]) => {
    const n = moratoriums.filter((m) => _morMatchesLevel(m, lv)).length;
    const active = lv === level;
    return `<button type="button" class="mor-toggle-btn${active ? " is-active" : ""}" data-level="${lv}" aria-pressed="${active}">${escapeHtml(label)}<span class="mor-toggle-count">${n}</span></button>`;
  }).join("");

  return `<figure class="mor-chart mor-chart--timeline">
    <div class="mor-chart-head">
      <figcaption class="mor-chart-title">The moratorium wave <span class="mor-chart-sub">by quarter, stacked by status · y-scale shared across levels</span></figcaption>
      <div class="mor-toggle" role="group" aria-label="Filter the timeline by jurisdiction level">${toggle}</div>
    </div>
    <div class="mtl-plot" style="--plot-h:${PLOT_H}px" role="img" aria-label="Timeline of ${escapeHtml(MOR_LEVEL_LABEL[level])} data center moratorium activity by quarter, stacked by status">${colsHtml}</div>
    ${_morStatusLegend()}
  </figure>`;
}

function _morHbars(rows, { colorVar, stacked } = {}) {
  // rows: [{label, value, segments?}]  segments: [{status,value}]
  const max = Math.max(1, ...rows.map((r) => r.value));
  return rows
    .map((r) => {
      let fill;
      if (stacked && r.segments) {
        fill = r.segments
          .filter((s) => s.value > 0)
          .map(
            (s) =>
              `<span class="mhb-fill" style="width:${(s.value / max) * 100}%;background:var(--moratorium-${s.status})" title="${s.value} ${MOR_STATUS_LABELS[s.status]}"></span>`
          )
          .join("");
      } else {
        fill = `<span class="mhb-fill" style="width:${(r.value / max) * 100}%;background:${colorVar || "var(--accent)"}"></span>`;
      }
      return `<div class="mhb-row">
        <span class="mhb-label">${escapeHtml(r.label)}</span>
        <span class="mhb-track">${fill}</span>
        <span class="mhb-val">${r.value}</span>
      </div>`;
    })
    .join("");
}

function _morConcernsChart(moratoriums) {
  const counts = {};
  MORATORIUM_REASON_TYPES.forEach((r) => (counts[r] = 0));
  moratoriums.forEach((m) =>
    (m.key_reasons || []).forEach((r) => {
      if (counts[r] !== undefined) counts[r] += 1;
    })
  );
  const rows = MORATORIUM_REASON_TYPES.map((r) => ({
    label: MORATORIUM_REASON_LABELS[r] || r,
    value: counts[r],
  }))
    .filter((r) => r.value > 0)
    .sort((a, b) => b.value - a.value);
  if (!rows.length) return "";
  return `<figure class="mor-chart">
    <figcaption class="mor-chart-title">Concerns cited <span class="mor-chart-sub">records naming each issue</span></figcaption>
    <div class="mor-hbar-set">${_morHbars(rows, { colorVar: "var(--accent)" })}</div>
  </figure>`;
}

function _morJurisdictionChart(moratoriums) {
  const order = ["state", "county", "city", "federal"];
  const labels = { state: "State", county: "County", city: "City", federal: "Federal" };
  const rows = order
    .map((level) => {
      const inLevel = moratoriums.filter((m) => m.jurisdiction_type === level);
      return {
        label: labels[level],
        value: inLevel.length,
        segments: MORATORIUM_STATUSES.map((s) => ({
          status: s,
          value: inLevel.filter((m) => m.status === s).length,
        })),
      };
    })
    .filter((r) => r.value > 0)
    .sort((a, b) => b.value - a.value);
  if (!rows.length) return "";
  return `<figure class="mor-chart">
    <figcaption class="mor-chart-title">By jurisdiction level <span class="mor-chart-sub">split by status</span></figcaption>
    <div class="mor-hbar-set">${_morHbars(rows, { stacked: true })}</div>
    ${_morStatusLegend()}
  </figure>`;
}

function renderMoratoriumCharts(moratoriums) {
  const container = document.getElementById("moratorium-charts");
  if (!container) return;
  if (!moratoriums || !moratoriums.length) {
    container.replaceChildren();
    return;
  }
  const timeline = _morTimelineChart(moratoriums);
  const concerns = _morConcernsChart(moratoriums);
  const jurisdiction = _morJurisdictionChart(moratoriums);
  const html =
    timeline +
    '<div class="mor-chart-row">' +
    concerns +
    jurisdiction +
    "</div>";
  container.innerHTML = html;

  // Level toggle re-renders the charts in place (the axis + y-scale are derived
  // from the full dataset, so only the bars change).
  container.querySelectorAll(".mor-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      _morTimelineLevel = btn.dataset.level;
      renderMoratoriumCharts(moratoriums);
    });
  });

  // A long quarterly axis can still overflow a narrow viewport.
  // Park the scroll on the most RECENT quarters: whatever gets clipped must be the
  // near-empty 2024/25 past, never the current surge. (A silently-clipped chart
  // reads as "the data is missing" — it did.)
  const plot = container.querySelector(".mtl-plot");
  if (plot) {
    const parkOnRecent = () => {
      plot.scrollLeft = plot.scrollWidth; // clamps to max scroll
    };
    parkOnRecent(); // when the view is already laid out
    // ...and again after layout, in case the charts rendered while the tab was
    // still hidden (a display:none plot has zero scrollWidth, so the first call
    // would be a silent no-op and the surge would clip off-screen again).
    requestAnimationFrame(parkOnRecent);
  }
}

function renderReasonBreakdown(moratoriums) {
  if (!moratoriums || !Array.isArray(moratoriums) || moratoriums.length === 0) {
    return;
  }

  const reasonCounts = {};
  MORATORIUM_REASON_TYPES.forEach((r) => {
    reasonCounts[r] = 0;
  });

  moratoriums.forEach((m) => {
    if (m.key_reasons && Array.isArray(m.key_reasons)) {
      m.key_reasons.forEach((r) => {
        if (reasonCounts[r] !== undefined) reasonCounts[r]++;
      });
    }
  });

  const container = document.getElementById("reason-breakdown");
  if (!container) return;
  container.innerHTML = "";

  const grid = document.createElement("div");
  grid.className = "reason-grid";

  Object.entries(reasonCounts).forEach(([reason, count]) => {
    if (count > 0) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "reason-card";
      card.dataset.theme = reason;
      card.innerHTML = `
        <span class="tcc-label">${escapeHtml(MORATORIUM_REASON_LABELS[reason] || reason)}</span>
        <span class="tcc-count">${count}</span>
      `;

      card.addEventListener("click", () => {
        document.querySelectorAll(".reason-card").forEach((c) => {
          c.classList.remove("active");
        });
        card.classList.add("active");
        renderThemePopout(reason);
      });

      grid.appendChild(card);
    }
  });

  container.appendChild(grid);

  // Create popout container
  const popoutContainer = document.createElement("div");
  popoutContainer.id = "theme-popout-container";
  container.appendChild(popoutContainer);

  // Auto-click first theme
  const firstCard = grid.querySelector(".reason-card");
  if (firstCard) {
    firstCard.click();
  }
}

function renderThemePopout(themeKey) {
  const rec = state.themeRecommendations?.[themeKey];
  const container = document.getElementById("theme-popout-container");
  if (!container) return;

  container.innerHTML = "";

  if (!rec) return;

  const popout = document.createElement("div");
  popout.className = "theme-popout active";

  let html = `
    <div class="theme-popout-header">
      <h3 class="theme-popout-title">${escapeHtml(rec.label)}</h3>
      <p class="theme-popout-desc">${escapeHtml(rec.description)}</p>
    </div>
    <div class="theme-evidence">
  `;

  if (rec.evidence && Array.isArray(rec.evidence)) {
    rec.evidence.forEach((ev) => {
      html += `
        <div class="evidence-item">
          <div class="evidence-moratorium">${escapeHtml(ev.moratorium)}</div>
          <p class="evidence-text">"${escapeHtml(ev.text)}"</p>
      `;

      if (ev.proposals && Array.isArray(ev.proposals)) {
        html += `<ul class="evidence-proposals">`;
        ev.proposals.forEach((p) => {
          html += `<li>${escapeHtml(p)}</li>`;
        });
        html += `</ul>`;
      }

      html += `</div>`;
    });
  }

  html += `</div>`;
  popout.innerHTML = html;
  container.appendChild(popout);
}

function renderChinaContext() {
  const container = document.getElementById("china-context-content");
  if (!container || !state.chinaContext) return;

  const ctx = state.chinaContext;
  let html = `<p><strong>${escapeHtml(ctx.overview || "")}</strong></p>`;
  html += `<p><em>${escapeHtml(ctx.key_claim || "")}</em></p>`;

  // Industry claims section
  if (ctx.industry_claims) {
    const ic = ctx.industry_claims;

    if (ic.kevin_oleary_claim) {
      const ko = ic.kevin_oleary_claim;
      html += `<h4>The Kevin O'Leary Claim</h4>`;
      html += `<p><strong>Claimant:</strong> ${escapeHtml(ko.claimant)}</p>`;
      html += `<p><strong>Claim:</strong> "${escapeHtml(ko.claim)}"</p>`;
      html += `<p><strong>Context:</strong> ${escapeHtml(ko.context)}</p>`;
      html += `<p><strong>Evidence:</strong> <em>${escapeHtml(ko.evidence_of_campaign)}</em></p>`;
    }

    if (ic.competing_explanations) {
      const ce = ic.competing_explanations;
      html += `<h4>Alternative Explanations</h4>`;
      html += `<ul>`;
      html += `<li><strong>Documented Drivers:</strong> ${escapeHtml(ce.documented_drivers)}</li>`;
      html += `<li><strong>Local Opposition:</strong> ${escapeHtml(ce.local_opposition)}</li>`;
      html += `<li><strong>Timing:</strong> ${escapeHtml(ce.timing)}</li>`;
      html += `</ul>`;
    }
  }

  // Assessment section
  if (ctx.assessment) {
    const a = ctx.assessment;
    html += `<h4>Assessment</h4>`;
    html += `<ul>`;
    html += `<li><strong>Claim Plausibility:</strong> ${escapeHtml(a.claim_plausibility)}</li>`;
    html += `<li><strong>What Is True:</strong> ${escapeHtml(a.what_is_true)}</li>`;
    html += `<li><strong>What Is Unproven:</strong> ${escapeHtml(a.what_is_unproven)}</li>`;
    html += `<li><strong>Intelligence Assessment:</strong> ${escapeHtml(a.intelligence_assessment)}</li>`;
    html += `</ul>`;
  }

  // Federal enforcement (CFIUS) — included for completeness
  if (ctx.federal_enforcement && ctx.federal_enforcement.cfius) {
    html += `<h4>Federal Enforcement: CFIUS Reviews</h4>`;
    html += `<p>${escapeHtml(ctx.federal_enforcement.cfius.description)}</p>`;
    if (ctx.federal_enforcement.cfius.key_actions) {
      html += `<ul>`;
      ctx.federal_enforcement.cfius.key_actions.forEach(action => {
        html += `<li><strong>${escapeHtml(action.action)}</strong> — ${escapeHtml(action.status)}</li>`;
      });
      html += `</ul>`;
    }
  }

  container.innerHTML = html;
}

// Show/hide an optional dt+dd pair in the moratorium modal.
function setMdKv(dtId, ddId, value) {
  const dt = document.getElementById(dtId);
  const dd = document.getElementById(ddId);
  if (!dt || !dd) return;
  if (value) {
    dd.textContent = value;
    dt.hidden = false;
    dd.hidden = false;
  } else {
    dt.hidden = true;
    dd.hidden = true;
  }
}

function showMoratoriumDetail(m) {
  const overlay = document.getElementById("moratorium-modal");
  const modal = document.getElementById("moratorium-detail");
  if (!overlay || !modal) return;

  // Header
  document.getElementById("md-jurisdiction-type").textContent = m.jurisdiction_type.charAt(0).toUpperCase() + m.jurisdiction_type.slice(1);
  document.getElementById("md-jurisdiction").textContent = m.jurisdiction;

  // Status badge
  const statusEl = document.getElementById("md-status");
  statusEl.textContent = m.status;
  statusEl.className = `badge badge-moratorium-status-${m.status}`;

  document.getElementById("md-duration").textContent = m.duration_description;

  // Core detail fields
  document.getElementById("md-status-detail").textContent = m.status;
  document.getElementById("md-enacted").textContent = m.enacted_date || "Not yet enacted";
  document.getElementById("md-duration-detail").textContent = m.duration_description;
  document.getElementById("md-threshold").textContent = m.power_threshold_mw ? `${m.power_threshold_mw} MW` : "No threshold (all sizes)";

  // Effective date — show only when present and distinct from enacted_date
  setMdKv("md-effective-dt", "md-effective", m.effective_date && m.effective_date !== m.enacted_date ? m.effective_date : null);

  // Reasons
  if (m.key_reasons && m.key_reasons.length > 0) {
    const reasonBadges = m.key_reasons
      .map((r) => `<span class="badge badge-reason-${r}">${escapeHtml(MORATORIUM_REASON_LABELS[r] || r)}</span>`)
      .join("");
    document.getElementById("md-reasons").innerHTML = reasonBadges;
  } else {
    document.getElementById("md-reasons").textContent = "Not specified";
  }

  // Optional legislative metadata
  setMdKv("md-policy-type-dt", "md-policy-type", m.policy_type || null);
  setMdKv("md-bill-dt", "md-bill-number", m.bill_number || null);
  setMdKv("md-sponsors-dt", "md-sponsors", m.sponsors && m.sponsors.length ? m.sponsors.join("; ") : null);
  setMdKv("md-enacted-by-dt", "md-enacted-by", m.enacted_by || null);
  setMdKv("md-votes-dt", "md-votes", m.legislative_votes || m.city_council_vote || null);
  setMdKv("md-session-dt", "md-session", m.session || null);
  setMdKv("md-failure-reason-dt", "md-failure-reason", m.failure_reason || null);

  // Summary
  document.getElementById("md-summary").innerHTML = `<p>${escapeHtml(m.summary)}</p>`;

  // Key stakeholders section
  const stakeholdersWrap = document.getElementById("md-stakeholders");
  const stakeholdersBody = document.getElementById("md-stakeholders-body");
  if (m.key_stakeholders && typeof m.key_stakeholders === "object" && Object.keys(m.key_stakeholders).length > 0) {
    const CATEGORY_LABELS = {
      environmental: "Environmental",
      utility: "Utility / Grid",
      community: "Community",
      labor: "Labor",
      opposed: "Opposed",
      government: "Government",
      academic: "Academic",
      industry: "Industry",
    };
    stakeholdersBody.innerHTML = Object.entries(m.key_stakeholders)
      .map(([cat, orgs]) => {
        if (!Array.isArray(orgs) || orgs.length === 0) return "";
        const label = CATEGORY_LABELS[cat] || cat.charAt(0).toUpperCase() + cat.slice(1);
        const items = orgs.map((o) => `<li>${escapeHtml(o)}</li>`).join("");
        return `<div class="mstakeholder-group" data-category="${escapeAttr(cat)}">
          <p class="mstakeholder-category">${escapeHtml(label)}</p>
          <ul class="mstakeholder-list">${items}</ul>
        </div>`;
      })
      .join("");
    stakeholdersWrap.hidden = false;
  } else {
    stakeholdersBody.innerHTML = "";
    stakeholdersWrap.hidden = true;
  }

  // Resources list — primary source first, then deduplicated additional resources
  const resourcesList = document.getElementById("md-resources-list");
  resourcesList.innerHTML = "";

  const seenUrls = new Set();

  function addResource(url, title, isPrimary) {
    if (!url || seenUrls.has(url)) return;
    seenUrls.add(url);
    const li = document.createElement("li");
    const isGov = /\.(gov|legislature\.|legis\.|capitol\.|assembly\.|senate\.|house\.|state\.[a-z]{2}\.us)/i.test(url);
    const govBadge = isGov ? `<span class="badge badge-gov" title="Official government source">gov</span> ` : "";
    li.innerHTML = `${govBadge}<a href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}${isPrimary ? " (primary)" : ""} ↗</a>`;
    resourcesList.appendChild(li);
  }

  addResource(m.source_url, m.source_title, true);
  if (m.resources && Array.isArray(m.resources)) {
    m.resources.forEach((res) => addResource(res.url, res.title, false));
  }

  // Captured date
  document.getElementById("md-captured").textContent = `Verified: ${m.captured_at}`;

  // Remember trigger for focus return, then open
  state._moratoriumReturnFocus =
    document.activeElement instanceof HTMLElement ? document.activeElement : null;
  overlay.hidden = false;
  document.body.classList.add("moratorium-modal-open");
  modal.scrollTop = 0;
  overlay.scrollTop = 0;
  const closeBtn = document.getElementById("moratorium-detail-close");
  if (closeBtn) closeBtn.focus();
}

function closeMoratoriumDetail() {
  const overlay = document.getElementById("moratorium-modal");
  if (!overlay || overlay.hidden) return;
  overlay.hidden = true;
  document.body.classList.remove("moratorium-modal-open");
  const ret = state._moratoriumReturnFocus;
  state._moratoriumReturnFocus = null;
  if (ret && typeof ret.focus === "function") ret.focus();
}

// --------------------------------------------------------------------------
// Utility Tariffs view (v1.17)
// --------------------------------------------------------------------------
// State large-load tariff designs scored against the DOE/LBL rate-design
// element taxonomy. Lazy-loads its own payload (data/tariffs.json); no Leaflet.

async function loadTariffsData() {
  if (state.tariffsLoaded) return;
  const payload = await fetchJson("data/tariffs.json");
  state.tariffs = payload.tariffs || [];
  state.tariffsLoaded = true;
  renderTariffsView();
}

// Number of LBL design elements a tariff addresses (included OR partial).
function tariffElementCount(t) {
  return Object.keys(t.parameters || {}).length;
}

function renderTariffsView() {
  wireTariffsFilters();
  wireTariffDetail();
  populateTariffStateFilter();

  const tbody = document.getElementById("tariffs-tbody");
  if (!tbody) return;
  if (!Array.isArray(state.tariffs) || state.tariffs.length === 0) {
    tbody.innerHTML = "<tr><td colspan='6'>No tariffs loaded</td></tr>";
    return;
  }

  // Stats + LBL coverage use the FULL set (not the filtered table).
  renderTariffStats(state.tariffs);
  renderTariffCoverage(state.tariffs);
  renderTariffsTable();
}

// Federal (FERC co-location) cases are tracked for context but kept OUT of the
// state-tariff status counts + state tally so they don't read as a state tariff
// being approved/rejected. They surface in their own "Federal cases" tile and a
// FED badge in the directory.
function isFederalTariff(t) {
  return t.jurisdiction_level === "federal";
}

function renderTariffStats(tariffs) {
  const ul = document.getElementById("tariff-stats");
  if (!ul) return;
  const stateTariffs = tariffs.filter((t) => !isFederalTariff(t));
  const federal = tariffs.filter(isFederalTariff);
  const by = (s) => stateTariffs.filter((t) => t.status === s).length;
  const statesCovered = new Set(stateTariffs.map((t) => t.state)).size;
  // [value, label, showWhenZero]. Status counts are STATE-only; federal cases
  // get their own tile; zero-count status tiles are hidden.
  const tiles = [
    [tariffs.length, "Tariffs tracked", true],
    [by("approved"), "Approved", false],
    [by("proposed"), "Proposed", false],
    [by("rejected"), "Rejected / Withdrawn", false],
    [federal.length, "Federal cases", false],
    [statesCovered, "States covered", true],
  ];
  ul.innerHTML = tiles
    .filter(([n, , showZero]) => showZero || n > 0)
    .map(
      ([n, label]) => `
      <li class="rp-stat">
        <span class="rp-stat-value">${n}</span>
        <span class="rp-stat-label">${escapeHtml(label)}</span>
      </li>`
    )
    .join("");
}

// Fill the state filter dropdown from the states present in the data.
function populateTariffStateFilter() {
  const sel = document.getElementById("tariff-state-filter");
  if (!sel || sel.dataset.populated) return;
  const states = [...new Set(state.tariffs.map((t) => t.state))].sort();
  for (const st of states) {
    const opt = document.createElement("option");
    opt.value = st;
    opt.textContent = st;
    sel.appendChild(opt);
  }
  sel.dataset.populated = "1";
}

// LBL element coverage grid: one card per design element, grouped by the five
// LBL categories, showing how many tracked tariffs address it. Click → popout
// listing the tariffs. Mirrors the moratorium "reason breakdown" pattern.
function renderTariffCoverage(tariffs) {
  const grid = document.getElementById("tariff-coverage-grid");
  if (!grid) return;
  grid.innerHTML = "";
  setAccCount("tariff-coverage-count", TARIFF_PARAMETERS.length, "element");

  const counts = {};
  for (const k of TARIFF_PARAMETERS) counts[k] = 0;
  for (const t of tariffs) {
    for (const k of Object.keys(t.parameters || {})) {
      if (counts[k] !== undefined) counts[k]++;
    }
  }

  for (const [groupKey, groupLabel] of TARIFF_PARAMETER_GROUPS) {
    const group = document.createElement("div");
    group.className = "tariff-coverage-group";
    group.innerHTML = `<h4 class="tariff-coverage-group-title">${escapeHtml(groupLabel)}</h4>`;
    const row = document.createElement("div");
    row.className = "tariff-coverage-row";
    for (const key of TARIFF_PARAMETERS) {
      if (TARIFF_PARAMETER_GROUP_OF[key] !== groupKey) continue;
      const count = counts[key];
      const card = document.createElement("button");
      card.type = "button";
      card.className = "tariff-coverage-card" + (count === 0 ? " empty" : "");
      card.dataset.param = key;
      card.title = TARIFF_PARAMETER_DESCRIPTIONS[key] || "";
      card.innerHTML = `
        <span class="tcc-label">${escapeHtml(TARIFF_PARAMETER_LABELS[key])}</span>
        <span class="tcc-count">${count}</span>
      `;
      card.addEventListener("click", () => {
        document
          .querySelectorAll(".tariff-coverage-card")
          .forEach((c) => c.classList.remove("active"));
        card.classList.add("active");
        renderTariffCoveragePopout(key);
      });
      row.appendChild(card);
    }
    group.appendChild(row);
    grid.appendChild(group);
  }
}

function renderTariffCoveragePopout(paramKey) {
  const wrap = document.getElementById("tariff-coverage-popout");
  if (!wrap) return;
  const matches = state.tariffs.filter((t) => t.parameters && t.parameters[paramKey]);
  const label = TARIFF_PARAMETER_LABELS[paramKey];
  const desc = TARIFF_PARAMETER_DESCRIPTIONS[paramKey] || "";

  if (matches.length === 0) {
    wrap.innerHTML = `
      <div class="tariff-popout active">
        <h4 class="tariff-popout-title">${escapeHtml(label)}</h4>
        <p class="tariff-popout-desc">${escapeHtml(desc)}</p>
        <p class="muted">No tracked tariff currently addresses this element — a gap in current practice.</p>
      </div>`;
    return;
  }

  const items = matches
    .map((t) => {
      const pc = t.parameters[paramKey];
      const partial = pc.status === "partial" ? ' <span class="tariff-partial-tag">partial</span>' : "";
      const url = pc.source_url || t.source_url;
      return `
        <li class="tariff-popout-item">
          <div class="tpi-head">
            <a href="${escapeAttr(String(url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(t.utility)} — ${escapeHtml(t.tariff_name)} ↗</a>
            <span class="tpi-state">${escapeHtml(t.state)}</span>${partial}
          </div>
          <p class="tpi-detail">${escapeHtml(pc.detail)}</p>
        </li>`;
    })
    .join("");

  wrap.innerHTML = `
    <div class="tariff-popout active">
      <h4 class="tariff-popout-title">${escapeHtml(label)} <span class="tariff-popout-n">${matches.length} tariff${matches.length === 1 ? "" : "s"}</span></h4>
      <p class="tariff-popout-desc">${escapeHtml(desc)}</p>
      <ul class="tariff-popout-list">${items}</ul>
    </div>`;
}

// Sort: approved first (by decision date desc), then proposed, then rejected.
function tariffSort(a, b) {
  const order = { approved: 0, proposed: 1, rejected: 2 };
  if (order[a.status] !== order[b.status]) return order[a.status] - order[b.status];
  const ad = a.decision_date || "";
  const bd = b.decision_date || "";
  if (ad && bd && ad !== bd) return bd.localeCompare(ad);
  return a.utility.localeCompare(b.utility);
}

function filteredTariffs() {
  const statusF = document.getElementById("tariff-status-filter")?.value || "";
  const stateF = document.getElementById("tariff-state-filter")?.value || "";
  return state.tariffs
    .filter((t) => (statusF ? t.status === statusF : true))
    .filter((t) => (stateF ? t.state === stateF : true))
    .sort(tariffSort);
}

function renderTariffsTable() {
  const tbody = document.getElementById("tariffs-tbody");
  if (!tbody) return;
  const rows = filteredTariffs();
  setAccCount("tariffs-count", rows.length, "tariff");
  tbody.innerHTML = "";

  if (rows.length === 0) {
    tbody.innerHTML = "<tr><td colspan='6' class='muted'>No tariffs match the current filters.</td></tr>";
    return;
  }

  for (const t of rows) {
    const tr = document.createElement("tr");
    tr.className = `tariff-status-${t.status}`;
    const minLoad = t.min_load_mw != null ? `${t.min_load_mw.toLocaleString()} MW` : "—";
    const n = tariffElementCount(t);
    const typeLine = t.tariff_type
      ? `<span class="tariff-row-type">${escapeHtml(t.tariff_type)}</span>`
      : "";
    // Federal (FERC) cases carry a FED tag so they're never mistaken for a
    // state tariff, even though they share the directory + status filter.
    const fedTag = isFederalTariff(t)
      ? ` <span class="badge badge-tariff-federal" title="Federal FERC case — not a state tariff">FED</span>`
      : "";
    tr.innerHTML = `
      <td>${escapeHtml(t.utility)}</td>
      <td><span class="badge badge-jurisdiction-type">${escapeHtml(t.state)}</span>${fedTag}</td>
      <td><span class="tariff-row-name">${escapeHtml(t.tariff_name)}</span>${typeLine}</td>
      <td><span class="badge badge-tariff-status-${t.status}">${escapeHtml(TARIFF_STATUS_LABELS[t.status] || t.status)}</span></td>
      <td class="num">${minLoad}</td>
      <td class="num"><span class="tariff-elem-count" title="${n} of 17 LBL design elements">${n} / 17</span></td>
    `;
    // Keyboard + screen-reader accessible: the row acts as a button.
    tr.tabIndex = 0;
    tr.setAttribute("role", "button");
    tr.setAttribute(
      "aria-label",
      `${t.utility} — ${t.tariff_name}, ${TARIFF_STATUS_LABELS[t.status] || t.status}. Open details.`
    );
    const open = () => showTariffDetail(t);
    tr.addEventListener("click", open);
    tr.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
        e.preventDefault();
        open();
      }
    });
    tbody.appendChild(tr);
  }
}

// Detail pop-out: the full per-element "met or not met" checklist + additional
// terms + legislation + sources. This is where the LBL mapping lives in full.
function showTariffDetail(t) {
  const overlay = document.getElementById("tariff-modal");
  const modal = document.getElementById("tariff-detail");
  if (!overlay || !modal) return;

  const setText = (id, txt) => {
    const el = document.getElementById(id);
    if (el) el.textContent = txt;
  };

  setText("td-utility", t.tariff_type || "Large-load tariff");
  setText("td-name", `${t.utility} — ${t.tariff_name}`);

  const statusEl = document.getElementById("td-status");
  statusEl.textContent = TARIFF_STATUS_LABELS[t.status] || t.status;
  statusEl.className = `badge badge-tariff-status-${t.status}`;
  setText("td-state", isFederalTariff(t) ? `${t.state} · Federal (FERC)` : t.state);

  setText("td-utility-detail", t.utility);
  setText("td-regulator", t.regulator || "—");
  setText("td-docket", t.docket_number || "Not assigned");
  setText("td-status-detail", t.status_detail || (TARIFF_STATUS_LABELS[t.status] || t.status));
  setText("td-decision", t.decision_date || (t.status === "proposed" ? "Pending" : "—"));
  setText("td-minload", t.min_load_mw != null ? `${t.min_load_mw.toLocaleString()} MW` : "Not specified");
  setText("td-customers", t.customers && t.customers.length ? t.customers.join(", ") : "Not disclosed");

  document.getElementById("td-summary").innerHTML = `<p>${escapeHtml(t.summary)}</p>`;

  // Surface the coverage tally in the params heading ("9 of 17 addressed").
  const paramsHeading = document.getElementById("td-params-heading");
  if (paramsHeading) {
    const n = tariffElementCount(t);
    paramsHeading.innerHTML =
      `LBL rate-design elements — met or not ` +
      `<span class="td-elem-tally">${n} of ${TARIFF_PARAMETERS.length} addressed</span>`;
  }

  // LBL element checklist — iterate the full taxonomy so "not addressed" shows.
  const body = document.getElementById("td-params-body");
  body.innerHTML = "";
  for (const [groupKey, groupLabel] of TARIFF_PARAMETER_GROUPS) {
    const groupParams = TARIFF_PARAMETERS.filter(
      (k) => TARIFF_PARAMETER_GROUP_OF[k] === groupKey
    );
    const rows = groupParams
      .map((key) => {
        const pc = (t.parameters || {})[key];
        const status = pc ? pc.status || "included" : "absent";
        const icon = status === "included" ? "✓" : status === "partial" ? "◐" : "✕";
        const statusLabel =
          status === "included" ? "Included" : status === "partial" ? "Partial" : "Not addressed";
        const detail = pc
          ? `<span class="tparam-detail">${escapeHtml(pc.detail)}</span>`
          : `<span class="tparam-detail muted">Not addressed in this tariff.</span>`;
        const srcLink =
          pc && pc.source_url
            ? ` <a class="tparam-src" href="${escapeAttr(String(pc.source_url))}" target="_blank" rel="noopener noreferrer" title="Source for this element">↗</a>`
            : "";
        return `
          <li class="tparam-row tparam-${status}">
            <span class="tparam-icon" aria-hidden="true">${icon}</span>
            <div class="tparam-body">
              <span class="tparam-label">${escapeHtml(TARIFF_PARAMETER_LABELS[key])}<span class="tparam-status"> · ${statusLabel}</span>${srcLink}</span>
              ${detail}
            </div>
          </li>`;
      })
      .join("");
    body.insertAdjacentHTML(
      "beforeend",
      `<div class="tparam-group">
        <h5 class="tparam-group-title">${escapeHtml(groupLabel)}</h5>
        <ul class="tparam-list">${rows}</ul>
      </div>`
    );
  }

  // Additional terms (outside the LBL study).
  const addWrap = document.getElementById("td-additional");
  const addList = document.getElementById("td-additional-list");
  if (t.additional_terms && t.additional_terms.length) {
    addList.innerHTML = t.additional_terms
      .map((a) => {
        const link = a.source_url
          ? ` <a href="${escapeAttr(String(a.source_url))}" target="_blank" rel="noopener noreferrer">↗</a>`
          : "";
        return `<li><strong>${escapeHtml(a.term)}:</strong> ${escapeHtml(a.detail)}${link}</li>`;
      })
      .join("");
    addWrap.hidden = false;
  } else {
    addList.innerHTML = "";
    addWrap.hidden = true;
  }

  // State legislation behind the tariff.
  const legWrap = document.getElementById("td-legislation");
  const legList = document.getElementById("td-legislation-list");
  if (t.legislation && t.legislation.length) {
    legList.innerHTML = t.legislation
      .map((l) => {
        const meta = [l.citation, l.status].filter(Boolean).join(" · ");
        const sub = l.summary ? `<span class="tleg-summary">${escapeHtml(l.summary)}</span>` : "";
        return `<li>
          <a href="${escapeAttr(String(l.url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(l.title)} ↗</a>
          ${meta ? `<span class="tleg-meta">${escapeHtml(meta)}</span>` : ""}
          ${sub}
        </li>`;
      })
      .join("");
    legWrap.hidden = false;
  } else {
    legList.innerHTML = "";
    legWrap.hidden = true;
  }

  // Sources: primary source first, then any additional resources.
  const resList = document.getElementById("td-resources-list");
  resList.innerHTML = "";
  const primary = document.createElement("li");
  primary.innerHTML = `<a href="${escapeAttr(String(t.source_url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(t.source_title)} ↗</a>`;
  resList.appendChild(primary);
  if (Array.isArray(t.resources)) {
    for (const r of t.resources) {
      const li = document.createElement("li");
      li.innerHTML = `<a href="${escapeAttr(String(r.url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(r.title)} ↗</a>`;
      resList.appendChild(li);
    }
  }

  setText("td-captured", `Verified: ${t.captured_at}`);

  // Remember the trigger so focus returns to it on close, then open the modal.
  state._tariffReturnFocus =
    document.activeElement instanceof HTMLElement ? document.activeElement : null;
  overlay.hidden = false;
  document.body.classList.add("tariff-modal-open");
  modal.scrollTop = 0;
  overlay.scrollTop = 0;
  const closeBtn = document.getElementById("tariff-detail-close");
  if (closeBtn) closeBtn.focus();
}

function closeTariffDetail() {
  const overlay = document.getElementById("tariff-modal");
  if (!overlay || overlay.hidden) return;
  overlay.hidden = true;
  document.body.classList.remove("tariff-modal-open");
  const ret = state._tariffReturnFocus;
  state._tariffReturnFocus = null;
  if (ret && typeof ret.focus === "function") ret.focus();
}

function wireTariffsFilters() {
  for (const id of ["tariff-status-filter", "tariff-state-filter"]) {
    const el = document.getElementById(id);
    if (el && !el.dataset.wired) {
      el.addEventListener("change", renderTariffsTable);
      el.dataset.wired = "1";
    }
  }
  const csvBtn = document.getElementById("tariffs-csv-btn");
  if (csvBtn && !csvBtn.dataset.wired) {
    csvBtn.addEventListener("click", (e) => { e.preventDefault(); downloadTariffCSV(); });
    csvBtn.dataset.wired = "1";
  }
  wireBtn("tariffs-pdf-btn", exportTariffsToPDF);
}

function wireTariffDetail() {
  const overlay = document.getElementById("tariff-modal");
  const closeBtn = document.getElementById("tariff-detail-close");
  if (closeBtn && !closeBtn.dataset.wired) {
    closeBtn.addEventListener("click", closeTariffDetail);
    closeBtn.dataset.wired = "1";
  }
  if (overlay && !overlay.dataset.wired) {
    // Click on the backdrop (or the overlay area outside the dialog) closes.
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay || e.target.closest("[data-tariff-close]")) {
        closeTariffDetail();
      }
    });
    // Keep Tab focus inside the dialog while the modal is open.
    overlay.addEventListener("keydown", (e) => {
      if (e.key === "Tab" && !overlay.hidden) trapModalFocus(e, overlay);
    });
    overlay.dataset.wired = "1";
  }
  if (!document._tariffEscWired) {
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeTariffDetail();
    });
    document._tariffEscWired = true;
  }
}

// Simple focus trap: cycle Tab / Shift+Tab within the modal's focusables.
// Shared by every `aria-modal` dialog (tariff, moratorium, state). The logic was
// always generic — only the name was tariff-specific, which is why the
// moratorium modal ended up re-inlining a copy of it.
function trapModalFocus(e, overlay) {
  const focusables = [...overlay.querySelectorAll(
    'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )].filter((el) => el.offsetParent !== null);
  if (!focusables.length) return;
  const first = focusables[0];
  const last = focusables[focusables.length - 1];
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
}

// CSV export: one row per tariff with status + per-element coverage flags.
function buildTariffCSV() {
  const headers = [
    "Utility",
    "State",
    "Tariff",
    "Type",
    "Status",
    "Regulator",
    "Docket",
    "Decision date",
    "Min load (MW)",
    "Customers",
    "LBL elements addressed",
    "Summary",
    "Source title",
    "Source URL",
    "Legislation",
    ...TARIFF_PARAMETERS.map((k) => TARIFF_PARAMETER_LABELS[k]),
  ];
  const lines = [headers.map(escapeCSV).join(",")];
  for (const t of filteredTariffs()) {
    const legis = (t.legislation || [])
      .map((l) => `${l.title} (${l.url})`)
      .join(" | ");
    const elemFlags = TARIFF_PARAMETERS.map((k) => {
      const pc = (t.parameters || {})[k];
      if (!pc) return "";
      return pc.status === "partial" ? "partial" : "yes";
    });
    const row = [
      t.utility,
      t.state,
      t.tariff_name,
      t.tariff_type || "",
      TARIFF_STATUS_LABELS[t.status] || t.status,
      t.regulator || "",
      t.docket_number || "",
      t.decision_date || "",
      t.min_load_mw != null ? t.min_load_mw : "",
      (t.customers || []).join("; "),
      tariffElementCount(t),
      t.summary,
      t.source_title,
      String(t.source_url),
      legis,
      ...elemFlags,
    ];
    lines.push(row.map(escapeCSV).join(","));
  }
  return lines.join("\r\n");
}

function downloadTariffCSV() {
  const csv = buildTariffCSV();
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "state-utility-tariffs.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
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
  wireBtn("comparison-pdf-btn", exportComparisonToPDF);
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
      const label = `${byStance.positive} positive, ${byStance.mixed} mixed, ${byStance.negative} negative`;
      breakdown.innerHTML =
        `<span class="stance-dot positive"></span>${byStance.positive}` +
        `<span class="stance-dot mixed"></span>${byStance.mixed}` +
        `<span class="stance-dot negative"></span>${byStance.negative}`;
      breakdown.setAttribute("aria-label", `Community responses by stance: ${label}`);
      breakdown.setAttribute("title", label);
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

// One-liner to wire a button by id — guards against double-wiring and missing elements.
function wireBtn(id, handler) {
  const btn = document.getElementById(id);
  if (!btn || btn.dataset.wired === "1") return;
  btn.dataset.wired = "1";
  btn.addEventListener("click", handler);
}

// --------------------------------------------------------------------------
// Pledge landing band (v2)
// --------------------------------------------------------------------------

// Format a date as "Jul 25, 2026". Roster counts are always shown with the day
// they were captured — the roster is a living list, and an undated count reads
// as a permanent fact.
function formatAsOf(iso) {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// Small DOM builder: el("span", "cls", "text"). Used instead of innerHTML for
// the hero because these tiles interleave data-derived strings with markup,
// and building nodes keeps that categorically un-injectable rather than
// correct-as-long-as-every-interpolation-stays-escaped.
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

// Render the hero's stat row from whatever data has actually loaded.
//
// Called at three moments — after companies+claims, after projects/responses,
// and after the roster — so it must degrade rather than wait: a tile whose
// payload has not landed shows an em dash instead of blocking the row. That
// keeps the pledge stats visible on first paint without pulling the 124 KB
// roster into it.
function renderPledgeHero() {
  const list = document.getElementById("pledge-stats");
  if (!list) return;

  const counts = state.signatoriesLoaded ? signatoryCounts() : null;
  const assessed = (state.projects || []).filter((p) => p.ratepayer);
  const byStatus = {};
  for (const s of RATEPAYER_STATUSES) byStatus[s] = 0;
  for (const p of assessed) {
    if (byStatus[p.ratepayer.status] !== undefined) byStatus[p.ratepayer.status] += 1;
  }

  const tiles = [
    {
      num: counts ? String(counts.organizations) : "—",
      label: "Organizations signed",
      note: state.rosterAsOf ? `As of ${formatAsOf(state.rosterAsOf)}` : "",
      target: "roster",
    },
    {
      num: counts ? String(counts.governor) : "—",
      label: "Governors signed an addendum",
      note: counts ? "A separate instrument" : "",
      target: "coverage",
    },
    {
      num: state.projects.length ? String(assessed.length) : "—",
      label: "Sites assessed against the pledge",
      note: assessed.length
        ? `${byStatus.affirmed} site-specific · ${byStatus.contested} contested`
        : "",
      target: "scorecard",
    },
    {
      num: String(PLEDGE_PRINCIPLES.length),
      label: "Commitments in the pledge",
      note: "What each site is measured against",
      target: "commitments",
    },
  ];

  list.replaceChildren(
    ...tiles.map((t) => {
      const li = el("li", "pledge-stat");
      const btn = el("button", null);
      btn.type = "button";
      btn.dataset.pathTarget = t.target;
      btn.append(
        el("span", "pledge-stat-num", t.num),
        el("span", "pledge-stat-lbl", t.label)
      );
      if (t.note) btn.append(el("span", "pledge-stat-note", t.note));
      li.append(btn);
      return li;
    })
  );

  wirePledgeTargets(list);
  renderPledgeCoverageBar();
  renderPledgeMeters();
  renderPledgeStateStrip();
  renderPledgeActivity();
  wirePledgeTargets(document.getElementById("view-overview"));
}

// --- who signed: one proportional bar ------------------------------------
//
// A single number ("279") says nothing about the shape of the coalition. The
// bar shows that it is overwhelmingly rural cooperatives, which is the actual
// story of the July expansion and is invisible in a stat tile.
function renderPledgeCoverageBar() {
  const bar = document.getElementById("pledge-coverage-bar");
  const key = document.getElementById("pledge-coverage-key");
  if (!bar || !key) return;
  if (!state.signatoriesLoaded) {
    bar.replaceChildren();
    key.replaceChildren(el("li", "pledge-bar-loading", "Loading roster…"));
    return;
  }

  const counts = signatoryCounts();
  const segments = SIGNATORY_CATEGORIES.map((cat) => ({
    cat,
    n: counts[cat] || 0,
  })).filter((s) => s.n > 0);

  bar.replaceChildren(
    ...segments.map((s) => {
      const seg = el("span", `pledge-bar-seg cat-${s.cat}`);
      seg.style.flexGrow = String(s.n);
      seg.title = `${s.n} ${SIGNATORY_CATEGORY_SHORT[s.cat]}`;
      return seg;
    })
  );
  bar.setAttribute("role", "img");
  bar.setAttribute(
    "aria-label",
    segments
      .map((s) => `${s.n} ${SIGNATORY_CATEGORY_SHORT[s.cat]}`)
      .join(", ")
  );

  key.replaceChildren(
    ...segments.map((s) => {
      const li = el("li", `pledge-bar-key-item cat-${s.cat}`);
      li.append(
        el("span", "pledge-bar-swatch"),
        el("span", "pledge-bar-key-n", String(s.n)),
        el("span", "pledge-bar-key-lbl", SIGNATORY_CATEGORY_SHORT[s.cat] || s.cat)
      );
      return li;
    })
  );
  // Share of ORGANIZATIONS, not of the whole roster — governors are not
  // organizations, and counting them in the denominator understates it.
  const pct = Math.round(((counts.cooperative || 0) / (counts.organizations || 1)) * 100);
  key.append(
    el(
      "li",
      "pledge-bar-note",
      `${pct}% of the organizations that signed are rural electric cooperatives.`
    )
  );
}

// --- is it showing up: per-commitment meters ------------------------------
function renderPledgeMeters() {
  const ul = document.getElementById("pledge-meters");
  if (!ul) return;
  if (!state.projects.length) {
    ul.replaceChildren(el("li", "pledge-bar-loading", "Loading site assessments…"));
    return;
  }

  const tallies = principleTallies();
  ul.replaceChildren(
    ...PLEDGE_PRINCIPLES.map((keyName, i) => {
      const t = tallies[keyName];
      const li = el("li", "pledge-meter");
      li.append(el("span", "pledge-meter-num", ROMAN[i] || String(i + 1)));

      const body = el("div", "pledge-meter-body");
      body.append(
        el("span", "pledge-meter-lbl", PLEDGE_PRINCIPLE_SHORT[keyName] || keyName)
      );

      const track = el("span", "pledge-meter-track");
      if (t.assessed === 0) {
        track.append(el("span", "pledge-meter-seg is-none"));
      } else {
        for (const status of PLEDGE_PRINCIPLE_STATUSES) {
          if (!t[status]) continue;
          const seg = el("span", `pledge-meter-seg is-${status}`);
          seg.style.flexGrow = String(t[status]);
          track.append(seg);
        }
      }
      body.append(track);
      body.append(
        el(
          "span",
          "pledge-meter-count",
          t.assessed === 0
            ? "not yet assessed"
            : `${t.met} met · ${t.partial} partial${t.not_met ? ` · ${t.not_met} not met` : ""}`
        )
      );
      li.append(body);
      li.setAttribute(
        "aria-label",
        `${PLEDGE_PRINCIPLE_LABELS[keyName]}: ${t.met} met, ${t.partial} partial, ${t.not_met} not met`
      );
      return li;
    })
  );
}

// --- what about my state: the 50-state strip ------------------------------
//
// Every state gets a cell, including the ones we hold nothing for. A grid that
// only showed states with data would quietly imply national coverage we do not
// have.
const STATE_STRIP_ORDER = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
];

function renderPledgeStateStrip() {
  const wrap = document.getElementById("pledge-state-strip");
  const keyEl = document.getElementById("pledge-strip-key");
  if (!wrap) return;

  const byCode = new Map(coverageStates().map((s) => [s.code, s]));
  let withRecords = 0;
  let governors = 0;

  wrap.replaceChildren(
    ...STATE_STRIP_ORDER.map((code) => {
      const s = byCode.get(code);
      const records = s ? s.projects + s.tariffs + s.moratoriums : 0;
      const gov = Boolean(s && s.governor);
      if (records) withRecords += 1;
      if (gov) governors += 1;

      // Four density steps, not a continuous ramp — the underlying counts are
      // small and a smooth scale would imply precision we don't have.
      const level = records === 0 ? 0 : records <= 2 ? 1 : records <= 6 ? 2 : 3;
      const cell = el("button", `pledge-state-cell lvl-${level}${gov ? " is-gov" : ""}`);
      cell.type = "button";
      cell.dataset.stateCode = code;
      cell.append(el("span", "pledge-state-abbr", code));
      cell.setAttribute(
        "aria-label",
        `${STATE_NAMES[code] || code}: ${records ? `${records} tracked records` : "no tracked records"}` +
          (gov ? ", governor signed the addendum" : "")
      );
      cell.title = cell.getAttribute("aria-label");
      cell.addEventListener("click", () => openStatePanel(code));
      return cell;
    })
  );

  if (keyEl) {
    keyEl.textContent =
      `${withRecords} of 50 states have tracked records · ` +
      `${governors} governors signed (marked ★) · select a state for detail`;
  }
}

// --- what changed: a short dated feed -------------------------------------
//
// Derived from the data rather than hand-maintained, so it cannot go stale
// while the dataset moves underneath it.
function renderPledgeActivity() {
  const ol = document.getElementById("pledge-activity");
  if (!ol) return;

  const items = [];

  if (state.signatoriesLoaded) {
    const counts = signatoryCounts();
    const joined = (state.signatories || []).filter(
      (s) => s.signed_track === "expansion-2026-07-23"
    );
    const joinedOrgs = joined.filter((s) => s.category !== "governor").length;
    const joinedGovs = joined.length - joinedOrgs;
    if (joined.length) {
      items.push({
        date: RATEPAYER_PLEDGE_EXPANSION_DATE,
        text:
          `${joinedOrgs} organizations and ${joinedGovs} governors joined, taking ` +
          `the roster from 8 signatories to ${counts.organizations}.`,
      });
    }
  }

  // Newest contested findings — the sharpest signal the dataset carries.
  const contested = (state.projects || [])
    .filter((p) => p.ratepayer && p.ratepayer.status === "contested")
    .slice(0, 3);
  if (contested.length) {
    items.push({
      date: contested[0].ratepayer.captured_at || contested[0].captured_at || null,
      text:
        `${contested.length} site${contested.length === 1 ? "" : "s"} marked contested — ` +
        "a third party documents costs reaching ratepayers despite the pledge.",
    });
  }

  // Most recently captured site assessment.
  const assessed = (state.projects || [])
    .filter((p) => p.ratepayer && p.ratepayer.captured_at)
    .sort((a, b) => b.ratepayer.captured_at.localeCompare(a.ratepayer.captured_at));
  if (assessed.length) {
    items.push({
      date: assessed[0].ratepayer.captured_at,
      text: `Latest site assessment: ${assessed[0].name}.`,
    });
  }

  if (!items.length) {
    ol.replaceChildren(el("li", "pledge-bar-loading", "Loading recent activity…"));
    return;
  }

  ol.replaceChildren(
    ...items.slice(0, 4).map((it) => {
      const li = el("li", "pledge-activity-item");
      li.append(
        el("span", "pledge-activity-date", it.date ? formatAsOf(it.date) : "—"),
        el("span", "pledge-activity-text", it.text)
      );
      return li;
    })
  );
}

// Every hero affordance (stat tiles + pathway cards) routes through one place,
// so a new entry point only has to name a target rather than know how views
// and anchors work.
const PLEDGE_TARGETS = {
  // Targets the <details>, NOT its #rp-roster-section wrapper:
  // openAccordionsFor() walks ancestors, so a target pointing at the
  // wrapper leaves the disclosure shut. test_every_pledge_target_lands_open
  // guards the whole table against that mistake.
  roster: { view: "ratepayer", anchor: "rp-roster-details" },
  coverage: { view: "ratepayer", anchor: "rp-coverage-section" },
  commitments: { view: "ratepayer", anchor: "rp-commitments-section" },
  // `subtab` pins the cohort this entry point PROMISES. The Overview's
  // "Which sites have real evidence?" card means the assessed, five-commitment
  // scorecard -- but the cohort persists across navigations, so a reader who
  // last looked at "Never signed" was being handed that instead. Ordinary tab
  // switches still preserve whatever cohort the reader chose; only a target
  // that names one overrides it.
  scorecard: {
    view: "ratepayer",
    anchor: "rp-scorecard-section",
    subtab: { group: "rp-sites", key: "assessed" },
  },
  states: { view: "ratepayer", anchor: "rp-coverage-section" },
  explorer: { view: "explorer", anchor: null },
};

// --------------------------------------------------------------------------
// Accordions (.acc)
//
// One collapsible-section component, shared by every tab — see the ACCORDION
// block in styles.css for the markup contract. Two helpers keep the rest of
// the app from having to know it's a <details>.
// --------------------------------------------------------------------------

// Write the "N sites" chip in an accordion's summary, so a collapsed panel
// still says how much is inside. A count of 0 clears the chip rather than
// rendering "0" — .acc-count:empty hides it, and an empty panel's own body
// copy is the honest place to explain the absence.
function setAccCount(id, n, singular, plural, note) {
  const el = document.getElementById(id);
  if (!el) return;
  // Naive +"s" produced "302 signatorys" / "13 companys" in the first cut, so
  // any noun that doesn't pluralize by suffix passes its plural explicitly.
  const noun = n === 1 ? singular : plural || `${singular}s`;
  // `note` carries the as-of date for counts sourced from an external list.
  // DESIGN.md: a count from an external source must render its as-of date --
  // an undated "302" reads as a permanent fact about a living roster. The
  // as-of text also lives in the roster's body copy, but that is INSIDE the
  // collapsed panel, which is exactly when the chip is the only thing showing.
  el.textContent = n ? `${n} ${noun}${note ? ` · ${note}` : ""}` : "";
}

// "as of <date>" for roster-derived counts, or "" before the roster lands.
function rosterAsOfNote() {
  return state.rosterAsOf ? `as of ${formatAsOf(state.rosterAsOf)}` : "";
}

// Expand the accordion containing `node` (and any accordion containing THAT,
// for the roster's nested case). Deep links and the Overview pathway cards
// both scroll to sections that may be collapsed; without this the scroll
// lands on a closed bar and reads as a dead link.
function openAccordionsFor(node) {
  for (let el = node; el; el = el.parentElement) {
    if (el.tagName === "DETAILS" && el.classList.contains("acc")) el.open = true;
  }
}

// --------------------------------------------------------------------------
// Sub-tabs
//
// For sections that are ALTERNATIVES rather than a sequence — see the SUB-TABS
// block in styles.css for when to reach for this instead of an accordion.
//
// Same drift-safe shape as DETAIL_TABS: everything iterates this constant, so
// adding a cohort means adding markup + one array entry, and nothing else has
// to be taught the new key. Ids are conventional:
//   button  subtab-<group>-<key>
//   panel   subpane-<group>-<key>
// --------------------------------------------------------------------------

const SUBTAB_GROUPS = {
  "rp-sites": ["assessed", "unassessed", "pre-pledge", "non-signatory"],
  agg: ["company", "signatory", "state"],
};

// Last-clicked sub-tab per group, for this session only. Same reasoning as
// _lastDetailTab: a reader comparing cohorts across re-renders shouldn't be
// snapped back, but a reload should land on the primary cohort rather than
// whatever they last poked at.
const _activeSubtab = {};

function setActiveSubtab(group, key) {
  const keys = SUBTAB_GROUPS[group];
  if (!keys) return;
  if (!keys.includes(key)) key = keys[0];
  _activeSubtab[group] = key;
  for (const k of keys) {
    const btn = document.getElementById(`subtab-${group}-${k}`);
    const pane = document.getElementById(`subpane-${group}-${k}`);
    const active = k === key;
    if (btn) {
      btn.setAttribute("aria-selected", active ? "true" : "false");
      // Roving tabindex, per the ARIA tablist pattern: Tab enters the strip
      // once and lands on the ACTIVE tab; ArrowLeft/Right move within it.
      // Leaving every tab at 0 puts seven stops in the tab order.
      btn.tabIndex = active ? 0 : -1;
    }
    if (pane) pane.hidden = !active;
  }
}

function wireSubtabs() {
  for (const [group, keys] of Object.entries(SUBTAB_GROUPS)) {
    for (const key of keys) {
      const btn = document.getElementById(`subtab-${group}-${key}`);
      if (!btn || btn.dataset.wired === "1") continue;
      btn.dataset.wired = "1";
      btn.addEventListener("click", () => setActiveSubtab(group, key));
      // Arrow keys move between tabs in a tablist, per the ARIA pattern.
      btn.addEventListener("keydown", (e) => {
        const delta = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!delta) return;
        e.preventDefault();
        const next = keys[(keys.indexOf(key) + delta + keys.length) % keys.length];
        setActiveSubtab(group, next);
        const nextBtn = document.getElementById(`subtab-${group}-${next}`);
        if (nextBtn) nextBtn.focus();
      });
    }
  }
}

// Bare number for a sub-tab pill. setAccCount's "39 sites" phrasing is right in
// an accordion summary and far too wide in a tab.
function setSubtabCount(id, n) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = n ? String(n) : "";
}

function goToPledgeTarget(name) {
  const target = PLEDGE_TARGETS[name];
  if (!target) return;
  activateView(target.view);
  if (!target.anchor) return;
  // The Ratepayer view renders asynchronously; wait a frame so the anchor
  // exists before scrolling, and fail quietly if it never appears.
  requestAnimationFrame(() => {
    const anchor = document.getElementById(target.anchor);
    if (!anchor) return;
    openAccordionsFor(anchor);
    if (target.subtab) setActiveSubtab(target.subtab.group, target.subtab.key);
    anchor.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function wirePledgeTargets(root) {
  for (const btn of (root || document).querySelectorAll("[data-path-target]")) {
    if (btn.dataset.wired === "1") continue;
    btn.dataset.wired = "1";
    btn.addEventListener("click", () => goToPledgeTarget(btn.dataset.pathTarget));
  }
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

// --------------------------------------------------------------------------
// Shared PDF export helper — builds a styled HTML document and saves via
// html2pdf (same lazy-loader used by moratoriums).
// --------------------------------------------------------------------------
async function _exportToPDF(title, bodyHtml, filename) {
  const element = document.createElement("div");
  element.style.cssText = "font-family: Arial, sans-serif; font-size: 12px; color: #111;";
  element.innerHTML = `
    <h1 style="font-size:18px; margin-bottom:4px;">${escapeHtml(title)}</h1>
    <p style="color:#666; font-size:11px; margin-bottom:16px;">Exported: ${new Date().toLocaleDateString()} · datacenterbenefits.org</p>
    ${bodyHtml}
  `;
  const opt = {
    margin: 10,
    filename,
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { orientation: "landscape", unit: "mm", format: "a4" },
  };
  let lib;
  try { lib = await loadHtml2Pdf(); }
  catch (err) {
    console.error(err);
    alert("Could not load the PDF library. Check your connection and try again.");
    return;
  }
  lib().set(opt).from(element).save();
}

function _pdfTable(headers, rows) {
  const th = headers.map((h) => `<th style="background:#f0f0f0;border:1px solid #ddd;padding:6px;text-align:left;">${escapeHtml(h)}</th>`).join("");
  const trs = rows.map((r) =>
    `<tr>${r.map((c) => `<td style="border:1px solid #ddd;padding:5px;font-size:10px;">${escapeHtml(String(c ?? ""))}</td>`).join("")}</tr>`
  ).join("");
  return `<table style="width:100%;border-collapse:collapse;margin-top:8px;"><thead><tr>${th}</tr></thead><tbody>${trs}</tbody></table>`;
}

function _triggerDownload(csv, filename) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const today = new Date().toISOString().slice(0, 10);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.replace("TODAY", today);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// --------------------------------------------------------------------------
// Comparison view PDF export
// --------------------------------------------------------------------------
async function exportComparisonToPDF() {
  if (!state.companies.length || !state.claims.length) {
    alert("No data loaded yet."); return;
  }
  const counts = new Map();
  for (const c of state.claims) counts.set(`${c.company_slug}|${c.theme}`, (counts.get(`${c.company_slug}|${c.theme}`) || 0) + 1);
  const headers = ["Company", ...THEMES.map((t) => THEME_LABELS[t] || t)];
  const rows = state.companies.map((co) => [
    co.name,
    ...THEMES.map((t) => counts.get(`${co.slug}|${t}`) || 0),
  ]);
  const today = new Date().toISOString().slice(0, 10);
  await _exportToPDF(
    "Company × Theme Commitment Matrix",
    _pdfTable(headers, rows),
    `dcb-matrix-${today}.pdf`
  );
}

// --------------------------------------------------------------------------
// Explorer CSV + PDF export (projects list, respects current filters)
// --------------------------------------------------------------------------
function _filteredProjects() {
  const { company, status, stance, state: stateFilter, theme, constituency } = state.explorerFilters;
  let list = [...state.projects];
  if (company) list = list.filter((p) => p.company_slug === company);
  if (stateFilter) list = list.filter((p) => p.state === stateFilter);
  if (status) list = list.filter((p) => p.status === status);
  if (stance || constituency) {
    list = list.filter((p) => {
      const responses = state.responsesByProject.get(p.id) || [];
      if (stance && !responses.some((r) => r.stance === stance)) return false;
      if (constituency && !responses.some((r) => r.constituency === constituency)) return false;
      return true;
    });
  }
  return list;
}

function downloadExplorerCSV() {
  const projects = _filteredProjects();
  if (!projects.length) { alert("No projects match the current filters."); return; }
  const headers = ["company", "project_name", "city", "state", "status", "announced_year",
    "investment_usd", "power_mw", "jobs", "acreage", "claims_count",
    "positive_responses", "mixed_responses", "negative_responses", "source_url"];
  const rows = [headers.map(csvCell).join(",")];
  for (const p of projects) {
    const co = state.companiesBySlug.get(p.company_slug);
    const resp = state.responsesByProject.get(p.id) || [];
    const claims = state.claimsByProject.get(p.id) || [];
    rows.push([
      co ? co.name : p.company_slug,
      p.name, p.city, p.state, p.status,
      p.announced_year, p.claimed_investment_usd ?? "",
      p.power_mw ?? "", p.claimed_jobs ?? "", p.acreage ?? "",
      claims.length,
      resp.filter((r) => r.stance === "positive").length,
      resp.filter((r) => r.stance === "mixed").length,
      resp.filter((r) => r.stance === "negative").length,
      String(p.source_url),
    ].map(csvCell).join(","));
  }
  _triggerDownload(rows.join("\r\n"), "dcb-projects-TODAY.csv");
}

async function exportExplorerToPDF() {
  const projects = _filteredProjects();
  if (!projects.length) { alert("No projects match the current filters."); return; }
  const headers = ["Company", "Project", "City", "State", "Status", "Investment", "Power", "Jobs", "Responses"];
  const rows = projects.map((p) => {
    const co = state.companiesBySlug.get(p.company_slug);
    const resp = state.responsesByProject.get(p.id) || [];
    return [
      co ? co.name : p.company_slug, p.name, p.city, p.state, p.status,
      p.claimed_investment_usd ? formatUsd(p.claimed_investment_usd) : "—",
      p.power_mw != null ? formatPower(p.power_mw) : "—",
      p.claimed_jobs ?? "—",
      `+${resp.filter(r=>r.stance==="positive").length} ±${resp.filter(r=>r.stance==="mixed").length} -${resp.filter(r=>r.stance==="negative").length}`,
    ];
  });
  const today = new Date().toISOString().slice(0, 10);
  await _exportToPDF("Project Explorer", _pdfTable(headers, rows), `dcb-projects-${today}.pdf`);
}

// --------------------------------------------------------------------------
// Ratepayer PDF export
// --------------------------------------------------------------------------
async function exportRatepayerToPDF() {
  if (!state.projects.length) { alert("No data loaded yet."); return; }
  const assessed = ratepayerAssessedProjects();
  if (!assessed.length) { alert("No assessed projects to export."); return; }
  const headers = ["Company", "Project", "City", "State", "Status", "Assessment", "Source"];
  const rows = assessed.map((p) => {
    const co = state.companiesBySlug.get(p.company_slug);
    const rp = p.ratepayer;
    return [
      co ? co.name : p.company_slug, p.name, p.city, p.state, p.status,
      RATEPAYER_LABELS[rp.status] || rp.status,
      rp.summary || "",
    ];
  });
  const today = new Date().toISOString().slice(0, 10);
  await _exportToPDF("Ratepayer Protection Pledge Scorecard", _pdfTable(headers, rows), `ratepayer-pledge-${today}.pdf`);
}

// --------------------------------------------------------------------------
// Moratoriums CSV export
// --------------------------------------------------------------------------
function downloadMoratoriumsCSV() {
  if (!state.moratoriums || !state.moratoriums.length) { alert("No moratoriums loaded."); return; }
  const statusFilter = document.getElementById("moratorium-status-filter")?.value || "";
  const typeFilter = document.getElementById("moratorium-type-filter")?.value || "";
  let list = [...state.moratoriums];
  if (statusFilter) list = list.filter((m) => m.status === statusFilter);
  if (typeFilter) list = list.filter((m) => m.jurisdiction_type === typeFilter);
  const headers = ["id", "jurisdiction", "jurisdiction_type", "status", "enacted_date",
    "effective_date", "duration_description", "power_threshold_mw",
    "key_reasons", "bill_number", "sponsors", "enacted_by",
    "legislative_votes", "failure_reason", "summary", "source_url", "captured_at"];
  const rows = [headers.map(csvCell).join(",")];
  for (const m of list) {
    rows.push([
      m.id, m.jurisdiction, m.jurisdiction_type, m.status,
      m.enacted_date || "", m.effective_date || "",
      m.duration_description, m.power_threshold_mw ?? "",
      (m.key_reasons || []).join("; "),
      m.bill_number || "", m.sponsors ? m.sponsors.join("; ") : "",
      m.enacted_by || "", m.legislative_votes || m.city_council_vote || "",
      m.failure_reason || "", m.summary, String(m.source_url), m.captured_at,
    ].map(csvCell).join(","));
  }
  _triggerDownload(rows.join("\r\n"), "moratoriums-TODAY.csv");
}

// --------------------------------------------------------------------------
// Tariffs PDF export
// --------------------------------------------------------------------------
async function exportTariffsToPDF() {
  if (!state.tariffs || !state.tariffs.length) { alert("No tariffs loaded."); return; }
  const statusFilter = document.getElementById("tariff-status-filter")?.value || "";
  const stateFilter = document.getElementById("tariff-state-filter")?.value || "";
  let list = [...state.tariffs];
  if (statusFilter) list = list.filter((t) => t.status === statusFilter);
  if (stateFilter) list = list.filter((t) => t.state === stateFilter);
  const headers = ["Utility", "State", "Tariff", "Status", "Docket", "Min Load (MW)", "LBL Elements", "Summary"];
  const rows = list.map((t) => [
    t.utility, t.state, t.tariff_name,
    TARIFF_STATUS_LABELS[t.status] || t.status,
    t.docket_number || "—", t.min_load_mw ?? "—",
    `${tariffElementCount(t)} of ${TARIFF_PARAMETERS.length}`,
    (t.summary || "").substring(0, 150),
  ]);
  const today = new Date().toISOString().slice(0, 10);
  await _exportToPDF("State Utility Tariff Designs for Large Loads", _pdfTable(headers, rows), `utility-tariffs-${today}.pdf`);
}

// --------------------------------------------------------------------------
// Aggregate CSV + PDF export
// --------------------------------------------------------------------------
function downloadAggregateCSV() {
  if (!state.projects.length) { alert("No data loaded yet."); return; }
  const coRows = buildCompanyRollups();
  const stRows = buildStateRollups();
  let csv = "BY COMPANY\r\n";
  const coHeaders = ["company", "projects", "power_mw", "investment_usd", "jobs", "claims", "positive", "mixed", "negative"];
  csv += coHeaders.map(csvCell).join(",") + "\r\n";
  for (const r of coRows) {
    csv += [r.name, r.projects, r.power_mw ?? "", r.capex ?? "", r.jobs ?? "",
      r.claims, r.positive, r.mixed, r.negative].map(csvCell).join(",") + "\r\n";
  }
  csv += "\r\nBY STATE\r\n";
  const stHeaders = ["state", "companies", "projects", "power_mw", "investment_usd", "jobs", "positive", "mixed", "negative"];
  csv += stHeaders.map(csvCell).join(",") + "\r\n";
  for (const r of stRows) {
    csv += [r.state, r.companies, r.projects, r.power_mw ?? "", r.capex ?? "",
      r.jobs ?? "", r.positive, r.mixed, r.negative].map(csvCell).join(",") + "\r\n";
  }
  _triggerDownload(csv, "dcb-aggregate-TODAY.csv");
}

async function exportAggregateToPDF() {
  if (!state.projects.length) { alert("No data loaded yet."); return; }
  const coRows = buildCompanyRollups();
  const stRows = buildStateRollups();
  const coHtml = _pdfTable(
    ["Company", "Projects", "Power", "Investment", "Jobs", "Claims", "+", "±", "−"],
    coRows.map((r) => [r.name, r.projects,
      r.power_mw != null ? formatPower(r.power_mw) : "—",
      r.capex != null ? formatUsd(r.capex) : "—",
      r.jobs ?? "—", r.claims, r.positive, r.mixed, r.negative])
  );
  const stHtml = _pdfTable(
    ["State", "Companies", "Projects", "Power", "Investment", "Jobs", "+", "±", "−"],
    stRows.map((r) => [r.state, r.companies, r.projects,
      r.power_mw != null ? formatPower(r.power_mw) : "—",
      r.capex != null ? formatUsd(r.capex) : "—",
      r.jobs ?? "—", r.positive, r.mixed, r.negative])
  );
  const today = new Date().toISOString().slice(0, 10);
  await _exportToPDF(
    "Aggregate Totals",
    `<h2 style="font-size:14px;margin-top:0;">By Company</h2>${coHtml}<h2 style="font-size:14px;margin-top:16px;">By State</h2>${stHtml}`,
    `dcb-aggregate-${today}.pdf`
  );
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
  setAccCount("matrix-count", state.companies.length, "company", "companies");

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

  // Position below the cell, clamped inside the matrix-wrap.
  // Use getBoundingClientRect() AFTER making the tooltip visible so the
  // browser has done a layout pass and we get correct dimensions (not 0).
  const wrap = cellEl.closest(".matrix-wrap") || cellEl.offsetParent;
  const wrapRect = wrap ? wrap.getBoundingClientRect() : { left: 0, top: 0 };
  const cellRect = cellEl.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();

  const left = Math.min(
    cellRect.left - wrapRect.left,
    (wrap ? wrap.clientWidth : 600) - tooltipRect.width - 8
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
  wireBtn("explorer-csv-btn", downloadExplorerCSV);
  wireBtn("explorer-pdf-btn", exportExplorerToPDF);
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


// Wire up moratoriums view filter controls
function wireMoratoriumsFilters() {
  const statusFilter = document.getElementById("moratorium-status-filter");
  const typeFilter = document.getElementById("moratorium-type-filter");

  if (statusFilter && !statusFilter.dataset.wired) {
    statusFilter.dataset.wired = "1";
    statusFilter.addEventListener("change", () => {
      renderMoratoriumsView();
    });
  }
  if (typeFilter && !typeFilter.dataset.wired) {
    typeFilter.dataset.wired = "1";
    typeFilter.addEventListener("change", () => {
      renderMoratoriumsView();
    });
  }
}

function wireMoratoriumDetail() {
  const overlay = document.getElementById("moratorium-modal");
  const closeBtn = document.getElementById("moratorium-detail-close");
  if (closeBtn && !closeBtn.dataset.wired) {
    closeBtn.dataset.wired = "1";
    closeBtn.addEventListener("click", closeMoratoriumDetail);
  }
  if (overlay && !overlay.dataset.wired) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay || e.target.closest("[data-moratorium-close]")) {
        closeMoratoriumDetail();
      }
    });
    overlay.addEventListener("keydown", (e) => {
      if (e.key === "Tab" && !overlay.hidden) trapModalFocus(e, overlay);
    });
    overlay.dataset.wired = "1";
  }
  if (!document._moratoriumEscWired) {
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeMoratoriumDetail();
    });
    document._moratoriumEscWired = true;
  }

  wireBtn("moratoriums-csv-btn", downloadMoratoriumsCSV);
  wireBtn("moratoriums-pdf-btn", exportMoratoriumsToPDF);
}

// Lazy-load html2pdf from cdnjs on first use (the moratorium PDF export) rather
// than blocking first paint — and every Playwright `page.goto(..., "load")` — on
// an external CDN script in <head>. Cached so repeat clicks don't re-inject; the
// SRI hash is the official cdnjs value so the loaded bundle is still verified.
const HTML2PDF_SRC =
  "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js";
const HTML2PDF_SRI =
  "sha512-GsLlZN/3F2ErC5ifS5QtgpiJtWd43JWSuIgh7mbzZ8zBps+dvLusV+eNQATqgA/HdeKFVgA5v3S/cIrLF7QnIg==";
let _html2pdfPromise = null;
function loadHtml2Pdf() {
  if (window.html2pdf) return Promise.resolve(window.html2pdf);
  if (_html2pdfPromise) return _html2pdfPromise;
  _html2pdfPromise = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = HTML2PDF_SRC;
    s.integrity = HTML2PDF_SRI;
    s.crossOrigin = "anonymous";
    s.referrerPolicy = "no-referrer";
    s.onload = () => resolve(window.html2pdf);
    s.onerror = () => {
      _html2pdfPromise = null; // allow a retry on the next click
      reject(new Error("Failed to load html2pdf"));
    };
    document.head.appendChild(s);
  });
  return _html2pdfPromise;
}

// Hardcoded status palette for the standalone PDF artifact. html2canvas
// rasterizes a snapshot and won't reliably resolve the app's CSS custom
// properties, so the export carries its own (light-theme) colors.
const MPDF_STATUS = {
  enacted: { ink: "#2f7a4d", soft: "#e8f2ec", label: "Enacted" },
  proposed: { ink: "#b07024", soft: "#f6edda", label: "Proposed" },
  failed: { ink: "#a3372f", soft: "#f6e1de", label: "Failed" },
};

function _mpdfPill(status) {
  const s = MPDF_STATUS[status] || { ink: "#555", soft: "#eee", label: status };
  return `<span class="mpdf-pill" style="color:${s.ink};background:${s.soft}">${escapeHtml(s.label)}</span>`;
}

function _mpdfMiniBars(rows, accent) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return rows
    .map(
      (r) => `<div class="mpdf-bar-row">
        <span class="mpdf-bar-label">${escapeHtml(r.label)}</span>
        <span class="mpdf-bar-track"><span class="mpdf-bar-fill" style="width:${(r.value / max) * 100}%;background:${r.color || accent}"></span></span>
        <span class="mpdf-bar-val">${r.value}</span>
      </div>`
    )
    .join("");
}

function _mpdfSourcesList(m) {
  const items = [];
  if (m.source_url) {
    items.push({ url: String(m.source_url), title: m.source_title || "Primary source", primary: true });
  }
  (m.resources || []).forEach((r) => {
    if (r && r.url) items.push({ url: String(r.url), title: r.title || "Source", primary: false });
  });
  if (!items.length) return "";
  const seen = new Set();
  const lis = items
    .filter((i) => (seen.has(i.url) ? false : seen.add(i.url)))
    .map(
      (i) => `<li>${i.primary ? '<span class="mpdf-src-tag">primary</span>' : ""}<a href="${escapeAttr(i.url)}">${escapeHtml(i.title)}</a><span class="mpdf-src-url">${escapeHtml(i.url)}</span></li>`
    )
    .join("");
  return `<ul class="mpdf-src">${lis}</ul>`;
}

async function exportMoratoriumsToPDF() {
  if (!state.moratoriums || state.moratoriums.length === 0) {
    alert("No moratoriums to export");
    return;
  }

  const statusFilter = document.getElementById("moratorium-status-filter")?.value || "";
  const typeFilter = document.getElementById("moratorium-type-filter")?.value || "";

  let filtered = [...state.moratoriums];
  if (statusFilter) filtered = filtered.filter((m) => m.status === statusFilter);
  if (typeFilter) filtered = filtered.filter((m) => m.jurisdiction_type === typeFilter);

  // Sort: enacted (date desc) → proposed → failed, matching the on-screen table.
  filtered.sort((a, b) => {
    const order = { enacted: 0, proposed: 1, failed: 2 };
    if (order[a.status] !== order[b.status]) return order[a.status] - order[b.status];
    if (a.enacted_date && b.enacted_date) return new Date(b.enacted_date) - new Date(a.enacted_date);
    return a.jurisdiction.localeCompare(b.jurisdiction);
  });

  // ---- Aggregates for the summary page ----
  const count = (fn) => filtered.filter(fn).length;
  const statusRows = MORATORIUM_STATUSES.map((s) => ({
    label: MOR_STATUS_LABELS[s],
    value: count((m) => m.status === s),
    color: MPDF_STATUS[s].ink,
  })).filter((r) => r.value > 0);
  const jurOrder = ["state", "county", "city", "federal"];
  const jurLabels = { state: "State", county: "County", city: "City", federal: "Federal" };
  const jurRows = jurOrder
    .map((t) => ({ label: jurLabels[t], value: count((m) => m.jurisdiction_type === t) }))
    .filter((r) => r.value > 0);
  const reasonCounts = {};
  MORATORIUM_REASON_TYPES.forEach((r) => (reasonCounts[r] = 0));
  filtered.forEach((m) => (m.key_reasons || []).forEach((r) => {
    if (reasonCounts[r] !== undefined) reasonCounts[r]++;
  }));
  const reasonRows = MORATORIUM_REASON_TYPES.map((r) => ({
    label: MORATORIUM_REASON_LABELS[r] || r,
    value: reasonCounts[r],
  })).filter((r) => r.value > 0).sort((a, b) => b.value - a.value);

  const today = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  const filterBits = [];
  if (statusFilter) filterBits.push(`status: ${MOR_STATUS_LABELS[statusFilter] || statusFilter}`);
  if (typeFilter) filterBits.push(`level: ${jurLabels[typeFilter] || typeFilter}`);
  const filterNote = filterBits.length ? ` · filtered by ${filterBits.join(", ")}` : "";

  // ---- Directory table rows ----
  const tableRows = filtered
    .map((m, i) => {
      const reasons = (m.key_reasons || []).map((r) => MORATORIUM_REASON_LABELS[r] || r).join(", ");
      const dur = escapeHtml(m.duration_description || "—");
      const eff = m.enacted_date || m.effective_date || "—";
      return `<tr class="${i % 2 ? "alt" : ""}">
        <td class="jur">${escapeHtml(m.jurisdiction)}${m.bill_number ? `<span class="billid">${escapeHtml(m.bill_number)}</span>` : ""}</td>
        <td>${escapeHtml(m.jurisdiction_type)}</td>
        <td>${_mpdfPill(m.status)}</td>
        <td>${dur}</td>
        <td class="num">${escapeHtml(eff)}</td>
        <td class="reasons">${escapeHtml(reasons || "—")}</td>
      </tr>`;
    })
    .join("");

  // ---- Per-record detail cards (grouped by status) ----
  const cards = filtered
    .map((m) => {
      const meta = [];
      meta.push(`${escapeHtml(m.jurisdiction_type)}`);
      if (m.duration_description) meta.push(escapeHtml(m.duration_description));
      if (m.enacted_date) meta.push(`enacted ${escapeHtml(m.enacted_date)}`);
      else if (m.effective_date) meta.push(`effective ${escapeHtml(m.effective_date)}`);
      if (m.power_threshold_mw) meta.push(`≥ ${m.power_threshold_mw} MW`);
      if (m.bill_number) meta.push(escapeHtml(m.bill_number));
      const vote = m.legislative_votes || m.city_council_vote;
      if (vote) meta.push(`vote ${escapeHtml(vote)}`);
      const reasonChips = (m.key_reasons || [])
        .map((r) => `<span class="mpdf-chip">${escapeHtml(MORATORIUM_REASON_LABELS[r] || r)}</span>`)
        .join("");
      const failNote = m.status === "failed" && m.failure_reason
        ? `<p class="mpdf-note">Why it failed: ${escapeHtml(m.failure_reason)}</p>` : "";
      return `<div class="mpdf-card">
        <div class="mpdf-card-head">
          <h3>${escapeHtml(m.jurisdiction)}</h3>
          ${_mpdfPill(m.status)}
        </div>
        <div class="mpdf-card-meta">${meta.join(" &nbsp;·&nbsp; ")}</div>
        ${reasonChips ? `<div class="mpdf-chips">${reasonChips}</div>` : ""}
        <p class="mpdf-card-summary">${escapeHtml(m.summary || "")}</p>
        ${failNote}
        ${_mpdfSourcesList(m)}
      </div>`;
    })
    .join("");

  const style = `<style>
    .mpdf { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: #1a1a1a; font-size: 11px; line-height: 1.45; -webkit-font-feature-settings: "tnum" 1; font-feature-settings: "tnum" 1; }
    .mpdf h1, .mpdf h2, .mpdf h3 { font-family: Georgia, "Times New Roman", serif; }
    .mpdf-cover { border-bottom: 2px solid #1a1a1a; padding-bottom: 14px; margin-bottom: 18px; }
    .mpdf-kicker { text-transform: uppercase; letter-spacing: 0.09em; font-size: 9.5px; color: #6b6b6b; font-weight: 600; }
    .mpdf-cover h1 { font-size: 27px; margin: 5px 0 6px; line-height: 1.1; color: #111; }
    .mpdf-dek { font-size: 12.5px; color: #3a3a3a; max-width: 34em; margin: 0 0 9px; line-height: 1.4; }
    .mpdf-meta { font-size: 10px; color: #6b6b6b; }
    .mpdf-stats { display: flex; gap: 9px; margin: 16px 0 14px; }
    .mpdf-stat { flex: 1; border: 1px solid #e2e2e2; border-radius: 7px; padding: 9px 11px; border-top: 3px solid #999; }
    .mpdf-stat .n { display: block; font-family: Georgia, serif; font-size: 22px; font-weight: 700; line-height: 1; }
    .mpdf-stat .l { display: block; font-size: 9.5px; color: #6b6b6b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 3px; }
    .mpdf-summary { display: flex; gap: 22px; margin: 4px 0 8px; }
    .mpdf-summary > div { flex: 1; }
    .mpdf-summary h2 { font-size: 12px; margin: 0 0 7px; color: #333; }
    .mpdf-bar-row { display: grid; grid-template-columns: 82px 1fr 20px; align-items: center; gap: 6px; margin-bottom: 4px; }
    .mpdf-bar-label { font-size: 9.5px; text-align: right; color: #333; }
    .mpdf-bar-track { background: #eee; border-radius: 3px; height: 11px; overflow: hidden; }
    .mpdf-bar-fill { display: block; height: 100%; }
    .mpdf-bar-val { font-size: 9.5px; font-weight: 700; }
    .mpdf-pill { display: inline-block; padding: 1px 7px; border-radius: 999px; font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; }
    h2.mpdf-h2 { font-size: 15px; margin: 20px 0 8px; padding-bottom: 4px; border-bottom: 1px solid #ddd; color: #111; }
    table.mpdf-table { width: 100%; border-collapse: collapse; font-size: 10px; }
    table.mpdf-table th { text-align: left; font-family: Georgia, serif; font-size: 9.5px; text-transform: uppercase; letter-spacing: 0.04em; color: #555; border-bottom: 1.5px solid #333; padding: 5px 6px; }
    table.mpdf-table td { padding: 5px 6px; border-bottom: 1px solid #eee; vertical-align: top; }
    table.mpdf-table tr.alt td { background: #fafafa; }
    table.mpdf-table td.jur { font-weight: 600; }
    table.mpdf-table td .billid { display: block; font-size: 8.5px; color: #888; font-weight: 400; }
    table.mpdf-table td.reasons { color: #555; font-size: 9px; }
    .mpdf-cards { margin-top: 6px; }
    .mpdf-card { border: 1px solid #e5e5e5; border-left: 3px solid #bbb; border-radius: 6px; padding: 9px 12px; margin-bottom: 9px; page-break-inside: avoid; }
    .mpdf-card-head { display: flex; align-items: center; gap: 8px; justify-content: space-between; }
    .mpdf-card-head h3 { font-size: 13.5px; margin: 0; color: #111; }
    .mpdf-card-meta { font-size: 9.5px; color: #666; margin: 3px 0 5px; }
    .mpdf-chips { margin-bottom: 5px; }
    .mpdf-chip { display: inline-block; background: #eef1f4; color: #34506b; font-size: 8.5px; padding: 1px 6px; border-radius: 4px; margin: 0 3px 3px 0; }
    .mpdf-card-summary { margin: 0 0 5px; font-size: 10.5px; color: #2a2a2a; line-height: 1.45; }
    .mpdf-note { margin: 0 0 5px; font-size: 9.5px; color: #a3372f; }
    ul.mpdf-src { list-style: none; margin: 4px 0 0; padding: 6px 0 0; border-top: 1px dashed #e0e0e0; }
    ul.mpdf-src li { font-size: 9px; margin-bottom: 3px; line-height: 1.35; }
    ul.mpdf-src a { color: #2f5d8a; text-decoration: none; font-weight: 600; }
    .mpdf-src-tag { display: inline-block; background: #2f5d8a; color: #fff; font-size: 7.5px; text-transform: uppercase; letter-spacing: 0.04em; padding: 0 4px; border-radius: 3px; margin-right: 5px; vertical-align: middle; }
    .mpdf-src-url { display: block; color: #999; font-size: 8px; word-break: break-all; }
    .mpdf-section { page-break-before: always; }
    .mpdf-foot { margin-top: 8px; font-size: 8.5px; color: #999; border-top: 1px solid #eee; padding-top: 6px; }
  </style>`;

  const html = `${style}<div class="mpdf">
    <div class="mpdf-cover">
      <div class="mpdf-kicker">Data Center Community Benefits · Policy Tracker</div>
      <h1>Data Center Moratoriums &amp; Restrictions</h1>
      <p class="mpdf-dek">A field guide to enacted, proposed, and failed limits on data center development across U.S. city, county, state, and federal jurisdictions.</p>
      <div class="mpdf-meta">As of ${today} · ${filtered.length} record${filtered.length === 1 ? "" : "s"}${filterNote}</div>
    </div>

    <div class="mpdf-stats">
      <div class="mpdf-stat" style="border-top-color:#333"><span class="n">${filtered.length}</span><span class="l">Total</span></div>
      <div class="mpdf-stat" style="border-top-color:${MPDF_STATUS.enacted.ink}"><span class="n">${count((m) => m.status === "enacted")}</span><span class="l">Enacted</span></div>
      <div class="mpdf-stat" style="border-top-color:${MPDF_STATUS.proposed.ink}"><span class="n">${count((m) => m.status === "proposed")}</span><span class="l">Proposed</span></div>
      <div class="mpdf-stat" style="border-top-color:${MPDF_STATUS.failed.ink}"><span class="n">${count((m) => m.status === "failed")}</span><span class="l">Failed</span></div>
    </div>

    <div class="mpdf-summary">
      <div><h2>By jurisdiction level</h2>${_mpdfMiniBars(jurRows, "#2f5d8a")}</div>
      <div><h2>Concerns cited</h2>${_mpdfMiniBars(reasonRows, "#2f5d8a")}</div>
    </div>

    <h2 class="mpdf-h2">Directory</h2>
    <table class="mpdf-table">
      <thead><tr><th>Jurisdiction</th><th>Level</th><th>Status</th><th>Duration</th><th>Effective</th><th>Concerns</th></tr></thead>
      <tbody>${tableRows}</tbody>
    </table>

    <h2 class="mpdf-h2 mpdf-section">Record details &amp; sources</h2>
    <div class="mpdf-cards">${cards}</div>

    <div class="mpdf-foot">Generated from the Data Center Community Benefits dashboard. Every record links to its primary government or authoritative source. Stance and status reflect the capture date; policies change — verify against the linked source before relying on any record.</div>
  </div>`;

  const element = document.createElement("div");
  element.innerHTML = html;

  const opt = {
    margin: [12, 12, 14, 12],
    filename: `moratoriums-${new Date().toISOString().split("T")[0]}.pdf`,
    // scale 1.6 + jpeg 0.9 keeps 10px table text crisp while roughly halving the
    // file vs scale:2 (a 90-record export with per-record cards runs ~30 pages).
    image: { type: "jpeg", quality: 0.9 },
    html2canvas: { scale: 1.6, useCORS: true, letterRendering: true },
    jsPDF: { orientation: "portrait", unit: "mm", format: "a4", compress: true },
    pagebreak: { mode: ["css", "legacy"], avoid: ".mpdf-card" },
  };

  let lib;
  try {
    lib = await loadHtml2Pdf();
  } catch (err) {
    console.error(err);
    alert("Could not load the PDF library. Check your connection and try again.");
    return;
  }
  lib().set(opt).from(element).save();
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
  setAccCount("explorer-filter-count", items.length, "site");

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
  const moratoriums = state.projectMoratoriums?.get(p.id) || [];

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

  const moratoriumBadges = moratoriums
    .map((m) => `<span class="badge badge-moratorium badge-moratorium-${m.status}" title="Affected by ${m.jurisdiction} ${m.status} moratorium">${escapeHtml(m.jurisdiction)}</span>`)
    .join("");

  li.innerHTML = `
    <p class="project-name">${escapeHtml(p.name)}</p>
    <div class="project-meta">
      <span>${escapeHtml(co ? co.name : p.company_slug)}</span>
      <span>${escapeHtml(p.city)}, ${escapeHtml(p.state)}</span>
      <span>${escapeHtml(STATUS_LABELS[p.status] || p.status)}</span>
    </div>
    ${stanceDots ? `<div class="project-stance-row">${stanceDots}</div>` : ""}
    ${moratoriumBadges ? `<div class="project-moratoriums-row">${moratoriumBadges}</div>` : ""}
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
    // Skip projects without coordinates
    if (p.lat === undefined || p.lon === undefined || p.lat === null || p.lon === null) {
      continue;
    }

    const color = cssVar(`--co-${p.company_slug}`) || cssVar("--accent");

    // Scale marker radius by power capacity (5–20 MW = size 6, 1000+ MW = size 14)
    let radius = 8;
    if (p.power_mw) {
      radius = Math.min(14, Math.max(6, 6 + (p.power_mw / 100)));
    }

    // Opacity reflects status: announced=0.4, construction=0.65, operational=0.9
    const opacityMap = { announced: 0.4, construction: 0.65, operational: 0.9 };
    const fillOpacity = opacityMap[p.status] || 0.65;

    // Border weight reflects status: more prominent for operational
    const weight = p.status === 'operational' ? 3 : 2;

    const marker = L.circleMarker([p.lat, p.lon], {
      radius,
      color,
      fillColor: color,
      fillOpacity,
      weight,
      className: `marker-${p.status}`,
    });

    // Rich tooltip with key metrics
    let tooltip = `<strong>${p.name}</strong><br>`;
    tooltip += `<small>${p.city}, ${p.state} · ${p.status}</small>`;
    if (p.power_mw) tooltip += `<br>⚡ ${p.power_mw} MW`;
    if (p.claimed_jobs) tooltip += `<br>👥 ${p.claimed_jobs} jobs`;
    if (p.claimed_investment_usd) tooltip += `<br>💰 $${(p.claimed_investment_usd / 1e9).toFixed(1)}B`;

    marker.bindTooltip(tooltip, { direction: "top" });
    marker.on("click", () => selectProject(p.id));
    marker.addTo(state.map);
    state.markers.set(p.id, marker);
  }

  // Calculate bounds only for projects with valid coordinates
  const validItems = items.filter((p) => p.lat !== undefined && p.lon !== undefined && p.lat !== null && p.lon !== null);
  if (validItems.length > 0) {
    const bounds = L.latLngBounds(validItems.map((p) => [p.lat, p.lon]));
    state.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 7 });
  }

  // Add map legend
  renderMapLegend();
}

function renderMapLegend() {
  if (!state.map || !window.L) return;

  // Remove existing legend
  const existing = document.querySelector(".map-legend");
  if (existing) existing.remove();

  // Create legend container
  const legend = L.control({ position: "bottomright" });
  legend.onAdd = function () {
    const div = L.DomUtil.create("div", "map-legend");
    div.innerHTML = `
      <div class="legend-content">
        <h4>Map Legend</h4>
        <div class="legend-section">
          <strong>Marker Size</strong>
          <div class="legend-item"><span class="legend-dot" style="width: 8px; height: 8px;"></span> &lt;100 MW</div>
          <div class="legend-item"><span class="legend-dot" style="width: 11px; height: 11px;"></span> 100–500 MW</div>
          <div class="legend-item"><span class="legend-dot" style="width: 14px; height: 14px;"></span> 1000+ MW</div>
        </div>
        <div class="legend-section">
          <strong>Status</strong>
          <div class="legend-item"><span class="legend-item-opacity-40">●</span> Announced</div>
          <div class="legend-item"><span class="legend-item-opacity-65">●</span> Under Construction</div>
          <div class="legend-item"><span class="legend-item-opacity-90">●</span> Operational</div>
        </div>
      </div>
    `;
    L.DomEvent.disableClickPropagation(div);
    return div;
  };
  legend.addTo(state.map);
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

  renderPledgeCommitments();
  renderCoverageStats();
  renderStateChips();
  renderSignatoryRoster();
  renderRatepayerLegend();
  renderRatepayerScorecard();
}

// --------------------------------------------------------------------------
// 1. The pledge — five commitments as the page's spine
// --------------------------------------------------------------------------

// Tally how the assessed sites score on each of the five principles.
// Sites without a per-principle assessment are counted in NOTHING — an
// unassessed site is a gap in our work, not a passing or failing grade, and
// rolling it into "unknown" would make the gap look like a finding.
function principleTallies() {
  const tallies = {};
  for (const key of PLEDGE_PRINCIPLES) {
    tallies[key] = { met: 0, partial: 0, not_met: 0, unknown: 0, assessed: 0 };
  }
  for (const p of state.projects || []) {
    const principles = p.ratepayer && p.ratepayer.principles;
    if (!principles) continue;
    for (const key of PLEDGE_PRINCIPLES) {
      const entry = principles[key];
      if (!entry || !entry.status) continue;
      const bucket = tallies[key];
      if (bucket[entry.status] === undefined) continue;
      bucket[entry.status] += 1;
      bucket.assessed += 1;
    }
  }
  return tallies;
}

const ROMAN = ["I", "II", "III", "IV", "V"];

function renderPledgeCommitments() {
  const ol = document.getElementById("rp-commitments");
  if (!ol) return;
  const tallies = principleTallies();
  setAccCount("rp-commitments-count", PLEDGE_PRINCIPLES.length, "commitment");

  ol.replaceChildren(
    ...PLEDGE_PRINCIPLES.map((key, i) => {
      const t = tallies[key];
      const li = el("li", "rp-commit");
      li.append(el("span", "rp-commit-num", ROMAN[i] || String(i + 1)));

      const body = el("div", "rp-commit-body");
      body.append(
        el("h4", "rp-commit-title", PLEDGE_PRINCIPLE_LABELS[key] || key),
        el("p", "rp-commit-dek", PLEDGE_PRINCIPLE_DESCRIPTIONS[key] || "")
      );

      const meter = el("div", "rp-commit-meter");
      if (t.assessed === 0) {
        meter.append(el("span", "rp-commit-empty", "No sites assessed on this commitment yet"));
      } else {
        for (const status of PLEDGE_PRINCIPLE_STATUSES) {
          if (!t[status]) continue;
          const chip = el("span", `rp-commit-chip is-${status}`);
          chip.append(
            el("span", "rp-commit-chip-num", String(t[status])),
            el(
              "span",
              "rp-commit-chip-lbl",
              PLEDGE_PRINCIPLE_STATUS_LABELS[status] || status
            )
          );
          meter.append(chip);
        }
      }
      body.append(meter);
      li.append(body);
      return li;
    })
  );
}

// --------------------------------------------------------------------------
// 2. Coverage — categories + states
// --------------------------------------------------------------------------

function renderCoverageStats() {
  const ul = document.getElementById("rp-category-stats");
  if (!ul) return;

  if (!state.signatoriesLoaded) {
    ul.replaceChildren(el("li", "rp-cat-stat", "Loading roster…"));
    return;
  }

  const counts = signatoryCounts();
  setAccCount(
    "rp-coverage-count",
    (state.signatories || []).length,
    "signatory",
    "signatories",
    rosterAsOfNote()
  );
  ul.replaceChildren(
    ...SIGNATORY_CATEGORIES.map((cat) => {
      const li = el("li", `rp-cat-stat cat-${cat}`);
      li.append(
        el("span", "rp-cat-num", String(counts[cat] || 0)),
        el("span", "rp-cat-lbl", SIGNATORY_CATEGORY_SHORT[cat] || cat)
      );
      return li;
    })
  );

  const sub = document.getElementById("rp-roster-sub");
  if (sub && state.rosterAsOf) {
    sub.textContent =
      `${counts.organizations} organizations and ${counts.governor} governors, ` +
      `as captured from the White House page on ${formatAsOf(state.rosterAsOf)}.`;
  }

  // Surface the source page's self-disagreement rather than quietly picking a
  // number. See SignatoriesPayload.drift_note.
  const note = document.getElementById("rp-drift-note");
  if (note) {
    if (state.rosterDriftNote) {
      note.textContent = state.rosterDriftNote;
      note.hidden = false;
    } else {
      note.hidden = true;
    }
  }
}

// Every state we can say something about: a governor signature, a tracked
// site, a tariff, or a moratorium. Governor states with no records still get
// a chip — an honest empty is more useful than an absent one, because "my
// governor signed and nothing is on file" is itself the answer.
// "XX" is the sentinel a few records use for virtual / multi-site partnerships
// with no physical location (city "Virtual", null lat/lon). It is not a place,
// so it must never become a chip.
const NON_GEOGRAPHIC_STATE = "XX";

function coverageStates() {
  const states = new Map();
  const touch = (code) => {
    if (!code) return null;
    const key = String(code).toUpperCase();
    if (key === NON_GEOGRAPHIC_STATE) return null;
    if (!states.has(key)) {
      states.set(key, { code: key, governor: null, projects: 0, tariffs: 0, moratoriums: 0 });
    }
    return states.get(key);
  };

  for (const [code, rec] of state.governorByState || []) {
    const entry = touch(code);
    if (entry) entry.governor = rec;
  }

  // Prefer the precomputed rollup: it covers all three record types, whereas
  // the live arrays only hold whatever the visitor's tab history happens to
  // have loaded. Falls back to live counts when the rollup is unavailable.
  if (state.coverageLoaded) {
    for (const [code, counts] of Object.entries(state.coverage || {})) {
      const entry = touch(code);
      if (!entry) continue;
      entry.projects = counts.projects || 0;
      entry.tariffs = counts.tariffs || 0;
      entry.moratoriums = counts.moratoriums || 0;
    }
  } else {
    for (const p of state.projects || []) {
      const entry = touch(p.state);
      if (entry) entry.projects += 1;
    }
    for (const t of state.tariffs || []) {
      const entry = touch(t.state);
      if (entry) entry.tariffs += 1;
    }
    for (const m of state.moratoriums || []) {
      const entry = touch(moratoriumStateCode(m));
      if (entry) entry.moratoriums += 1;
    }
  }

  return [...states.values()].sort((a, b) => {
    // Governor states first (that is the pledge-relevant cohort), then by how
    // much we can actually show, then alphabetically.
    if (!!b.governor !== !!a.governor) return b.governor ? 1 : -1;
    const load = (s) => s.projects + s.tariffs + s.moratoriums;
    const d = load(b) - load(a);
    if (d !== 0) return d;
    return a.code.localeCompare(b.code);
  });
}

function renderStateChips() {
  const wrap = document.getElementById("rp-state-chips");
  if (!wrap) return;
  const entries = coverageStates();

  wrap.replaceChildren(
    ...entries.map((s) => {
      const records = s.projects + s.tariffs + s.moratoriums;
      const btn = el("button", `rp-state-chip${records ? "" : " is-empty"}`);
      btn.type = "button";
      btn.dataset.stateCode = s.code;
      btn.append(el("span", "rp-state-code", s.code));
      if (s.governor) {
        const mark = el("span", "rp-state-gov", "★");
        mark.setAttribute("aria-hidden", "true");
        btn.append(mark);
      }
      const parts = [];
      if (s.projects) parts.push(`${s.projects} site${s.projects === 1 ? "" : "s"}`);
      if (s.tariffs) parts.push(`${s.tariffs} tariff${s.tariffs === 1 ? "" : "s"}`);
      if (s.moratoriums) parts.push(`${s.moratoriums} moratorium${s.moratoriums === 1 ? "" : "s"}`);
      btn.append(el("span", "rp-state-meta", parts.length ? parts.join(" · ") : "No records yet"));
      btn.setAttribute(
        "aria-label",
        `${s.code}${s.governor ? ", governor signed" : ""} — ` +
          (parts.length ? parts.join(", ") : "no tracked records yet")
      );
      btn.addEventListener("click", () => openStatePanel(s.code));
      return btn;
    })
  );
}

// --------------------------------------------------------------------------
// 3. Signatory roster — the full published list
// --------------------------------------------------------------------------

// --------------------------------------------------------------------------
// State panel (deep-linkable at #state/XX)
// --------------------------------------------------------------------------

const STATE_NAMES = {
  AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California",
  CO: "Colorado", CT: "Connecticut", DE: "Delaware", FL: "Florida", GA: "Georgia",
  HI: "Hawaii", ID: "Idaho", IL: "Illinois", IN: "Indiana", IA: "Iowa",
  KS: "Kansas", KY: "Kentucky", LA: "Louisiana", ME: "Maine", MD: "Maryland",
  MA: "Massachusetts", MI: "Michigan", MN: "Minnesota", MS: "Mississippi",
  MO: "Missouri", MT: "Montana", NE: "Nebraska", NV: "Nevada", NH: "New Hampshire",
  NJ: "New Jersey", NM: "New Mexico", NY: "New York", NC: "North Carolina",
  ND: "North Dakota", OH: "Ohio", OK: "Oklahoma", OR: "Oregon", PA: "Pennsylvania",
  RI: "Rhode Island", SC: "South Carolina", SD: "South Dakota", TN: "Tennessee",
  TX: "Texas", UT: "Utah", VT: "Vermont", VA: "Virginia", WA: "Washington",
  WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming", DC: "District of Columbia",
};

// Moratoriums carry an explicit `state_code` (backfilled in v2) rather than a
// parsed one — `jurisdiction` is a bare place name with no state in it.
function moratoriumStateCode(m) {
  return m && m.state_code ? String(m.state_code).toUpperCase() : null;
}

// Utility signatories operating in a state, resolved through the curated alias
// map on the tariffs filed there. Exact joins only — no name fuzzing.
function stateUtilitySignatories(code) {
  const found = new Map();
  for (const t of state.tariffs || []) {
    if (String(t.state || "").toUpperCase() !== code) continue;
    const sig = state.signatoryByUtilityAlias.get(t.utility);
    if (sig) found.set(sig.id, sig);
  }
  return [...found.values()];
}

// Open the panel for a state. Loads whatever payloads are still missing first,
// because a visitor can reach this from the landing page without ever having
// opened the Tariffs or Moratoriums tabs — and a panel that silently showed
// "no tariffs" because the payload had not loaded would be a lie.
async function openStatePanel(code) {
  const key = String(code || "").toUpperCase();
  if (!STATE_NAMES[key]) return;

  const overlay = document.getElementById("state-modal");
  const body = document.getElementById("sd-body");
  if (!overlay || !body) return;

  state._stateReturnFocus =
    document.activeElement instanceof HTMLElement ? document.activeElement : null;
  overlay.hidden = false;
  document.body.classList.add("state-modal-open");
  document.getElementById("sd-name").textContent = STATE_NAMES[key];
  body.replaceChildren(el("p", "state-loading", "Loading records…"));
  const closeBtn = document.getElementById("state-detail-close");
  if (closeBtn) closeBtn.focus();
  history.replaceState(null, "", `#state/${key}`);

  await Promise.all([
    loadProjectData(),
    loadSignatoryData(),
    state.moratoriumsLoaded ? Promise.resolve() : loadMoratoriumsData(),
    state.tariffsLoaded ? Promise.resolve() : loadTariffsData(),
  ]).catch((err) => console.error("State panel data load failed:", err));

  // Bail if the user closed the panel (or opened another state) while loading.
  if (overlay.hidden || !window.location.hash.endsWith(`/${key}`)) return;
  renderStatePanel(key);
}

function renderStatePanel(code) {
  const body = document.getElementById("sd-body");
  if (!body) return;

  const gov = state.governorByState.get(code);
  const govLine = document.getElementById("sd-governor");
  if (govLine) {
    govLine.replaceChildren();
    if (gov) {
      govLine.append(
        el("span", "sd-gov-name", `${gov.name} signed the governors' addendum`)
      );
      const a = document.createElement("a");
      a.href = String(gov.source_url);
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = "sd-gov-link";
      a.textContent = "Source ↗";
      govLine.append(a);
    } else {
      govLine.append(
        el(
          "span",
          "sd-gov-none",
          "No governor signature on the addendum — records below are shown for context."
        )
      );
    }
  }

  const projects = (state.projects || []).filter(
    (p) => String(p.state || "").toUpperCase() === code
  );
  const tariffs = (state.tariffs || []).filter(
    (t) => String(t.state || "").toUpperCase() === code
  );
  const moratoriums = (state.moratoriums || []).filter(
    (m) => moratoriumStateCode(m) === code
  );
  const utilities = stateUtilitySignatories(code);

  const sections = [
    {
      title: "Data-center sites",
      empty: "No tracked sites in this state yet.",
      items: projects.map((p) => ({
        label: p.name,
        meta: [
          (state.companiesBySlug.get(p.company_slug) || {}).name || p.company_slug,
          STATUS_LABELS[p.status] || p.status,
          p.ratepayer ? RATEPAYER_LABELS[p.ratepayer.status] : null,
        ]
          .filter(Boolean)
          .join(" · "),
        onClick: () => {
          closeStatePanel();
          activateView("explorer");
          selectProject(p.id);
        },
      })),
    },
    {
      title: "Utility tariffs",
      empty: "No large-load tariff on file for this state yet.",
      items: tariffs.map((t) => ({
        label: t.tariff_name,
        meta: [t.utility, TARIFF_STATUS_LABELS[t.status] || t.status]
          .filter(Boolean)
          .join(" · "),
        onClick: () => {
          closeStatePanel();
          activateView("tariffs");
          requestAnimationFrame(() => showTariffDetail(t));
        },
      })),
    },
    {
      title: "Moratoriums",
      empty: "No moratorium records for this state yet.",
      items: moratoriums.map((m) => ({
        label: m.jurisdiction,
        meta: [
          m.jurisdiction_type,
          MOR_STATUS_LABELS[m.status] || m.status,
          m.duration_description,
        ]
          .filter(Boolean)
          .join(" · "),
        onClick: () => {
          closeStatePanel();
          activateView("moratoriums");
          requestAnimationFrame(() => showMoratoriumDetail(m));
        },
      })),
    },
    {
      title: "Utility signatories",
      empty:
        "No pledge signatory matched to a tariff in this state. Absence here means " +
        "no exact match in the roster, not that no local utility signed.",
      items: utilities.map((u) => ({
        label: u.name,
        meta: SIGNATORY_TRACK_LABELS[u.signed_track] || u.signed_track,
        onClick: null,
      })),
    },
  ];

  body.replaceChildren(
    ...sections.map((sec) => {
      const wrap = el("section", "sd-section");
      const h = el("h4", "sd-section-title", sec.title);
      const n = el("span", "sd-section-count", String(sec.items.length));
      h.append(n);
      wrap.append(h);

      if (!sec.items.length) {
        wrap.append(el("p", "sd-empty", sec.empty));
        return wrap;
      }

      const ul = el("ul", "sd-list");
      for (const item of sec.items) {
        const li = el("li", "sd-item");
        if (item.onClick) {
          const btn = el("button", "sd-item-btn");
          btn.type = "button";
          btn.append(el("span", "sd-item-label", item.label));
          if (item.meta) btn.append(el("span", "sd-item-meta", item.meta));
          btn.addEventListener("click", item.onClick);
          li.append(btn);
        } else {
          li.append(el("span", "sd-item-label", item.label));
          if (item.meta) li.append(el("span", "sd-item-meta", item.meta));
        }
        ul.append(li);
      }
      wrap.append(ul);
      return wrap;
    })
  );
}

function closeStatePanel() {
  const overlay = document.getElementById("state-modal");
  if (!overlay || overlay.hidden) return;
  overlay.hidden = true;
  document.body.classList.remove("state-modal-open");
  if (window.location.hash.startsWith("#state/")) {
    history.replaceState(null, "", "#ratepayer");
  }
  const ret = state._stateReturnFocus;
  state._stateReturnFocus = null;
  if (ret && typeof ret.focus === "function") ret.focus();
}

function wireStatePanel() {
  const overlay = document.getElementById("state-modal");
  const closeBtn = document.getElementById("state-detail-close");
  if (closeBtn && !closeBtn.dataset.wired) {
    closeBtn.dataset.wired = "1";
    closeBtn.addEventListener("click", closeStatePanel);
  }
  if (overlay && !overlay.dataset.wired) {
    overlay.dataset.wired = "1";
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay || e.target.closest("[data-state-close]")) {
        closeStatePanel();
      }
    });
    // Without this, Tab walks straight out of an aria-modal dialog into the
    // page behind it — the other two modals already guard against that.
    overlay.addEventListener("keydown", (e) => {
      if (e.key === "Tab" && !overlay.hidden) trapModalFocus(e, overlay);
    });
  }
  if (!document.body.dataset.stateEscWired) {
    document.body.dataset.stateEscWired = "1";
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeStatePanel();
    });
  }
}

const _rosterFilter = { q: "", category: "" };

function renderSignatoryRoster() {
  const ul = document.getElementById("rp-roster");
  if (!ul) return;

  renderRosterFilters();

  const q = _rosterFilter.q.trim().toLowerCase();
  const rows = (state.signatories || []).filter((s) => {
    if (_rosterFilter.category && s.category !== _rosterFilter.category) return false;
    if (!q) return true;
    return (
      s.name.toLowerCase().includes(q) ||
      (s.website_domain || "").toLowerCase().includes(q)
    );
  });

  const count = document.getElementById("rp-roster-count");
  if (count) {
    count.textContent = `Showing ${rows.length} of ${(state.signatories || []).length}`;
  }
  // Summary chip counts the WHOLE roster, not the filtered subset — it has to
  // read correctly while the panel is collapsed and no filter is visible.
  setAccCount(
    "rp-roster-total",
    (state.signatories || []).length,
    "signatory",
    "signatories",
    rosterAsOfNote()
  );

  ul.replaceChildren(
    ...rows.map((s) => {
      const li = el("li", `rp-sig-row cat-${s.category}`);
      li.append(el("span", "rp-sig-name", s.name));
      li.append(
        el("span", `rp-sig-cat cat-${s.category}`, SIGNATORY_CATEGORY_LABELS[s.category] || s.category)
      );
      li.append(
        el("span", "rp-sig-track", SIGNATORY_TRACK_LABELS[s.signed_track] || s.signed_track)
      );
      if (s.website_domain) {
        const a = document.createElement("a");
        a.className = "rp-sig-domain";
        a.href = `https://${s.website_domain}`;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = s.website_domain;
        li.append(a);
      }
      if (s.matched_company_slug) {
        const tag = el("span", "rp-sig-tracked", "Tracked here");
        li.append(tag);
      }

      // The row IS the lens (spec 7.4): no per-signatory pages for 300 orgs,
      // but a row we can say something concrete about expands to say it.
      const lens = signatoryLensSummary(s);
      if (lens) {
        li.classList.add("has-lens");
        const btn = el("button", "rp-sig-expand");
        btn.type = "button";
        btn.setAttribute("aria-expanded", "false");
        btn.textContent = lens;
        const panel = el("div", "rp-sig-lens");
        panel.hidden = true;
        btn.addEventListener("click", async () => {
          const open = btn.getAttribute("aria-expanded") === "true";
          btn.setAttribute("aria-expanded", String(!open));
          panel.hidden = open;
          if (!open && panel.dataset.filled !== "1") {
            panel.dataset.filled = "1";
            await renderSignatoryLens(s, panel);
          }
        });
        li.append(btn, panel);
      }
      return li;
    })
  );
}

// What we can show for a roster row, or null when the honest answer is
// "nothing beyond what the roster itself publishes".
//
// Counts come from data already loaded on this view (projects) plus tariffs,
// which may not be loaded yet — so the label reports only what it can count
// without a fetch, and the panel fills in the rest on expand.
function signatoryLensSummary(s) {
  const parts = [];
  if (s.matched_company_slug) {
    const n = (state.projects || []).filter(
      (p) => p.company_slug === s.matched_company_slug
    ).length;
    if (n) parts.push(`${n} tracked site${n === 1 ? "" : "s"}`);
  }
  const served = (state.projects || []).filter(
    (p) => p.serving_utility_signatory_id === s.id
  ).length;
  if (served) parts.push(`serves ${served} tracked site${served === 1 ? "" : "s"}`);
  if ((s.utility_aliases || []).length) parts.push("tariffs on file");
  if (!parts.length) return null;
  return `${parts.join(" · ")} ▾`;
}

async function renderSignatoryLens(s, panel) {
  panel.replaceChildren(el("p", "rp-sig-lens-loading", "Loading…"));
  // Tariffs live behind their own tab; a reader can reach this row without
  // having opened it.
  if (!state.tariffsLoaded) {
    await loadTariffsData().catch((err) =>
      console.error("Tariff load for signatory lens failed:", err)
    );
  }

  const sections = [];

  if (s.matched_company_slug) {
    const own = (state.projects || []).filter(
      (p) => p.company_slug === s.matched_company_slug
    );
    if (own.length) {
      sections.push({ title: "Sites it operates", items: own });
    }
  }

  const served = (state.projects || []).filter(
    (p) => p.serving_utility_signatory_id === s.id
  );
  if (served.length) sections.push({ title: "Sites it serves", items: served });

  const aliases = new Set(s.utility_aliases || []);
  const tariffs = (state.tariffs || []).filter((t) => aliases.has(t.utility));

  const frag = document.createDocumentFragment();

  for (const sec of sections) {
    frag.append(el("h5", "rp-sig-lens-h", sec.title));
    const ul = el("ul", "rp-sig-lens-list");
    for (const p of sec.items) {
      const li = el("li");
      const btn = el("button", "rp-sig-lens-link");
      btn.type = "button";
      btn.textContent = `${p.name} — ${p.city}, ${p.state}`;
      btn.addEventListener("click", () => {
        activateView("explorer");
        selectProject(p.id);
      });
      li.append(btn);
      ul.append(li);
    }
    frag.append(ul);
  }

  if (tariffs.length) {
    frag.append(el("h5", "rp-sig-lens-h", "Large-load tariffs"));
    const ul = el("ul", "rp-sig-lens-list");
    for (const t of tariffs) {
      const li = el("li");
      const btn = el("button", "rp-sig-lens-link");
      btn.type = "button";
      btn.textContent = `${t.tariff_name} (${t.state}) — ${
        TARIFF_STATUS_LABELS[t.status] || t.status
      }`;
      btn.addEventListener("click", () => {
        activateView("tariffs");
        requestAnimationFrame(() => showTariffDetail(t));
      });
      li.append(btn);
      ul.append(li);
    }
    frag.append(ul);
    if (s.notes) frag.append(el("p", "rp-sig-lens-note", s.notes));
  }

  if (!frag.childNodes.length) {
    frag.append(
      el(
        "p",
        "rp-sig-lens-note",
        "Nothing tracked for this signatory beyond the roster entry itself."
      )
    );
  }
  panel.replaceChildren(frag);
}

function renderRosterFilters() {
  const wrap = document.getElementById("rp-roster-filters");
  if (!wrap || wrap.dataset.built === "1") return;
  wrap.dataset.built = "1";

  const counts = signatoryCounts();
  const options = [
    { key: "", label: "All", n: counts.total },
    ...SIGNATORY_CATEGORIES.map((c) => ({
      key: c,
      label: SIGNATORY_CATEGORY_SHORT[c] || c,
      n: counts[c] || 0,
    })),
  ];

  wrap.replaceChildren(
    ...options.map((o) => {
      const btn = el("button", "rp-roster-chip");
      btn.type = "button";
      btn.dataset.category = o.key;
      btn.setAttribute("aria-pressed", String(_rosterFilter.category === o.key));
      btn.append(el("span", null, o.label), el("span", "rp-roster-chip-n", String(o.n)));
      btn.addEventListener("click", () => {
        _rosterFilter.category = o.key;
        for (const other of wrap.querySelectorAll(".rp-roster-chip")) {
          other.setAttribute("aria-pressed", String(other.dataset.category === o.key));
        }
        renderSignatoryRoster();
      });
      return btn;
    })
  );

  const input = document.getElementById("rp-roster-q");
  if (input && input.dataset.wired !== "1") {
    input.dataset.wired = "1";
    input.addEventListener("input", () => {
      _rosterFilter.q = input.value;
      renderSignatoryRoster();
    });
  }
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

// True when the project predates the pledge. Dated announcements compare
// directly against RATEPAYER_PLEDGE_DATE; year-only announcements are
// pre-pledge only when the year is earlier than the pledge year — a bare
// "2026" can't be placed either side of March 4, so it stays in the
// pledge-era bucket (awaiting assessment) rather than being mislabeled
// pre-pledge. Bucketing is company-agnostic (the White House date), even
// though QTS signed via the DOE track on 2026-04-24 — no dated QTS site
// currently lands in the Mar 4 – Apr 24 window; revisit if one does.
const RATEPAYER_PLEDGE_YEAR = Number(RATEPAYER_PLEDGE_DATE.slice(0, 4));

// The date THIS project's operator joined the pledge — not the pledge's own
// date. Since the July 2026 expansion the two differ: CoreWeave, Crusoe and
// Prologis signed on 2026-07-23, so a CoreWeave site announced in May 2026 is
// pre-*their*-pledge even though it postdates the White House event.
//
// Falls back to the White House date while the roster payload is still in
// flight, which keeps the original seven bucketed correctly on a cold
// deep-link instead of briefly showing every site as non-signatory.
function projectPledgeDate(p) {
  const fromRoster = signatorySignedDate(p.company_slug);
  if (fromRoster) return fromRoster;
  const co = state.companiesBySlug.get(p.company_slug);
  return co && co.ratepayer_pledge_signatory ? RATEPAYER_PLEDGE_DATE : null;
}

// True when the project predates its operator's signature. Year-only
// announcements are pre-pledge only when the year is earlier than the signing
// year — a bare "2026" can't be placed either side of a specific day, so it
// stays in the pledge-era (awaiting assessment) bucket rather than being
// mislabeled.
function isPrePledgeProject(p) {
  const signed = projectPledgeDate(p);
  if (!signed) return false;
  if (p.announced_date) return p.announced_date < signed;
  return p.announced_year < Number(signed.slice(0, 4));
}

function rosterSort(a, b) {
  if (a.company_slug !== b.company_slug)
    return a.company_slug.localeCompare(b.company_slug);
  return a.name.localeCompare(b.name);
}

// Signatory sites announced before the pledge with no post-pledge commitment
// captured. Shown in a separate section beneath the assessed cohort.
function ratepayerPrePledgeProjects() {
  const signatorySlugs = new Set(ratepayerSignatories().map((c) => c.slug));
  return state.projects
    .filter(
      (p) =>
        signatorySlugs.has(p.company_slug) &&
        !p.ratepayer &&
        isPrePledgeProject(p)
    )
    .sort(rosterSort);
}

// Signatory sites announced in the pledge era (on/after the pledge, or a
// year-only 2026 announcement) with no assessment captured yet. Shown in
// their own section so they aren't mislabeled "pre-pledge" — absence of an
// assessment means the curation work is pending, not implied compliance.
function ratepayerUnassessedPledgeEraProjects() {
  const signatorySlugs = new Set(ratepayerSignatories().map((c) => c.slug));
  return state.projects
    .filter(
      (p) =>
        signatorySlugs.has(p.company_slug) &&
        !p.ratepayer &&
        !isPrePledgeProject(p)
    )
    .sort(rosterSort);
}

// Sites from companies that never signed the pledge at all (CoreWeave, Crusoe,
// Anthropic, Wonder Valley, Prologis, ...). Not part of the assessed cohort —
// there's no pledge to have complied with — shown only when the reader
// explicitly opts in via the "Show non-signatory companies" toggle, so the
// default view stays scoped to what the pledge actually covers.
function ratepayerNonSignatoryProjects() {
  const signatorySlugs = new Set(ratepayerSignatories().map((c) => c.slug));
  return state.projects
    .filter((p) => !signatorySlugs.has(p.company_slug))
    .sort(rosterSort);
}

// Format an announced date for display. Uses announced_date (ISO) when
// present, falling back to announced_year as a plain string.
function formatAnnouncedDate(p) {
  if (p.announced_date) return formatLongDate(p.announced_date);
  return String(p.announced_year);
}

// Claim language that reads as a ratepayer / pay-our-own-way commitment.
// Used as the company-wide fallback on a scorecard card when a site has no
// site-specific claim of its own, so a card can still show what the operator
// has committed to in general rather than rendering empty.
const RATEPAYER_CLAIM_KEYWORDS = [
  "ratepayer",
  "pay our own way",
  "pay our way",
  "100% of the power",
  "100% of the cost of power",
  "100% of the energy",
  "100% of the grid",
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
    "Signing Track",
    "Company Signed Date",
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

    // Which pledge round the operator signed in. Since the July expansion the
    // cohort spans three tracks, and a scorecard row is not interpretable
    // without knowing which pledge the site is being measured against.
    const sig = state.signatoryByCompany && state.signatoryByCompany.get(p.company_slug);

    const row = [
      co ? co.name : p.company_slug,
      sig ? SIGNATORY_TRACK_LABELS[sig.signed_track] || sig.signed_track : "Not a signatory",
      sig && sig.signed_date ? sig.signed_date : "",
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

  // Unassessed signatory sites: pledge-era (assessment pending) and
  // pre-pledge (out of cohort), each labeled honestly.
  const unassessedBuckets = [
    [
      ratepayerUnassessedPledgeEraProjects(),
      "not-yet-assessed",
      "Announced during the pledge era; per-site assessment pending.",
    ],
    [
      ratepayerPrePledgeProjects(),
      "pre-pledge",
      "Announced before the pledge; no site-specific commitment captured.",
    ],
  ];
  for (const [bucket, assessment, summary] of unassessedBuckets) {
    for (const p of bucket) {
      const co = state.companiesBySlug.get(p.company_slug);
      const announcedDate = p.announced_date || String(p.announced_year);
      // Must stay column-for-column identical to the assessed row above —
      // adding a header without touching this block shifts every later value.
      const sig = state.signatoryByCompany && state.signatoryByCompany.get(p.company_slug);
      const row = [
        co ? co.name : p.company_slug,
        sig ? SIGNATORY_TRACK_LABELS[sig.signed_track] || sig.signed_track : "Not a signatory",
        sig && sig.signed_date ? sig.signed_date : "",
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
        assessment, // Pledge Assessment
        summary,
        "", "", "", // Evidence Title, URL, Assessment Date
        ...PRINCIPLE_KEYS.map(() => "N/A"),
      ];
      rows.push(row.map(escapeCSV).join(","));
    }
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

// Scorecard filter state. Deliberately module-level and NOT persisted: a
// returning reader should see the whole cohort, not whatever slice they left
// behind — same reasoning as _lastDetailTab not going to localStorage.
const _rpFilter = { q: "", status: "", concernsOnly: false };

// Sites matching the current filter, concern-first.
//
// Ordering is the point of the sort: a site where someone has documented costs
// reaching ratepayers is the most consequential thing on the page, and it was
// previously buried alphabetically among 39 cards.
function filteredAssessedProjects() {
  const q = _rpFilter.q.trim().toLowerCase();
  const rows = ratepayerAssessedProjects().filter((p) => {
    if (_rpFilter.status && p.ratepayer.status !== _rpFilter.status) return false;
    if (_rpFilter.concernsOnly && !rpConflictingReports(p).length) return false;
    if (!q) return true;
    const co = state.companiesBySlug.get(p.company_slug);
    // Match the spelled-out state too — records store "GA", but people type
    // "Georgia", and a search that silently returns nothing reads as "no sites
    // here" rather than "wrong query".
    const stateName = STATE_NAMES[String(p.state || "").toUpperCase()] || "";
    return (
      p.name.toLowerCase().includes(q) ||
      (co ? co.name : p.company_slug).toLowerCase().includes(q) ||
      String(p.state || "").toLowerCase().includes(q) ||
      stateName.toLowerCase().includes(q) ||
      String(p.city || "").toLowerCase().includes(q)
    );
  });

  return rows.sort((a, b) => {
    const concern = (p) => (rpConflictingReports(p).length ? 0 : 1);
    const d = concern(a) - concern(b);
    if (d !== 0) return d;
    return 0; // ratepayerAssessedProjects already sorts within the group
  });
}

function renderRatepayerFilterBar() {
  const wrap = document.getElementById("rp-status-filter");
  if (!wrap) return;

  if (wrap.dataset.built !== "1") {
    wrap.dataset.built = "1";
    const all = ratepayerAssessedProjects();
    const options = [
      { key: "", label: "All", n: all.length },
      ...RATEPAYER_STATUSES.map((s) => ({
        key: s,
        label: RATEPAYER_LABELS[s] || s,
        n: all.filter((p) => p.ratepayer.status === s).length,
      })).filter((o) => o.n > 0), // honest-absence: no zero chips
    ];
    wrap.replaceChildren(
      ...options.map((o) => {
        const btn = el("button", `rp-filter-chip is-${o.key || "all"}`);
        btn.type = "button";
        btn.dataset.status = o.key;
        btn.setAttribute("aria-pressed", String(_rpFilter.status === o.key));
        btn.append(el("span", null, o.label), el("span", "rp-filter-chip-n", String(o.n)));
        btn.addEventListener("click", () => {
          _rpFilter.status = o.key;
          for (const other of wrap.querySelectorAll(".rp-filter-chip")) {
            other.setAttribute("aria-pressed", String(other.dataset.status === o.key));
          }
          renderRatepayerScorecard();
        });
        return btn;
      })
    );
  }

  const input = document.getElementById("rp-q");
  if (input && input.dataset.wired !== "1") {
    input.dataset.wired = "1";
    input.addEventListener("input", () => {
      _rpFilter.q = input.value;
      renderRatepayerScorecard();
    });
  }
  const only = document.getElementById("rp-only-concerns");
  if (only && only.dataset.wired !== "1") {
    only.dataset.wired = "1";
    only.addEventListener("change", () => {
      _rpFilter.concernsOnly = only.checked;
      renderRatepayerScorecard();
    });
  }
}

function renderRatepayerScorecard() {
  renderRatepayerFilterBar();
  setSubtabCount("rp-scorecard-count", ratepayerAssessedProjects().length);

  const ul = document.getElementById("rp-scorecard");
  if (ul) {
    ul.innerHTML = "";
    const total = ratepayerAssessedProjects().length;
    const assessed = filteredAssessedProjects();
    const count = document.getElementById("rp-filter-count");
    if (count) {
      count.textContent =
        assessed.length === total
          ? `${total} assessed site${total === 1 ? "" : "s"}`
          : `Showing ${assessed.length} of ${total} assessed sites`;
    }
    if (total === 0) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "No assessed data centers yet.";
      ul.appendChild(li);
    } else if (assessed.length === 0) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "No assessed sites match these filters.";
      ul.appendChild(li);
    } else {
      for (const p of assessed) {
        ul.appendChild(renderRatepayerCard(p));
      }
    }
  }

  // Wire export buttons (includes both assessed + pre-pledge rows).
  const exportBtn = document.getElementById("rp-export-csv");
  if (exportBtn) exportBtn.onclick = downloadRatepayerCSV;
  wireBtn("rp-export-pdf", exportRatepayerToPDF);

  // Pledge-era sites awaiting assessment (post-pledge or year-only 2026,
  // no assessment captured yet).
  const unassessedUl = document.getElementById("rp-unassessed");
  if (unassessedUl) {
    unassessedUl.innerHTML = "";
    const unassessed = ratepayerUnassessedPledgeEraProjects();
    setSubtabCount("rp-unassessed-count", unassessed.length);
    if (unassessed.length === 0) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "No pledge-era sites awaiting assessment.";
      unassessedUl.appendChild(li);
    } else {
      for (const p of unassessed) {
        unassessedUl.appendChild(
          renderPrePledgeCard(p, "Pledge era — assessment pending")
        );
      }
    }
  }

  // Pre-pledge section.
  const prePledgeUl = document.getElementById("rp-pre-pledge");
  if (prePledgeUl) {
    prePledgeUl.innerHTML = "";
    const prePledge = ratepayerPrePledgeProjects();
    setSubtabCount("rp-pre-pledge-count", prePledge.length);
    if (prePledge.length === 0) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "No pre-pledge sites found.";
      prePledgeUl.appendChild(li);
    } else {
      for (const p of prePledge) {
        prePledgeUl.appendChild(renderPrePledgeCard(p, prePledgeNote(p)));
      }
    }
  }

  // Non-signatory section: rendered once regardless of toggle state (cheap —
  // same card renderer as the other sections), visibility is toggle-only.
  const nonSigUl = document.getElementById("rp-non-signatory");
  if (nonSigUl) {
    nonSigUl.replaceChildren();
    const nonSig = ratepayerNonSignatoryProjects();
    setSubtabCount("rp-non-signatory-count", nonSig.length);
    if (nonSig.length === 0) {
      const li = document.createElement("li");
      li.className = "muted";
      li.textContent = "No non-signatory sites tracked.";
      nonSigUl.appendChild(li);
    } else {
      for (const p of nonSig) {
        nonSigUl.appendChild(renderPrePledgeCard(p, "Not a pledge signatory"));
      }
    }
  }
  // Every cohort's total, so the collapsed accordion says how many sites are
  // tracked in all — the sub-tab pills break that down once it's open.
  setAccCount(
    "rp-sites-count",
    ratepayerAssessedProjects().length +
      ratepayerUnassessedPledgeEraProjects().length +
      ratepayerPrePledgeProjects().length +
      ratepayerNonSignatoryProjects().length,
    "site"
  );
  wireSubtabs();
  setActiveSubtab("rp-sites", _activeSubtab["rp-sites"] || "assessed");
}

// True when the project's company is a pledge signatory at all (regardless of
// whether this specific site has been assessed) — used to keep non-signatory
// cards (the "Show non-signatory companies" toggle) from citing or labeling
// content as pledge-related when the company never signed it.
function isRatepayerSignatoryCompany(companySlug) {
  const signatorySlugs = new Set(ratepayerSignatories().map((c) => c.slug));
  return signatorySlugs.has(companySlug);
}

// Build an always-visible "Sources" footer for a ratepayer site. Guarantees
// EVERY card — including pledge_only and unassessed sites with no evidence
// claim — links to a traceable source, fixing the "no links for evidence"
// gap. Order: site-specific evidence claim (affirmed/contested) → company
// project page → record source → the pledge proclamation (signatory
// companies only — a non-signatory's card must not cite the pledge as one of
// its sources). Deduped by URL and robust to claims not being loaded yet (the
// project's own source_url is always present and required by the schema).
function rpCardSourcesHtml(p) {
  const rp = p.ratepayer;
  const links = [];
  const seen = new Set();
  const add = (url, label) => {
    if (!url) return;
    const u = String(url);
    if (seen.has(u)) return;
    seen.add(u);
    links.push([u, label]);
  };
  if (rp && rp.evidence_claim_id) {
    const claim = state.claims.find((c) => c.id === rp.evidence_claim_id);
    if (claim) add(claim.source_url, claim.source_title || "Site commitment source");
  }
  add(p.project_page_url, "Company project page");
  add(p.source_url, p.source_title || "Record source");
  if (isRatepayerSignatoryCompany(p.company_slug)) {
    add(RATEPAYER_PLEDGE_URL, "The pledge");
  }
  const anchors = links
    .map(
      ([u, label]) =>
        `<a href="${escapeAttr(u)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)} ↗</a>`
    )
    .join('<span class="rp-src-sep"> · </span>');
  return `<div class="rp-card-sources"><span class="rp-sources-label">Sources:</span> ${anchors}</div>`;
}

// Per-claim audit trail: every claim tied to this site, each linked to its own
// source. Falls back to company-level ratepayer pledge claims (up to 3) when no
// project-specific claims exist, labeled distinctly so readers know the scope.
// Depends on state.claimsByProject (populated after claims.json loads).
function rpCardClaimsHtml(p) {
  const projectClaims = (state.claimsByProject && state.claimsByProject.get(p.id)) || [];
  const evidenceId = p.ratepayer && p.ratepayer.evidence_claim_id;

  // Fall back to company-wide ratepayer pledge claims when no site-specific ones.
  let claims = projectClaims;
  let isCompanyFallback = false;
  if (!claims.length && state.claims) {
    claims = state.claims
      .filter(
        (c) =>
          c.company_slug === p.company_slug &&
          !c.project_id &&
          RATEPAYER_CLAIM_KEYWORDS.some((k) => c.statement.toLowerCase().includes(k))
      )
      .slice(0, 3);
    isCompanyFallback = claims.length > 0;
  }

  if (!claims.length) return "";

  const items = claims
    .map((c) => {
      const label = THEME_LABELS[c.theme] || c.theme;
      const date = c.published_at || c.captured_at || "";
      const isEvidence = !isCompanyFallback && evidenceId && c.id === evidenceId;
      const flag = isEvidence
        ? `<span class="rp-claim-flag" title="Cited as this site's ratepayer evidence">★ evidence</span>`
        : "";
      return `<li class="rp-claim-src">
        <span class="rp-claim-theme" style="--theme-color: var(--theme-${escapeAttr(c.theme)});">${escapeHtml(label)}</span>
        <a href="${escapeAttr(String(c.source_url))}" target="_blank" rel="noopener noreferrer" class="rp-claim-link">${escapeHtml(c.source_title || "Source")} ↗</a>
        ${date ? `<span class="rp-claim-date">${escapeHtml(date)}</span>` : ""}
        ${flag}
      </li>`;
    })
    .join("");

  const sectionLabel = isCompanyFallback
    ? isRatepayerSignatoryCompany(p.company_slug)
      ? `Company-wide pledge sources (${claims.length}) — no site-specific claims on file:`
      : `Company's own related claims (${claims.length}) — not pledge-affiliated, no site-specific claims on file:`
    : `Claim sources (${claims.length}) — every claim, individually cited:`;

  return `<div class="rp-card-claims">
    <span class="rp-claims-label">${sectionLabel}</span>
    <ul class="rp-claims-list">${items}</ul>
  </div>`;
}

// "Did the company claim this exact site, or only sign the national pledge?"
// Basis is derived from whether a site-specific evidence claim backs the record:
//   individual  → an explicit, site-specific first-party commitment exists
//   company-wide → covered only by the company's national pledge signature
function rpClaimBasis(p) {
  const rp = p.ratepayer;
  if (rp && rp.evidence_claim_id) return "individual";
  return "company-wide";
}

const RP_BASIS_LABELS = {
  individual: "Claimed individually",
  "company-wide": "Company-wide pledge only",
};

function rpBasisBadgeHtml(p) {
  const basis = rpClaimBasis(p);
  const title =
    basis === "individual"
      ? "The company published a ratepayer commitment for this exact site."
      : "This site is covered only by the company's national pledge signature — no site-specific commitment captured.";
  return `<span class="rp-basis rp-basis--${basis}" title="${escapeAttr(title)}">${RP_BASIS_LABELS[basis]}</span>`;
}

// Independent reports that conflict with the claim of meeting the pledge:
// negative-stance community responses for this site whose summary touches
// ratepayer / cost-shift / rate / bill / utility. Surfaced on every card
// (affirmed, pledge_only, contested) so a reader sees the counter-evidence.
const RP_CONFLICT_KEYWORDS = [
  "ratepayer", "rate payer", "cost-shift", "cost shift", "cost shifting",
  "shift cost", "shifting cost", "cost onto", "onto residential",
  "rate increase", "rate hike", "electricity bill", "utility bill", "energy bill",
  "subsidiz", "subsidy", "grid cost", "grid-cost", "monthly bill", "residential rate",
  "residential customer", "residential bill", "rate class", "pass the cost",
  "passing the cost", "raise rates", "higher rates",
];

function rpConflictingReports(p) {
  const responses = (state.responsesByProject && state.responsesByProject.get(p.id)) || [];
  return responses.filter((r) => {
    if (r.stance !== "negative") return false;
    // Curated ratepayer-conflict responses carry "ratepayer" in their id — the
    // reliable signal (the Synapse contested-site responses and the added
    // regulator/report conflicts both use it), independent of summary wording.
    if ((r.id || "").toLowerCase().includes("ratepayer")) return true;
    const s = (r.summary || "").toLowerCase();
    return RP_CONFLICT_KEYWORDS.some((k) => s.includes(k));
  });
}

function rpConflictsHtml(p) {
  const reports = rpConflictingReports(p);
  if (!reports.length) return "";
  const items = reports
    .map((r) => {
      const date = r.date ? `<span class="rp-conflict-date">${escapeHtml(r.date)}</span>` : "";
      const who = r.constituency
        ? `<span class="rp-conflict-who">${escapeHtml(CONSTITUENCY_LABELS[r.constituency] || r.constituency)}</span>`
        : "";
      const single = r.single_source
        ? `<span class="rp-conflict-single" title="Single-source claim">single source</span>`
        : "";
      return `<li class="rp-conflict-item">
        <p class="rp-conflict-summary">${escapeHtml(r.summary)}</p>
        <div class="rp-conflict-meta">${who}${date}${single}
          <a href="${escapeAttr(String(r.source_url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(r.source_title || "Source")} ↗</a>
        </div>
      </li>`;
    })
    .join("");
  return `<div class="rp-conflicts">
    <div class="rp-conflicts-head">⚠ Ratepayer cost-shift concerns (${reports.length}) — independent findings affecting this site or its utility system</div>
    <ul class="rp-conflicts-list">${items}</ul>
  </div>`;
}

function rpConflictFlagHtml(p) {
  // Small always-visible header flag when independent reports raise a ratepayer
  // cost-shift concern for this site or the utility system it sits on.
  return rpConflictingReports(p).length ? `<span class="rp-conflict-flag" title="Independent reports raise a ratepayer cost-shift concern for this site or its utility">⚠ Ratepayer concern</span>` : "";
}

function renderRatepayerCard(p) {
  const co = state.companiesBySlug.get(p.company_slug);
  const rp = p.ratepayer;
  const li = document.createElement("li");
  li.className = "rp-card";
  li.dataset.status = rp.status;
  li.style.setProperty("--co-color", `var(--co-${p.company_slug})`);
  li.style.setProperty("--rp-color", `var(--ratepayer-${rp.status})`);

  // Resolve evidence claim once — used for "met" principle source links.
  const evidenceClaim = rp.evidence_claim_id
    ? state.claims.find((c) => c.id === rp.evidence_claim_id)
    : null;

  const loc = `${escapeHtml(p.city)}, ${escapeHtml(p.state)}`;

  // X/5 met pill — count principles with status === 'met'
  const metCount = PLEDGE_PRINCIPLES.filter(
    (key) => rp.principles?.[key]?.status === "met"
  ).length;
  const metClass =
    metCount === 5 ? "met" : metCount >= 3 ? "partial" : "low";

  // Per-principle rows. Each row carries an inline source link so readers can
  // immediately verify how each element is assessed — no separate evidence
  // blockquote or per-claim audit trail needed.
  let principlesHtml = "";
  if (rp.principles && Object.keys(rp.principles).length > 0) {
    const rows = PLEDGE_PRINCIPLES.map((key) => {
      const assessment = rp.principles[key] || {};
      const status = assessment.status || "unknown";
      const note = assessment.note || "";
      const label = PLEDGE_PRINCIPLE_LABELS[key];
      const statusLabel = PLEDGE_PRINCIPLE_STATUS_LABELS[status] || status;

      // Derive per-principle source link:
      //   met      → evidence claim (the site-specific backing claim)
      //   partial  → the national pledge proclamation
      //   not_met  → the project's source (contested-evidence article)
      //   unknown  → no link
      let srcUrl = null;
      let srcTitle = null;
      if (status === "met" && evidenceClaim) {
        srcUrl = String(evidenceClaim.source_url);
        srcTitle = evidenceClaim.source_title;
      } else if (status === "partial") {
        srcUrl = RATEPAYER_PLEDGE_URL;
        srcTitle = "Ratepayer Protection Pledge";
      } else if (status === "not_met") {
        srcUrl = String(p.source_url);
        srcTitle = p.source_title || "Project source";
      }
      const srcHtml = srcUrl
        ? ` <a href="${escapeAttr(srcUrl)}" target="_blank" rel="noopener noreferrer" class="pp-row-src" title="${escapeAttr(srcTitle || "")}">↗</a>`
        : "";

      const noteHtml = note
        ? `<span class="pp-row-note">${escapeHtml(note)}</span>`
        : "";
      return `<li class="pp-row pp-row--${escapeAttr(status)}">
        <div class="pp-row-body">
          <span class="pp-row-label">${escapeHtml(label)}</span>
          ${noteHtml}
        </div>
        <span class="pp-row-status">${escapeHtml(statusLabel)}${srcHtml}</span>
      </li>`;
    }).join("");
    principlesHtml = `<ul class="rp-principles" aria-label="Pledge principles fulfillment">${rows}</ul>`;
  }

  // Date metadata row: announced date + first pledge reference.
  const announcedStr = formatAnnouncedDate(p);
  const pledgeRefStr = rp.assessed_at ? formatLongDate(rp.assessed_at) : "";
  const datesHtml = `<span class="rp-card-dates">Announced: ${escapeHtml(announcedStr)}${pledgeRefStr ? ` · First pledge ref: ${escapeHtml(pledgeRefStr)}` : ""}</span>`;

  // Collapsible card — header is always visible; body expands on click.
  // Sources footer is the single consolidated reference list; the separate
  // evidence blockquote and per-claim audit trail have been removed.
  li.innerHTML = `
    <details class="rp-card-details">
      <summary class="rp-card-head">
        <div class="rp-card-title">
          <span class="rp-card-company">${escapeHtml(co ? co.name : p.company_slug)}</span>
          <span class="rp-card-name">${escapeHtml(p.name)}</span>
          <span class="rp-card-loc">${loc} · ${escapeHtml(STATUS_LABELS[p.status] || p.status)}</span>
          <span class="rp-card-badges">${rpBasisBadgeHtml(p)}${rpConflictFlagHtml(p)}</span>
          ${datesHtml}
        </div>
        <span class="rp-met-pill rp-met-pill--${escapeAttr(metClass)}">${metCount}/5 met</span>
      </summary>
      <div class="rp-card-body">
        <p class="rp-card-summary">${escapeHtml(rp.summary)}</p>
        ${principlesHtml}
        ${rpConflictsHtml(p)}
        ${rpCardSourcesHtml(p)}
      </div>
    </details>
  `;
  return li;
}

// Compact card for unassessed signatory sites (no ratepayer assessment).
// Used by both the pre-pledge section (default note) and the pledge-era
// awaiting-assessment section (caller passes a note).
// Why a given site sits in the pre-pledge bucket. Since the July expansion
// there are two distinct reasons, and collapsing them would misread the July
// cohort: a Meta site from 2024 predates a pledge that already existed by the
// time we started tracking, whereas a CoreWeave site from May 2026 predates
// CoreWeave's own signature by two months. The second is not a gap in the
// company's follow-through; it is simply outside the window.
function prePledgeNote(p) {
  const signed = projectPledgeDate(p);
  if (signed && signed !== RATEPAYER_PLEDGE_DATE) {
    return `Announced before this operator signed (${formatLongDate(signed)})`;
  }
  return "National pledge — no site assessment";
}

function renderPrePledgeCard(p, note = "National pledge — no site assessment") {
  const co = state.companiesBySlug.get(p.company_slug);
  const li = document.createElement("li");
  li.className = "rp-pre-card";
  li.style.setProperty("--co-color", `var(--co-${p.company_slug})`);
  const announcedStr = formatAnnouncedDate(p);
  li.innerHTML = `
    <span class="rp-pre-company">${escapeHtml(co ? co.name : p.company_slug)}</span>
    <span class="rp-pre-name">${escapeHtml(p.name)}</span>
    <span class="rp-pre-loc">${escapeHtml(p.city)}, ${escapeHtml(p.state)} · ${escapeHtml(STATUS_LABELS[p.status] || p.status)}</span>
    <span class="rp-pre-dates">Announced: ${escapeHtml(announcedStr)} · ${escapeHtml(note)}</span>
    ${rpCardClaimsHtml(p)}
    ${rpCardSourcesHtml(p)}
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
  // Build rollups once and pass to each renderer to avoid triple iteration.
  const coRows = buildCompanyRollups();
  const stRows = buildStateRollups();
  renderAggregateStats(coRows, stRows);
  renderCompanyRollup(coRows);
  renderSignatoryCategoryRollup();
  renderStateRollup(stRows);
  wireAggSort();
  wireSubtabs();
  setActiveSubtab("agg", _activeSubtab.agg || "company");
  wireBtn("agg-csv-btn", downloadAggregateCSV);
  wireBtn("agg-pdf-btn", exportAggregateToPDF);
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
      // Re-render the whole view so _aggSort state is picked up correctly.
      // renderAggregateView() is cheap (O(n) with n<=100) and keeps the
      // sort indicators, stats, and both tables in sync.
      renderAggregateView();
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

function renderAggregateStats(preCoRows, preStRows) {
  const ul = document.getElementById("agg-stats");
  if (!ul) return;
  ul.innerHTML = "";

  const coRows = preCoRows || buildCompanyRollups();
  const stRows = preStRows || buildStateRollups();
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

// Roll the tracked sites up by the pledge cohort their operator belongs to.
//
// Only covers the 13 deeply-tracked companies — the other 268 roster rows have
// no sites here, and inventing a row for them would imply coverage we don't
// have. Companies with no roster match land in a "Did not sign" row, which is
// the comparison the table exists to make.
function buildSignatoryCategoryRollups() {
  const rows = new Map();
  const touch = (key, label) => {
    if (!rows.has(key)) {
      rows.set(key, {
        key,
        label,
        companies: new Set(),
        projects: 0,
        power_mw: 0,
        capex: 0,
        assessed: 0,
        contested: 0,
      });
    }
    return rows.get(key);
  };

  for (const p of state.projects || []) {
    const sig = state.signatoryByCompany && state.signatoryByCompany.get(p.company_slug);
    const key = sig ? sig.category : "none";
    const label = sig
      ? SIGNATORY_CATEGORY_LABELS[sig.category] || sig.category
      : "Did not sign";
    const r = touch(key, label);
    r.companies.add(p.company_slug);
    r.projects += 1;
    if (p.power_mw) r.power_mw += p.power_mw;
    if (p.claimed_investment_usd) r.capex += p.claimed_investment_usd;
    if (p.ratepayer) {
      r.assessed += 1;
      if (p.ratepayer.status === "contested") r.contested += 1;
    }
  }

  // Signatory categories in vocabulary order, non-signatories last.
  const order = [...SIGNATORY_CATEGORIES, "none"];
  return [...rows.values()].sort(
    (a, b) => order.indexOf(a.key) - order.indexOf(b.key)
  );
}

function renderSignatoryCategoryRollup() {
  const tbody = document.getElementById("agg-signatory-tbody");
  if (!tbody) return;
  const rows = buildSignatoryCategoryRollups();

  tbody.replaceChildren(
    ...rows.map((r) => {
      const tr = document.createElement("tr");
      const cells = [
        r.label,
        String(r.companies.size),
        String(r.projects),
        r.power_mw ? formatSummaryGW(r.power_mw) : "—",
        r.capex ? formatSummaryUsd(r.capex) : "—",
        String(r.assessed),
        r.contested ? String(r.contested) : "—",
      ];
      cells.forEach((v, i) => {
        const td = document.createElement("td");
        if (i > 0) td.className = "num";
        td.textContent = v;
        tr.append(td);
      });
      return tr;
    })
  );

  const sub = document.getElementById("agg-signatory-sub");
  if (sub) {
    const tracked = new Set((state.projects || []).map((p) => p.company_slug)).size;
    sub.textContent =
      `Covers the ${tracked} companies tracked site by site — not the full ` +
      `roster. "Assessed" counts sites carrying a per-site pledge assessment; ` +
      `a site with none is counted in neither Assessed nor Contested.`;
  }
}

function renderCompanyRollup(preRows) {
  const tbody = document.getElementById("agg-company-tbody");
  const tfoot = document.getElementById("agg-company-tfoot");
  if (!tbody || !tfoot) return;

  const rows = sortAggRows(preRows || buildCompanyRollups(), "company");
  const tot = aggTotals(rows);
  setSubtabCount("agg-company-count", rows.length);

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

function renderStateRollup(preRows) {
  const tbody = document.getElementById("agg-state-tbody");
  const tfoot = document.getElementById("agg-state-tfoot");
  if (!tbody || !tfoot) return;

  const rows = sortAggRows(preRows || buildStateRollups(), "state");
  const tot = aggTotals(rows);
  setSubtabCount("agg-state-count", rows.length);

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
