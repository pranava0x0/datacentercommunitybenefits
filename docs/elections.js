// Loaded on demand. Policy comparisons use the winner and actual prior holder.
function el(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function source(evidence, label = evidence.source_title) {
  const link = el("a", "election-source", label);
  const url = new URL(evidence.source_url);
  if (!["https:", "http:"].includes(url.protocol)) throw new Error("Invalid election source URL");
  link.href = url.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.title = evidence.source_title;
  return link;
}

function winner(record) {
  return (record.candidates || []).find((candidate) => candidate.name === record.result.winner);
}

function change(record) {
  const incoming = winner(record);
  if (!incoming || !record.outgoing) return "";
  if (incoming.name === record.outgoing.name) return "Re-elected";
  const party = (value) => value.toLowerCase().trim().replace(/\s+party$/, "");
  const known = ["democratic", "republican", "independent", "nonpartisan", "libertarian", "green"];
  const before = party(record.outgoing.party);
  const after = party(incoming.party);
  return known.includes(before) && known.includes(after) && before !== after ? "Party change" : "New officeholder";
}

function priorStatements(record) {
  return [...(record.candidates || []).filter((candidate) => candidate.name === record.outgoing?.name)
    .flatMap((candidate) => candidate.statements), ...(record.outgoing?.statements || [])];
}

export function mount(root, data, hooks) {
  if (!Array.isArray(data.races) || !Array.isArray(data.measures) || !data.calendar) {
    throw new Error("Election payload is incomplete");
  }
  const records = [...data.races.filter((record) => winner(record)).map((record) => ({ ...record, kind: "race" })),
    ...data.measures.map((record) => ({ ...record, kind: "measure" }))];
  const priority = ["TX", "OH", "GA", "IA", "PA", "WI", "OR", "AZ", "NM", "MI"];
  const rank = (record) => {
    const index = priority.indexOf(record.state_code);
    return index < 0 ? priority.length : index;
  };
  records.sort((a, b) => Boolean(b.pause_proposal_topic) - Boolean(a.pause_proposal_topic)
    || (a.kind === "measure") - (b.kind === "measure")
    || rank(a) - rank(b) || a.state_code.localeCompare(b.state_code)
    || (a.level === "governor" ? -1 : b.level === "governor" ? 1 : a.jurisdiction.localeCompare(b.jurisdiction)));

  const heading = el("h2", "hero-title", "Elections");
  const hero = el("div", "hero"); hero.append(heading);
  const filters = el("div", "filter-bar election-filters");
  filters.setAttribute("role", "group");
  filters.setAttribute("aria-label", "Filter policies");
  const searchLabel = el("label", "", "Search");
  const search = el("input");
  search.type = "search";
  search.id = "elections-q";
  search.placeholder = "State, person or policy";
  searchLabel.append(search);
  function picker(id, label, options) {
    const wrapper = el("label", "", label);
    const select = el("select");
    select.id = id;
    for (const [value, text] of options) select.add(new Option(text, value));
    wrapper.append(select);
    filters.append(wrapper);
    return select;
  }
  filters.append(searchLabel);
  const state = picker("elections-state", "State", [["", "All states"],
    ...[...new Set(records.map((record) => record.state_code))].sort().map((code) => [code, hooks.stateNames[code] || code])]);
  const kind = picker("elections-kind", "Office or measure", [["", "All"], ["governor", "Governors"], ["local", "Local officials"], ["measure", "Ballot measures"]]);
  const status = picker("elections-status", "Officeholder", [["", "All"], ["changes", "New officeholders"], ["party", "Party changes"], ["reelected", "Re-elected"]]);
  const moreFilters = el("details", "election-more-filters");
  moreFilters.append(el("summary", "", "More filters"));
  const secondary = el("div", "election-secondary");
  secondary.append(kind.parentElement, status.parentElement);
  moreFilters.append(secondary);
  const reset = el("button", "btn-ghost", "Reset");
  reset.type = "button";
  reset.id = "elections-reset";
  filters.append(reset, moreFilters);
  const count = el("p", "muted");
  count.id = "elections-meta";
  count.setAttribute("role", "status");
  const list = el("div", "election-directory");
  list.id = "elections-directory";

  const table = el("table", "election-table");
  const caption = el("caption", "sr-only", "November 2026 data-center policy summary");
  const head = el("thead");
  const header = el("tr");
  for (const label of ["Officeholder", "Data-center policy"]) {
    const cell = el("th", "", label);
    cell.scope = "col";
    header.append(cell);
  }
  head.append(header);
  const body = el("tbody");
  table.append(caption, head, body);

  function policyEvidence(record) {
    return [...(winner(record)?.statements || []), ...priorStatements(record)];
  }

  function evidenceBlock(evidence, documentLabel = "Documented action") {
    const block = el("div", "election-evidence");
    if (!evidence.speaker) block.append(el("p", "muted", documentLabel));
    block.append(el("blockquote", "", evidence.statement));
    const citation = el("p", "muted");
    citation.append(source(evidence));
    citation.append(document.createTextNode(` · ${evidence.published_at || `Accessed ${evidence.captured_at}`}`));
    block.append(citation);
    return block;
  }

  function recordCard(record) {
    const card = el("article", "election-card");
    if (record.kind === "race") {
      const incoming = winner(record);
      const same = incoming.name === record.outgoing?.name;
      const lead = record.proposed_changes.find((item) => item.topic === record.pause_proposal_topic) || record.proposed_changes[0];
      const evidence = policyEvidence(record);
      for (const policy of record.proposed_changes.filter((item) => item !== lead)) {
        const section = el("section", "election-changes");
        section.append(el("h4", "", policy.topic), el("p", "", policy.summary));
        const citations = el("p");
        for (const url of policy.source_urls) {
          const item = evidence.find((entry) => entry.source_url === url);
          if (!item) throw new Error("Policy comparison citation is missing");
          if (citations.childNodes.length) citations.append(document.createTextNode(" · "));
          citations.append(source(item));
        }
        section.append(citations); card.append(section);
      }
      const candidates = el("div", "election-candidates");
      function panel(person, role, statements) {
        const section = el("section", "election-candidate");
        section.append(el("h4", "", `${role} · ${person.name}`));
        for (const statement of statements) section.append(evidenceBlock(statement));
        if (!statements.length) section.append(el("p", "", "No sourced data-center position available."));
        candidates.append(section);
      }
      if (same) {
        panel(incoming, "Current officeholder", [...incoming.statements, ...(record.outgoing.statements || [])]);
        candidates.classList.add("election-single");
      } else {
        panel(incoming, "Incoming", incoming.statements);
        if (record.outgoing) panel(record.outgoing, "Prior holder", priorStatements(record));
      }
      card.append(candidates);
      const identity = el("p", "election-related");
      if (record.result.evidence) identity.append(source(record.result.evidence, "Election source"));
      if (record.outgoing?.evidence) identity.append(source(record.outgoing.evidence, "Officeholder source"));
      card.append(identity);
    } else {
      card.append(evidenceBlock(record.ballot_evidence, "Ballot text"));
    }
    return card;
  }

  function relatedLinks(record, includeState = true) {
    const related = el("div", "election-related");
    if (includeState) {
      const stateLink = el("a", "", hooks.stateNames[record.state_code] || record.state_code);
      stateLink.href = `#state/${record.state_code}`;
      related.append(stateLink);
    }
    for (const [field, label, open] of [["related_moratorium_ids", "Moratorium", hooks.openMoratorium], ["related_policy_ids", "Current policy", hooks.openPolicy]]) {
      for (const id of record[field] || []) {
        const button = el("button", "btn-ghost", label);
        button.type = "button";
        button.dataset.relatedRecord = id;
        button.addEventListener("click", () => open(id));
        related.append(button);
      }
    }
    return related;
  }

  function summaryRow(record) {
    const row = el("tr", "election-row");
    row.id = `election-${record.id}`;
    row.dataset.electionId = record.id;
    row.dataset.kind = record.kind;
    row.dataset.pauseProposal = String(Boolean(record.pause_proposal_topic));
    const place = el("th", "election-place");
    place.scope = "row";
    const location = el("a", "", hooks.stateNames[record.state_code] || record.state_code);
    location.href = `#state/${record.state_code}`;
    const placeHead = el("div", "election-place-head");
    placeHead.append(location, el("span", "election-office", `${record.jurisdiction === hooks.stateNames[record.state_code] ? "" : record.jurisdiction + " · "}${record.office || record.title}`));
    place.append(placeHead);
    const toggle = el("button", "btn-ghost election-toggle", "Statements");
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", `election-details-${record.id}`);
    toggle.setAttribute("aria-label", `Compare details: ${record.jurisdiction} · ${record.office || record.title}`);
    const people = el("div", "election-people");
    const policies = el("td", "election-summary");
    const detail = el("tr", "election-detail-row");
    detail.id = `election-details-${record.id}`;
    detail.hidden = true;
    const detailCell = el("td");
    detailCell.colSpan = 2;
    detail.append(detailCell);
    toggle.addEventListener("click", () => {
      const expanded = toggle.getAttribute("aria-expanded") !== "true";
      if (expanded && !detailCell.childNodes.length) detailCell.append(recordCard(record));
      detail.hidden = !expanded;
      toggle.setAttribute("aria-expanded", String(expanded));
      toggle.textContent = expanded ? "Close statements" : "Statements";
    });
    if (record.kind === "race") {
      const incoming = winner(record);
      const same = incoming.name === record.outgoing?.name;
      const result = el("p", "election-result");
      result.append(el("strong", "", `${incoming.name} (${incoming.party})`),
        el("span", "election-role", same ? " · Re-elected" : " · Incoming"));
      people.append(result);
      if (!same && record.outgoing) {
        const prior = el("p", "election-transition");
        prior.append(el("strong", "", `${record.outgoing.name} (${record.outgoing.party})`),
          el("span", "election-role", " · Prior holder"));
        people.append(prior);
      }
      const evidence = policyEvidence(record);
      const lead = record.proposed_changes.find((item) => item.topic === record.pause_proposal_topic) || record.proposed_changes[0];
      for (const policy of lead ? [lead] : []) {
        const topic = el("p", "election-topic");
        topic.append(el("strong", "", `${policy.topic}: `), document.createTextNode(policy.summary));
        policy.source_urls.forEach((url, index) => {
          const item = evidence.find((entry) => entry.source_url === url);
          if (!item) throw new Error("Policy comparison citation is missing");
          const citation = source(item, `[${index + 1}]`);
          citation.setAttribute("aria-label", `${policy.topic}: ${item.source_title}`);
          topic.append(document.createTextNode(" "), citation);
        });
        policies.append(topic);
      }
      const holders = same ? [[incoming, [...incoming.statements, ...(record.outgoing.statements || [])]]]
        : [[incoming, incoming.statements], ...(record.outgoing ? [[record.outgoing, priorStatements(record)]] : [])];
      for (const [person, statements] of holders) {
        if (!statements.length) policies.append(el("p", "muted election-missing", `${person.name}: no sourced data-center position available.`));
        else if (!record.proposed_changes?.length) {
          const position = el("p", "election-topic");
          position.append(el("strong", "", `${person.name}: `));
          statements.forEach((item, index) => {
            if (index) position.append(document.createTextNode(" "));
            position.append(document.createTextNode(item.statement + " "), source(item, `[${index + 1}]`));
          });
          policies.append(position);
        }
      }
      if (!same && !record.outgoing) policies.append(el("p", "muted election-missing", "Prior officeholder’s data-center position unavailable."));
    } else {
      const result = el("p", "election-result");
      result.append(el("strong", "", record.result.outcome === "passed" ? "Passed" : record.result.outcome === "failed" ? "Failed" : "Outcome pending"),
        el("span", "election-role", record.effect === "advisory" ? " · Advisory question" : " · Binding measure"));
      if (record.result.evidence) result.append(document.createTextNode(" · "), source(record.result.evidence, "Vote"));
      people.append(result);
      const effect = el("p", "election-topic", record.legal_effect + " ");
      effect.append(source(record.ballot_evidence, "Ballot text"));
      policies.append(effect);
    }
    if (record.related_moratorium_ids?.length || record.related_policy_ids?.length) policies.append(relatedLinks(record, false));
    placeHead.append(toggle);
    place.append(people);
    row.append(place, policies);
    return [row, detail];
  }

  function render() {
    const query = search.value.trim().toLocaleLowerCase();
    const filtered = records.filter((record) => {
      if (state.value && record.state_code !== state.value) return false;
      if (kind.value === "measure" && record.kind !== "measure") return false;
      if (kind.value === "governor" && record.level !== "governor") return false;
      if (kind.value === "local" && (record.kind !== "race" || record.level === "governor")) return false;
      const changed = change(record);
      if (status.value === "changes" && !["New officeholder", "Party change"].includes(changed)) return false;
      if (status.value === "party" && changed !== "Party change") return false;
      if (status.value === "reelected" && changed !== "Re-elected") return false;
      const people = record.kind === "race" ? [winner(record), record.outgoing].filter(Boolean) : [];
      const haystack = [hooks.stateNames[record.state_code], record.state_code, record.jurisdiction, record.office, record.title,
        record.legal_effect, record.ballot_evidence?.statement,
        ...people.flatMap((person) => [person.name, ...(person.statements || []).map((item) => item.statement)]),
        ...priorStatements(record).map((item) => item.statement),
        ...(record.proposed_changes || []).flatMap((item) => [item.topic, item.summary])].join(" ").toLocaleLowerCase();
      return !query || query.split(/\s+/).every((word) => haystack.includes(word));
    });
    const proposals = filtered.filter((record) => record.pause_proposal_topic).length;
    count.textContent = `${proposals ? proposals + " pause proposals · " : ""}${filtered.length} ${kind.value === "measure" ? "ballot measures" : "records"}`;
    body.replaceChildren(...filtered.flatMap(summaryRow));
    list.replaceChildren(filtered.length ? table : el("p", "election-empty", records.length ? "No matching policies." : "No policy records available."));
  }
  function clear() {
    search.value = "";
    state.value = "";
    kind.value = "";
    status.value = "";
    render();
  }
  reset.addEventListener("click", clear);
  search.addEventListener("input", render);
  for (const select of [state, kind, status]) select.addEventListener("change", render);
  root.replaceChildren(hero, filters, count, list);
  render();
  return {
    openRecord(id) {
      if (!records.some((record) => record.id === id)) {
        count.textContent = "Policy record unavailable.";
        return false;
      }
      clear();
      const row = document.getElementById(`election-${id}`);
      const toggle = row.querySelector(".election-toggle");
      toggle.click();
      row.scrollIntoView({ block: "start" });
      toggle.focus({ preventScroll: true });
      return true;
    },
  };
}
