// Loaded only when the Elections view opens. Every policy quote and result
// has its own citation; a campaign promise never becomes a legal record here.
function el(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function source(evidence, label = "Source") {
  const link = el("a", "election-source", label);
  const url = new URL(evidence.source_url);
  if (!["https:", "http:"].includes(url.protocol)) throw new Error("Invalid election source URL");
  link.href = url.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.title = evidence.source_title;
  return link;
}

const RESULT_LABEL = { unverified: "Result not verified", reported: "Reported · not certified", certified: "Certified" };

function winner(record) {
  return (record.candidates || []).find((candidate) => candidate.name === record.result.winner);
}

function change(record) {
  const incoming = winner(record);
  if (!incoming || !record.outgoing) return "";
  if (incoming.name === record.outgoing.name) return "Re-elected";
  const knownParties = ["Democratic", "Republican", "Independent", "Nonpartisan", "Libertarian", "Green"];
  if (!knownParties.includes(incoming.party) || !knownParties.includes(record.outgoing.party)) return "New officeholder";
  return incoming.party === record.outgoing.party ? "New officeholder · same party" : "Party change";
}

export function mount(root, data, hooks) {
  if (!Array.isArray(data.races) || !Array.isArray(data.measures) || !data.calendar) {
    throw new Error("Election payload is incomplete");
  }
  const records = [...data.races.map((record) => ({ ...record, kind: "race" })),
    ...data.measures.map((record) => ({ ...record, kind: "measure" }))];
  const priority = ["TX", "OH", "GA", "IA", "PA", "WI", "OR", "AZ", "NM", "MI"];
  const rank = (record) => {
    const index = priority.indexOf(record.state_code);
    return index < 0 ? priority.length : index;
  };
  records.sort((a, b) => rank(a) - rank(b) || a.state_code.localeCompare(b.state_code)
    || (a.level === "governor" ? -1 : b.level === "governor" ? 1 : a.jurisdiction.localeCompare(b.jurisdiction)));

  const heading = el("div", "hero");
  heading.append(el("h2", "", "Elections · November 2026"),
    el("p", "hero-dek", "Who won, what candidates said about data centers, and what local ballot measures do."));
  const capturedThrough = [data.calendar.captured_at, ...records.map((record) => record.captured_at)].sort().at(-1);
  const checked = el("p", "muted", `Evidence captured through ${capturedThrough}. Reported results await certification. Candidate proposals require separate government action.`);
  const governors = data.races.filter((record) => record.level === "governor");
  const reported = records.filter((record) => record.result.status !== "unverified");
  const summary = el("p", "election-summary", `${governors.length} governor races · ${data.races.length - governors.length} other races · ${data.measures.length} ballot measures · ${reported.length} results verified in the cited sources`);
  summary.id = "elections-summary";

  const filters = el("div", "filter-bar election-filters");
  filters.setAttribute("role", "group");
  filters.setAttribute("aria-label", "Filter election records");
  const searchLabel = el("label", "", "Search");
  const search = el("input");
  search.type = "search";
  search.id = "elections-q";
  search.placeholder = "State, candidate, place or policy";
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
  const kind = picker("elections-kind", "Office or measure", [["", "All records"], ["governor", "Governor races"], ["local", "Other races"], ["measure", "Ballot measures"]]);
  const status = picker("elections-status", "Show", [["", "All results"], ["changes", "New officeholders"], ["party", "Party changes"], ["unverified", "Results not verified"], ["certified", "Certified results"]]);
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
    block.append(el("blockquote", "", evidence.statement));
    const citation = el("p", "muted");
    citation.append(source(evidence, evidence.source_title),
      document.createTextNode(` · ${evidence.published_at ? `Published ${evidence.published_at} · ` : ""}Checked ${evidence.captured_at}`));
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
    const result = el("p", "election-result");
    if (record.result.status === "unverified") {
      result.append(document.createTextNode("No result verified in this pass. "));
    } else if (record.kind === "race") {
      const candidate = winner(record);
      result.append(el("strong", "", `${record.result.winner} (${candidate.party})`), document.createTextNode(" won. "));
    } else {
      result.append(el("strong", "", record.result.outcome === "passed" ? "Passed" : "Failed"), document.createTextNode(` · ${record.effect === "advisory" ? "Advisory question" : "Binding measure"}. `));
    }
    result.append(el("span", "election-status", RESULT_LABEL[record.result.status]));
    if (record.result.evidence) result.append(document.createTextNode(" "), source(record.result.evidence, "Result source"));
    card.append(result);
    if (record.outgoing) {
      const transition = el("p", "election-transition");
      transition.append(document.createTextNode(`At election time: ${record.outgoing.name} (${record.outgoing.party}). `), source(record.outgoing.evidence, "Officeholder source"));
      const changed = change(record);
      if (changed) transition.append(document.createTextNode(` · ${changed}`));
      card.append(transition);
    } else if (record.kind === "race") {
      card.append(el("p", "muted", "Officeholder at election time not verified in this pass."));
    }
    if (record.kind === "measure") card.append(el("p", "", record.legal_effect));
    if (record.notes) card.append(el("p", "muted", record.notes));

    const details = el("details", "election-details");
    details.append(el("summary", "", record.kind === "race" ? "Candidate statements and evidence" : "Ballot wording and evidence"));
    if (record.result.evidence) {
      const resultEvidence = evidenceBlock(record.result.evidence);
      resultEvidence.prepend(el("h4", "", "Result evidence"));
      details.append(resultEvidence);
    }
    if (record.kind === "race") {
      const candidates = el("div", "election-candidates");
      for (const candidate of record.candidates) {
        const panel = el("section", "election-candidate");
        panel.append(el("h4", "", `${candidate.name} · ${candidate.party}`));
        if (candidate.statements.length) {
          for (const statement of candidate.statements) panel.append(evidenceBlock(statement));
        } else {
          panel.append(el("p", "muted", "No data-center statement verified in this pass."));
        }
        if (candidate.review_note) panel.append(el("p", "muted election-review-note", candidate.review_note));
        candidates.append(panel);
      }
      if (!record.candidates.length) candidates.append(el("p", "muted", "Candidate statements have not been reviewed."));
      details.append(candidates);
    } else {
      details.append(evidenceBlock(record.ballot_evidence));
    }
    card.append(details);
    const related = el("div", "election-related");
    const stateLink = el("a", "", `${hooks.stateNames[record.state_code] || record.state_code}: sites, pledge and rules`);
    stateLink.href = `#state/${record.state_code}`;
    related.append(stateLink);
    for (const [field, label, open] of [["related_moratorium_ids", "Moratorium record", hooks.openMoratorium], ["related_policy_ids", "Policy record", hooks.openPolicy]]) {
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
      if (["unverified", "certified"].includes(status.value) && record.result.status !== status.value) return false;
      const changed = change(record);
      if (status.value === "changes" && !["New officeholder", "New officeholder · same party", "Party change"].includes(changed)) return false;
      if (status.value === "party" && changed !== "Party change") return false;
      const haystack = [hooks.stateNames[record.state_code], record.state_code, record.jurisdiction, record.office, record.title,
        record.legal_effect, record.ballot_evidence?.statement,
        ...(record.candidates || []).flatMap((candidate) => [candidate.name,
          ...candidate.statements.map((statement) => statement.statement)])].join(" ").toLocaleLowerCase();
      return !query || query.split(/\s+/).every((word) => haystack.includes(word));
    });
    count.textContent = `${filtered.length} of ${records.length} election records`;
    list.replaceChildren(...filtered.map(recordCard));
    if (!filtered.length) list.append(el("p", "election-empty", records.length ? "No records match these filters. Reset to see all records." : "No election records have been verified yet. See the coverage notes below."));
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

  const coverage = el("details", "acc election-coverage");
  coverage.append(el("summary", "", "Coverage and sources"));
  const notes = el("ul");
  for (const note of data.coverage_notes || []) notes.append(el("li", "", note));
  coverage.append(notes, source(data.calendar, "Governor election calendar · National Governors Association"));
  root.replaceChildren(heading, checked, summary, filters, count, list, coverage);
  render();
  return {
    openRecord(id) {
      if (!records.some((record) => record.id === id)) {
        count.textContent = "This election record was not found. The directory below is still available.";
        return false;
      }
      clear();
      const card = document.getElementById(`election-${id}`);
      card.querySelector("details").open = true;
      card.scrollIntoView({ block: "start" });
      card.querySelector("h3 a").focus({ preventScroll: true });
      return true;
    },
  };
}
