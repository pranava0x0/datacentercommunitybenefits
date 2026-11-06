// Generated from jurisdiction-map.js by tools/build_preview.py.
window.__JURISDICTION_MAP__ = (() => {
// Boundary and point data are fetched only when Moratoriums → Map opens.
const NS = "http://www.w3.org/2000/svg";
const SITE_LABELS = { national_lab: "National lab", em_site: "EM site / office", other_asset: "DOE asset" };
const TOPIC_LABELS = { data_center: "Data centers", grid: "Grid & power", large_load: "Large loads" };
function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}
function svg(tag, attrs = {}) {
  const node = document.createElementNS(NS, tag);
  for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, String(value));
  return node;
}
function link(url, label) {
  const parsed = new URL(url);
  if (!["https:", "http:"].includes(parsed.protocol)) throw new Error("Invalid geographic source URL");
  const node = el("a", "", label);
  node.href = parsed.href;
  node.target = "_blank";
  node.rel = "noopener noreferrer";
  return node;
}
function point(lon, lat, stateCode) {
  const x = stateCode === "AK" && lon > 0 ? lon - 360 : lon;
  return [x, -Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) * 180 / Math.PI];
}
function polygonPoints(item) {
  const polygons = item.geometry.type === "Polygon" ? [item.geometry.coordinates] : item.geometry.coordinates;
  return polygons.map((polygon) => polygon.map((ring) => ring.map(([lon, lat]) => point(lon, lat, item.state_code))));
}
function extent(points) {
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}
function status(record, kind) {
  return kind === "moratorium" && record.lifted_date ? "lifted" : record.status;
}

function mount(root, data, hooks) {
  if (!Array.isArray(data.geography?.jurisdictions) || !Array.isArray(data.doe?.sites)
      || !Array.isArray(data.doe.announcements)) throw new Error("Geographic payload is incomplete");
  const moratoriums = new Map(data.moratoriums.map((item) => [item.id, item]));
  const policies = new Map(data.policies.map((item) => [item.id, item]));
  const regions = data.geography.jurisdictions.map((item) => {
    const projected = polygonPoints(item);
    return { ...item, projected, bounds: extent(projected.flat(2)),
      path: projected.map((polygon) => polygon.map((ring) => ring.map(([x, y], index) => `${index ? "L" : "M"}${x.toFixed(5)},${y.toFixed(5)}`).join("") + "Z").join("")).join("") };
  });
  const sites = data.doe.sites.map((item) => ({ ...item, projected: point(item.lon, item.lat, item.state_code) }));
  const stateRegions = new Map(regions.filter((item) => item.level === "state").map((item) => [item.state_code, item]));
  const regionsById = new Map(regions.map((item) => [item.id, item]));
  const controls = el("div", "filter-bar jurisdiction-filters");
  controls.setAttribute("aria-label", "Map filters");
  const queryLabel = el("label", "", "Search");
  const query = el("input"); query.type = "search"; query.id = "jurisdiction-map-q";
  query.placeholder = "Place, lab or project"; queryLabel.append(query); controls.append(queryLabel);
  function select(id, label, options) {
    const wrapper = el("label", "", label); const node = el("select"); node.id = id;
    for (const [value, title] of options) node.add(new Option(title, value));
    wrapper.append(node); controls.append(wrapper); return node;
  }
  const state = select("jurisdiction-map-state", "State", [["", "All states"], ...Object.entries(hooks.stateNames)]);
  const recorded = select("jurisdiction-map-status", "Status", [["enacted", "Enacted / in effect"], ["proposed", "Proposed"], ["all", "All recorded"]]);
  const level = select("jurisdiction-map-level", "Jurisdiction", [["", "All levels"], ["state", "State"], ["county", "County"], ["city", "City / town"]]);
  const siteKind = select("jurisdiction-map-site-kind", "DOE locations", [["", "All types"], ...Object.entries(SITE_LABELS)]);
  const topic = select("jurisdiction-map-topic", "Announcements", [["", "All topics"], ...Object.entries(TOPIC_LABELS)]);
  const advanced = el("details", "map-filters"); advanced.append(el("summary", "", "More filters"));
  const advancedControls = el("div", "filter-bar jurisdiction-filters");
  for (const input of [recorded, level, siteKind, topic]) advancedControls.append(input.parentElement);
  advanced.append(advancedControls);
  const layers = el("fieldset", "jurisdiction-layers"); layers.append(el("legend", "sr-only", "Map layers"));
  function checkbox(key, text) {
    const label = el("label", `map-key-${key}`); const input = el("input");
    input.type = "checkbox"; input.checked = true; input.id = `map-layer-${key}`;
    label.append(input, document.createTextNode(text)); layers.append(label); return input;
  }
  const showMoratoriums = checkbox("moratoriums", "Moratoriums");
  const showPolicies = checkbox("policies", "Policy frameworks");
  const showDOE = checkbox("doe", "DOE sites");
  const showAnnouncements = checkbox("announcements", "Announcements");
  advanced.append(layers);
  const meta = el("p", "muted"); meta.id = "jurisdiction-map-meta"; meta.setAttribute("role", "status");
  const layout = el("div", "jurisdiction-layout");
  const canvas = el("div", "jurisdiction-canvas");
  const map = svg("svg", { role: "group", "aria-label": "Moratorium jurisdictions, policy frameworks and DOE locations", tabindex: "0", preserveAspectRatio: "xMidYMid meet" });
  map.id = "jurisdiction-map-svg";
  const background = svg("g", { class: "map-state-background", "aria-hidden": "true" });
  for (const item of stateRegions.values()) background.append(svg("path", { d: item.path, "vector-effect": "non-scaling-stroke" }));
  const fills = svg("g"); const markers = svg("g"); map.append(background, fills, markers);
  const toolbar = el("div", "jurisdiction-zoom"); toolbar.setAttribute("aria-label", "Map position");
  function button(text, label, action) {
    const node = el("button", "btn-ghost", text); node.type = "button"; node.setAttribute("aria-label", label);
    node.addEventListener("click", action); toolbar.append(node); return node;
  }
  button("+", "Zoom in", () => zoom(.65)); button("−", "Zoom out", () => zoom(1.55));
  button("U.S.", "Contiguous United States", () => { state.value = ""; render(true); });
  button("AK", "Alaska", () => { state.value = "AK"; render(true); });
  button("HI", "Hawaii", () => { state.value = "HI"; render(true); });
  const tooltip = el("div", "jurisdiction-tooltip");
  tooltip.id = "jurisdiction-map-tooltip"; tooltip.setAttribute("role", "tooltip"); tooltip.hidden = true;
  canvas.append(map, toolbar, tooltip);
  const legend = el("ul", "jurisdiction-legend"); legend.setAttribute("aria-label", "Map legend");
  for (const [key, label] of [["moratorium", "Pause / ban"], ["policy", "Framework"], ["both", "Both"],
    ["proposed", "Proposed: dashed border"], ["inactive", "Lifted / failed: dotted border"],
    ["doe", "DOE site"], ["announcement", "DOE site with announcement"]]) {
    const item = el("li"); const symbol = el("span", `map-swatch map-swatch-${key}`, ["doe", "announcement"].includes(key) ? "★" : "");
    symbol.setAttribute("aria-hidden", "true"); item.append(symbol, document.createTextNode(label)); legend.append(item);
  }
  const detail = el("section", "jurisdiction-detail"); detail.id = "jurisdiction-map-detail";
  detail.setAttribute("aria-label", "Selected location"); detail.setAttribute("aria-live", "polite");
  detail.append(el("h3", "", "DOE sites and jurisdictions")); detail.hidden = true;
  layout.append(canvas, detail);
  const caption = el("p", "jurisdiction-caption", "Census boundaries; DOE stars mark published site reference points, not development parcels. Unshaded areas have no mapped record in this collection.");
  const resultsHeading = el("h3", "", "Locations");
  const results = el("ul", "jurisdiction-results"); results.id = "jurisdiction-map-results";
  const more = el("button", "btn-ghost"); more.type = "button"; more.hidden = true;
  const announcements = el("section", "map-announcements"); announcements.id = "jurisdiction-map-announcements";
  const coverage = el("details", "map-coverage"); coverage.append(el("summary", "", "Sources and location coverage"));
  const sources = el("p"); sources.append(link("https://tigerweb.geo.census.gov/tigerweb/", "U.S. Census Bureau"), document.createTextNode(" · "),
    link("https://www.energy.gov/national-laboratories", "DOE laboratories"), document.createTextNode(" · "), link("https://www.energy.gov/em/office-environmental-management", "DOE Environmental Management"),
    document.createTextNode(" · "), link("https://www.energy.gov/nnsa/locations", "NNSA locations"), document.createTextNode(" · "), link("https://www.energy.gov/ea/ea-information-doe-site", "DOE site directory"));
  const coverageList = el("ul");
  for (const note of data.doe.coverage_notes || []) coverageList.append(el("li", "", note));
  coverage.append(sources, coverageList);
  const mapped = new Set(regions.flatMap((item) => [...item.moratorium_ids, ...item.policy_ids]));
  const gaps = new Map((data.geography.unmatched || []).map((item) => [item.record_id, item.reason]));
  const unmapped = [...data.moratoriums.map((item) => ["moratorium", item]), ...data.policies.map((item) => ["policy", item])]
    .filter(([kind, item]) => !mapped.has(item.id) && ["state", "county", "city"].includes(kind === "moratorium" ? item.jurisdiction_type : item.scope)
      && !["benefit_agreement", "company_plan"].includes(item.instrument));
  if (unmapped.length) {
    const missing = el("details"); missing.append(el("summary", "", `Unmapped jurisdictions (${unmapped.length})`));
    for (const [kind, item] of unmapped) {
      const entry = el("p"); entry.append(recordButton(item, kind), document.createTextNode(` · ${gaps.get(item.id) || "Boundary not yet matched."}`)); missing.append(entry);
    }
    coverage.append(missing);
  }
  controls.append(advanced);
  root.replaceChildren(controls, meta, layout, legend, caption, resultsHeading, results, more, announcements, coverage);
  let box = [-128, -60, 64, 37]; let visibleSites = []; let shown = 20; let currentResults = []; let chosen = null;
  function setBox(next) {
    hideTooltip();
    box = next; map.setAttribute("viewBox", box.join(" ")); drawMarkers();
  }
  function fit(bounds) {
    const width = Math.max(bounds[2] - bounds[0], .04); const height = Math.max(bounds[3] - bounds[1], .04);
    const ratio = Math.max(canvas.clientWidth, 320) / Math.max(canvas.clientHeight, 320);
    const w = Math.max(width, height * ratio) * 1.12; const h = w / ratio;
    setBox([(bounds[0] + bounds[2] - w) / 2, (bounds[1] + bounds[3] - h) / 2, w, h]);
  }
  function zoom(factor) {
    const width = Math.min(370, Math.max(.025, box[2] * factor)); const height = box[3] * width / box[2];
    setBox([box[0] + (box[2] - width) / 2, box[1] + (box[3] - height) / 2, width, height]);
  }
  function recordButton(record, kind) {
    const node = el("button", "map-record-link", record.title || record.jurisdiction);
    node.type = "button"; node.dataset.recordId = record.id;
    node.addEventListener("click", () => kind === "moratorium" ? hooks.openMoratorium(record.id) : hooks.openPolicy(record.id));
    return node;
  }
  function revealDetail() {
    detail.tabIndex = -1;
    detail.scrollTop = 0;
    detail.focus({ preventScroll: true });
    detail.scrollIntoView({ block: "nearest" });
  }
  function detailHeading(title) {
    const header = el("div", "map-detail-heading");
    const close = el("button", "btn-ghost", "×"); close.type = "button";
    close.setAttribute("aria-label", "Close location details");
    close.addEventListener("click", () => {
      chosen = null; hideTooltip(); detail.hidden = true; layout.classList.remove("has-selection");
      map.focus({ preventScroll: true });
    });
    header.append(el("h3", "", title), close); return header;
  }
  function showRegion(item) {
    chosen = item.id;
    detail.hidden = false; layout.classList.add("has-selection");
    detail.replaceChildren(detailHeading(`${item.name} · ${hooks.stateNames[item.state_code] || item.state_code}`));
    for (const [kind, records] of [["moratorium", item.moratoriums], ["policy", item.policies]]) {
      for (const record of records) {
        const section = el("section"); section.append(recordButton(record, kind),
          el("p", "muted", `${kind === "moratorium" ? "Moratorium" : "Framework"} · ${status(record, kind).replaceAll("_", " ")} · Recorded ${record.captured_at}`),
          link(record.source_url, record.source_title)); detail.append(section);
      }
    }
    const boundary = el("p", "muted"); boundary.append(link(item.source_url, `Census boundary · ${item.census_geoid}`)); detail.append(boundary);
  }
  function showSites(items) {
    chosen = items.map((site) => site.id).join(",");
    detail.hidden = false; layout.classList.add("has-selection");
    detail.replaceChildren(detailHeading(items.length > 1 ? `${items.length} DOE locations` : items[0].name));
    for (const site of items) {
      const section = el("section"); if (items.length > 1) section.append(el("h4", "", site.name));
      section.append(el("p", "muted", `${site.site_types.map((key) => SITE_LABELS[key]).join(" · ")} · ${hooks.stateNames[site.state_code]} · ${site.location_kind.replaceAll("_", " ")}`));
      const refs = el("p"); refs.append(link(site.source_url, "DOE site source"), document.createTextNode(" · "), link(site.coordinate_source_url, "Coordinate source"));
      section.append(refs);
      for (const event of visibleAnnouncements().filter((item) => item.site_ids.includes(site.id))) section.append(announcementCard(event));
      if (site.notes) {
        const location = el("details"); location.append(el("summary", "", "Location record"), el("p", "", site.notes)); section.append(location);
      }
      detail.append(section);
    }
  }
  function announcementCard(event) {
    const section = el("article", "map-announcement"); section.dataset.announcementId = event.id;
    section.append(el("h4", "", event.title), el("p", "muted", `${event.published_at} · ${event.status_text}`), el("p", "", event.summary), link(event.source_url, "DOE announcement"));
    if (!event.site_ids.length) section.append(el("p", "muted", "National / multiple-site announcement; no project location specified."));
    return section;
  }
  function matches(values) {
    const words = query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const text = values.join(" ").toLowerCase();
    return words.every((word) => text.includes(word));
  }
  function visibleAnnouncements() {
    return showAnnouncements.checked ? data.doe.announcements.filter((event) => (!topic.value || event.topics.includes(topic.value))
      && (!state.value || !event.site_ids.length || event.site_ids.some((id) => sites.some((site) => site.id === id && site.state_code === state.value)))
      && matches([event.title, event.summary, event.status_text, ...sites.filter((site) => event.site_ids.includes(site.id)).flatMap((site) => [site.name, site.state_code, hooks.stateNames[site.state_code]])]))
      .sort((a, b) => b.published_at.localeCompare(a.published_at)) : [];
  }
  let hovered = null; let dismissed = null;
  function hideTooltip() {
    tooltip.hidden = true;
  }
  const dismissTooltip = (event) => { if (event.key === "Escape") { dismissed = hovered; hideTooltip(); } };
  document.addEventListener("keydown", dismissTooltip);
  function hoverDetails(node, title, lines) {
    function show(event) {
      if (event.pointerType === "touch" || drag || dismissed === node) return;
      hovered = node;
      tooltip.replaceChildren(el("strong", "", title), ...lines.map((text) => el("span", "", text)));
      tooltip.hidden = false;
      const bounds = canvas.getBoundingClientRect(); const target = node.getBoundingClientRect();
      const x = event.clientX ?? target.x + target.width / 2;
      const y = event.clientY ?? target.y + target.height / 2;
      tooltip.style.left = `${Math.max(8, Math.min(x - bounds.left + 14, bounds.width - tooltip.offsetWidth - 8))}px`;
      tooltip.style.top = `${Math.max(8, Math.min(y - bounds.top + 14, bounds.height - tooltip.offsetHeight - 8))}px`;
    }
    node.addEventListener("pointerenter", show); node.addEventListener("pointermove", show);
    node.addEventListener("focus", show);
    function leave() { if (dismissed === node) dismissed = null; hovered = null; hideTooltip(); }
    node.addEventListener("pointerleave", leave); node.addEventListener("blur", leave);
    node.setAttribute("aria-describedby", tooltip.id);
  }
  function drawMarkers() {
    const focused = markers.contains(document.activeElement) ? document.activeElement.dataset.siteIds?.split(",") : null;
    markers.replaceChildren();
    const rect = map.getBoundingClientRect();
    const unit = 1 / Math.min(Math.max(rect.width, 320) / box[2], Math.max(rect.height, 320) / box[3]);
    const events = visibleAnnouncements();
    const inBox = ([left, top, right, bottom]) => right >= box[0] && left <= box[0] + box[2]
      && bottom >= box[1] && top <= box[1] + box[3];
    for (const node of fills.children) node.setAttribute("tabindex", inBox(regionsById.get(node.dataset.jurisdictionId).bounds) ? "0" : "-1");
    for (const site of visibleSites) {
      const [x, y] = site.projected;
      const associated = events.filter((event) => event.site_ids.includes(site.id));
      const highlighted = associated.length > 0;
      const node = svg("g", { class: `map-doe-point${highlighted ? " has-announcement" : ""}`, role: "button", tabindex: "0",
        "aria-label": site.name, transform: `translate(${x},${y})` });
      node.dataset.siteIds = site.id;
      node.setAttribute("tabindex", inBox([x, y, x, y]) ? "0" : "-1");
      const star = Array.from({ length: 10 }, (_, index) => {
        const angle = -Math.PI / 2 + index * Math.PI / 5; const radius = (index % 2 ? 3.6 : 8) * unit;
        return `${Math.cos(angle) * radius},${Math.sin(angle) * radius}`;
      }).join(" ");
      const hitRadius = window.matchMedia("(pointer: coarse)").matches ? 22 : 9;
      node.append(svg("circle", { r: hitRadius * unit, class: "map-dot-hit" }), svg("polygon", { points: star, class: "map-dot map-doe-star" }));
      hoverDetails(node, site.name, [site.site_types.map((key) => SITE_LABELS[key]).join(" · "),
        hooks.stateNames[site.state_code], ...associated.slice(0, 2).map((event) => event.title)]);
      node.addEventListener("click", () => { hideTooltip(); showSites([site]); revealDetail(); });
      node.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); hideTooltip(); showSites([site]); } });
      markers.append(node);
    }
    if (focused) {
      const replacement = [...markers.children].find((node) => node.dataset.siteIds.split(",").some((id) => focused.includes(id)));
      replacement?.focus({ preventScroll: true });
    }
  }
  function renderResults() {
    results.replaceChildren();
    for (const item of currentResults.slice(0, shown)) {
      const li = el("li"); const button = el("button", "map-location-link", item.name); button.type = "button";
      button.dataset.locationId = item.id;
      button.addEventListener("click", () => {
        if (item.projected && !item.geometry) { showSites([item]); fit([item.projected[0] - .15, item.projected[1] - .1, item.projected[0] + .15, item.projected[1] + .1]); }
        else { showRegion(item); fit(item.bounds); }
        revealDetail();
      });
      li.append(button, el("span", "muted", ` · ${hooks.stateNames[item.state_code]}`)); results.append(li);
    }
    more.hidden = shown >= currentResults.length;
    more.textContent = `Show ${Math.min(20, currentResults.length - shown)} more locations`;
  }
  function render(resetView = false) {
    hideTooltip();
    const active = (record, kind) => recorded.value === "all" || (recorded.value === "enacted" ? status(record, kind) === (kind === "moratorium" ? "enacted" : "in_effect") : status(record, kind) === "proposed");
    const filtered = regions.filter((item) => (!state.value || item.state_code === state.value) && (!level.value || item.level === level.value)).map((item) => ({ ...item,
      moratoriums: showMoratoriums.checked ? item.moratorium_ids.map((id) => moratoriums.get(id)).filter((record) => record && active(record, "moratorium")) : [],
      policies: showPolicies.checked ? item.policy_ids.map((id) => policies.get(id)).filter((record) => record && active(record, "policy")) : [] }))
      .filter((item) => (item.moratoriums.length || item.policies.length) && matches([item.name, item.state_code, hooks.stateNames[item.state_code], ...item.moratoriums.map((r) => r.jurisdiction), ...item.policies.map((r) => r.title)]));
    const events = visibleAnnouncements();
    visibleSites = sites.filter((site) => (!state.value || site.state_code === state.value) && (!siteKind.value || site.site_types.includes(siteKind.value))
      && (showDOE.checked || events.some((event) => event.site_ids.includes(site.id)))
      && (matches([site.name, site.state_code, hooks.stateNames[site.state_code], site.notes]) || events.some((event) => event.site_ids.includes(site.id))));
    fills.replaceChildren();
    for (const item of filtered) {
      const path = svg("path", { d: item.path, "fill-rule": "evenodd", "vector-effect": "non-scaling-stroke", role: "button", tabindex: "0",
        "aria-label": `${item.name} · ${hooks.stateNames[item.state_code]}`,
        class: `map-jurisdiction ${item.moratoriums.length ? "map-has-moratorium" : ""} ${item.policies.length ? "map-has-policy" : ""}${[...item.moratoriums, ...item.policies].every((record) => record.status === "proposed") ? " map-proposed" : ""}` });
      path.classList.toggle("map-inactive", [...item.moratoriums.map((record) => status(record, "moratorium")), ...item.policies.map((record) => status(record, "policy"))]
        .every((value) => !["enacted", "in_effect", "proposed"].includes(value)));
      path.dataset.jurisdictionId = item.id;
      hoverDetails(path, `${item.name} · ${hooks.stateNames[item.state_code]}`, [
        ...item.moratoriums.map((record) => `Pause / ban · ${status(record, "moratorium")} · ${record.duration_description}`),
        ...item.policies.map((record) => `${record.title} · ${status(record, "policy").replaceAll("_", " ")}`)].slice(0, 4));
      path.addEventListener("click", () => { hideTooltip(); showRegion(item); revealDetail(); });
      path.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); hideTooltip(); showRegion(item); } }); fills.append(path);
    }
    meta.textContent = `${recorded.options[recorded.selectedIndex].text} · ${filtered.length} jurisdictions · ${visibleSites.length} DOE sites · ${events.length} announcements`;
    currentResults = [...filtered, ...visibleSites]; shown = 20; renderResults();
    const anchor = query.value.trim() ? layout : announcements;
    for (const node of [resultsHeading, results, more]) root.insertBefore(node, anchor);
    announcements.replaceChildren(el("h3", "", "DOE announcements"), ...events.map(announcementCard));
    if (!events.length) announcements.append(el("p", "muted", "No matching announcements."));
    if (chosen) {
      const selected = currentResults.filter((item) => chosen.split(",").includes(item.id));
      if (!selected.length) { chosen = null; detail.hidden = true; layout.classList.remove("has-selection"); detail.replaceChildren(); }
      else if (selected[0].geometry) showRegion(selected[0]);
      else showSites(selected);
    }
    if (!currentResults.length) results.append(el("li", "muted", "No matching locations."));
    if (resetView) {
      const selected = stateRegions.get(state.value);
      if (selected) fit(selected.bounds); else setBox([-128, -60, 64, 37]);
    } else drawMarkers();
  }
  more.addEventListener("click", () => { shown += 20; renderResults(); });
  query.addEventListener("input", () => render());
  state.addEventListener("change", () => render(true));
  for (const input of [recorded, level, siteKind, topic, showMoratoriums, showPolicies, showDOE, showAnnouncements]) input.addEventListener("change", () => render());
  map.addEventListener("keydown", (event) => {
    if (event.target !== map) return;
    const move = { ArrowLeft: [-.2, 0], ArrowRight: [.2, 0], ArrowUp: [0, -.2], ArrowDown: [0, .2] }[event.key];
    if (move) { event.preventDefault(); setBox([box[0] + move[0] * box[2], box[1] + move[1] * box[3], box[2], box[3]]); }
    else if (["+", "=", "-"].includes(event.key)) { event.preventDefault(); zoom(event.key === "-" ? 1.55 : .65); }
  });
  let drag = null; let dragged = false;
  map.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 || event.target.closest(".map-doe-point")) return;
    dragged = false;
    drag = { x: event.clientX, y: event.clientY, box: [...box], scale: map.getScreenCTM().a };
  });
  map.addEventListener("pointermove", (event) => {
    if (!drag) return;
    if (!dragged && Math.hypot(event.clientX - drag.x, event.clientY - drag.y) < 4) return;
    dragged = true; map.setPointerCapture(event.pointerId);
    setBox([drag.box[0] - (event.clientX - drag.x) / drag.scale,
      drag.box[1] - (event.clientY - drag.y) / drag.scale, drag.box[2], drag.box[3]]);
  });
  map.addEventListener("click", (event) => { if (dragged) { event.stopPropagation(); dragged = false; } }, true);
  for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) map.addEventListener(name, () => { drag = null; });
  const observer = new ResizeObserver(() => drawMarkers()); observer.observe(canvas);
  render(true);
  return { resize: drawMarkers, destroy() { observer.disconnect(); document.removeEventListener("keydown", dismissTooltip); } };
}

return {mount};
})();
