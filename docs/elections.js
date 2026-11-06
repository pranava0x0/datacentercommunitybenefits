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
  return incoming.party === record.outgoing.party ? "New officeholder" : "Party change";
}

function priorStatements(record) {
  return [...(record.outgoing?.statements || []),
    ...(record.candidates || []).filter((candidate) => candidate.name === record.outgoing?.name)
      .flatMap((candidate) => candidate.statements)];
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
  records.sort((a, b) => (a.kind === "measure") - (b.kind === "measure")
    || rank(a) - rank(b) || a.state_code.localeCompare(b.state_code)
    || (a.level === "governor" ? -1 : b.level === "governor" ? 1 : a.jurisdiction.localeCompare(b.jurisdiction)));

  const heading = el("h2", "", "Data-center policy · November 2026");
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
  const reset = el("button", "btn-ghost", "Reset");
  reset.type = "button";
  reset.id = "elections-reset";
  filters.append(reset);
  const count = el("p", "muted");
  count.id = "elections-meta";
  count.setAttribute("role", "status");
  const list = el("div", "election-directory");
  list.id = "elections-directory";

  function evidenceBlock(evidence) {
    const block = el("div", "election-evidence");
    if (!evidence.speaker) block.append(el("p", "muted", "Official record"));
    block.append(el("blockquote", "", evidence.statement));
    const citation = el("p", "muted");
    citation.append(source(evidence));
    if (evidence.published_at) citation.append(document.createTextNode(` · ${evidence.published_at}`));
    block.append(citation);
    return block;
  }

  function recordCard(record) {
    const card = el("article", "election-card");
    card.id = `election-${record.id}`;
    card.dataset.electionId = record.id;
    card.dataset.kind = record.kind;
    const title = el("h3");
    const permalink = el("a", "", `${record.jurisdiction} · ${record.office || record.title}`);
    permalink.href = `#elections/${record.id}`;
    title.append(permalink);
    card.append(title);
    if (record.kind === "race") {
      const incoming = winner(record);
      const same = incoming.name === record.outgoing?.name;
      const result = el("p", "election-result");
      result.append(el("strong", "", `${incoming.name} (${incoming.party})`),
        document.createTextNode(same ? " · Re-elected" : " · Incoming"));
      card.append(result);
      if (!same && record.outgoing) {
        const transition = el("p", "election-transition", `Outgoing: ${record.outgoing.name} (${record.outgoing.party}) · `);
        transition.append(source(record.outgoing.evidence, "Officeholder"));
        card.append(transition);
      }
      const comparisons = el("div", "election-changes");
      const evidence = [...incoming.statements, ...priorStatements(record)];
      for (const policy of record.proposed_changes || []) {
        const section = el("section");
        section.append(el("h4", "", policy.topic), el("p", "", policy.summary));
        const citations = el("p", "muted");
        for (const url of policy.source_urls) {
          const item = evidence.find((entry) => entry.source_url === url);
          if (!item) throw new Error("Policy comparison citation is missing");
          if (citations.childNodes.length) citations.append(document.createTextNode(" · "));
          citations.append(source(item));
        }
        section.append(citations);
        comparisons.append(section);
      }
      card.append(comparisons);
      const candidates = el("div", "election-candidates");
      function panel(person, role, statements) {
        const section = el("section", "election-candidate");
        section.append(el("h4", "", `${role} · ${person.name}`));
        for (const statement of statements) section.append(evidenceBlock(statement));
        if (!statements.length) section.append(el("p", "muted", "No sourced data-center position available."));
        candidates.append(section);
      }
      if (same) {
        const statements = [...incoming.statements, ...(record.outgoing.statements || [])];
        panel(incoming, "Current officeholder", statements);
        candidates.classList.add("election-single");
      } else {
        panel(incoming, "Incoming", incoming.statements);
        if (record.outgoing) panel(record.outgoing, "Outgoing", priorStatements(record));
        else candidates.append(el("p", "muted", "Prior officeholder’s data-center position unavailable."));
      }
      card.append(candidates);
    } else {
      card.append(el("p", "election-result", `${record.result.outcome === "passed" ? "Passed" : record.result.outcome === "failed" ? "Failed" : "Outcome pending"} · ${record.effect === "advisory" ? "Advisory question" : "Binding measure"}`),
        el("p", "", record.legal_effect), evidenceBlock(record.ballot_evidence));
    }
    const related = el("div", "election-related");
    const stateLink = el("a", "", hooks.stateNames[record.state_code] || record.state_code);
    stateLink.href = `#state/${record.state_code}`;
    related.append(stateLink);
    for (const [field, label, open] of [["related_moratorium_ids", "Moratorium", hooks.openMoratorium], ["related_policy_ids", "Current policy", hooks.openPolicy]]) {
      for (const id of record[field] || []) {
        const button = el("button", "btn-ghost", label);
        button.type = "button";
        button.dataset.relatedRecord = id;
        button.addEventListener("click", () => open(id));
        related.append(button);
      }
    }
    card.append(related);
    return card;
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
    count.textContent = `${filtered.length} ${kind.value === "measure" ? "ballot measures" : "records"}`;
    list.replaceChildren(...filtered.map(recordCard));
    if (!filtered.length) list.append(el("p", "election-empty", records.length ? "No matching policies." : "No policy records available."));
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
  root.replaceChildren(heading, filters, count, list);
  render();
  return {
    openRecord(id) {
      if (!records.some((record) => record.id === id)) {
        count.textContent = "Policy record unavailable.";
        return false;
      }
      clear();
      const card = document.getElementById(`election-${id}`);
      card.scrollIntoView({ block: "start" });
      card.querySelector("h3 a").focus({ preventScroll: true });
      return true;
    },
  };
}
