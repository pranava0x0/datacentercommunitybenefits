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

export function mount(root, data, hooks) {
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
  const recorded = select("jurisdiction-map-status", "Recorded status", [["enacted", "Enacted / in effect"], ["proposed", "Proposed"], ["all", "All recorded"]]);
  const level = select("jurisdiction-map-level", "Jurisdiction", [["", "All levels"], ["state", "State"], ["county", "County"], ["city", "City / town"]]);
  const siteKind = select("jurisdiction-map-site-kind", "DOE locations", [["", "All types"], ...Object.entries(SITE_LABELS)]);
  const topic = select("jurisdiction-map-topic", "Announcements", [["", "All topics"], ...Object.entries(TOPIC_LABELS)]);
  const advanced = el("details", "map-filters"); advanced.append(el("summary", "", "More filters"));
  const advancedControls = el("div", "filter-bar jurisdiction-filters");
  for (const input of [level, siteKind, topic]) advancedControls.append(input.parentElement);
  advanced.append(advancedControls);
  const layers = el("fieldset", "jurisdiction-layers"); layers.append(el("legend", "sr-only", "Map layers"));
  function checkbox(key, text) {
    const label = el("label", `map-key-${key}`); const input = el("input");
    input.type = "checkbox"; input.checked = true; input.id = `map-layer-${key}`;
    label.append(input, document.createTextNode(text)); layers.append(label); return input;
  }
  const showMoratoriums = checkbox("moratoriums", "Moratoriums");
  const showPolicies = checkbox("policies", "Policy frameworks");
  const showDOE = checkbox("doe", "DOE reference points");
  const showAnnouncements = checkbox("announcements", "Announcements");
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
  canvas.append(map, toolbar);
  const detail = el("section", "jurisdiction-detail"); detail.id = "jurisdiction-map-detail";
  detail.setAttribute("aria-label", "Selected location"); detail.setAttribute("aria-live", "polite");
  detail.append(el("h3", "", "DOE sites and jurisdictions"));
  layout.append(canvas, detail);
  const caption = el("p", "jurisdiction-caption", "Generalized Census jurisdiction boundaries. DOE dots are published reference points; development parcels may differ.");
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
  root.replaceChildren(controls, layers, meta, layout, caption, advanced, resultsHeading, results, more, announcements, coverage);
  let box = [-128, -60, 64, 37]; let visibleSites = []; let shown = 20; let currentResults = []; let chosen = null;
  function setBox(next) {
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
  function showRegion(item) {
    chosen = item.id;
    detail.replaceChildren(el("h3", "", `${item.name} · ${hooks.stateNames[item.state_code] || item.state_code}`));
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
    detail.replaceChildren(el("h3", "", items.length > 1 ? `${items.length} DOE locations` : items[0].name));
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
  function drawMarkers() {
    const focused = markers.contains(document.activeElement) ? document.activeElement.dataset.siteIds?.split(",") : null;
    markers.replaceChildren();
    const rect = map.getBoundingClientRect();
    const unit = 1 / Math.min(Math.max(rect.width, 320) / box[2], Math.max(rect.height, 320) / box[3]); const groups = [];
    for (const site of visibleSites) {
      const group = groups.find((item) => Math.hypot(item[0].projected[0] - site.projected[0], item[0].projected[1] - site.projected[1]) < 24 * unit);
      if (group) group.push(site); else groups.push([site]);
    }
    const events = visibleAnnouncements();
    for (const group of groups) {
      const x = group.reduce((sum, item) => sum + item.projected[0], 0) / group.length;
      const y = group.reduce((sum, item) => sum + item.projected[1], 0) / group.length;
      const highlighted = group.some((site) => events.some((event) => event.site_ids.includes(site.id)));
      const node = svg("g", { class: `map-doe-point${highlighted ? " has-announcement" : ""}`, role: "button", tabindex: "0",
        "aria-label": group.length > 1 ? `${group.length} DOE reference points` : group[0].name, transform: `translate(${x},${y})` });
      node.dataset.siteIds = group.map((item) => item.id).join(",");
      node.append(svg("circle", { r: 22 * unit, class: "map-dot-hit" }), svg("circle", { r: (group.length > 1 ? 10 : 6) * unit, class: "map-dot" }));
      if (group.length > 1) {
        const label = svg("text", { "text-anchor": "middle", dy: ".35em", "font-size": 11 * unit }); label.textContent = group.length; node.append(label);
      }
      const title = svg("title"); title.textContent = group.map((site) => site.name).join("; "); node.append(title);
      function open(reveal = false) {
        showSites(group);
        if (group.length > 1) fit(extent(group.map((site) => site.projected)));
        if (reveal) revealDetail();
      }
      node.addEventListener("click", () => open(true));
      node.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); } });
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
      const path = svg("path", { d: item.path, "fill-rule": "evenodd", "vector-effect": "non-scaling-stroke",
        class: `map-jurisdiction ${item.moratoriums.length ? "map-has-moratorium" : ""} ${item.policies.length ? "map-has-policy" : ""}${[...item.moratoriums, ...item.policies].every((record) => record.status === "proposed") ? " map-proposed" : ""}` });
      path.classList.toggle("map-inactive", [...item.moratoriums.map((record) => status(record, "moratorium")), ...item.policies.map((record) => status(record, "policy"))]
        .every((value) => !["enacted", "in_effect", "proposed"].includes(value)));
      path.dataset.jurisdictionId = item.id;
      const title = svg("title"); title.textContent = `${item.name}: ${item.moratoriums.length} moratoriums, ${item.policies.length} frameworks`; path.append(title);
      path.addEventListener("click", () => { showRegion(item); revealDetail(); }); fills.append(path);
    }
    meta.textContent = `${filtered.length} jurisdictions · ${visibleSites.length} DOE reference points · ${events.length} announcements`;
    currentResults = [...filtered, ...visibleSites]; shown = 20; renderResults();
    const anchor = query.value.trim() ? layout : announcements;
    for (const node of [resultsHeading, results, more]) root.insertBefore(node, anchor);
    announcements.replaceChildren(el("h3", "", "DOE announcements"), ...events.map(announcementCard));
    if (!events.length) announcements.append(el("p", "muted", "No matching announcements."));
    if (chosen) {
      const selected = currentResults.filter((item) => chosen.split(",").includes(item.id));
      if (!selected.length) { chosen = null; detail.replaceChildren(el("h3", "", "No location selected")); }
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
  return { resize: drawMarkers, destroy() { observer.disconnect(); } };
}
