# UX audit — 2026-11-09 (main @ 2a92cbe)

## How this was run

- I loaded all 10 tabs cold at three widths: 1366×900, 820×1180 (touch) and 390×844 (phone).
- On each one I measured:
  - page length in screens;
  - where the first record appears;
  - the number of words above it;
  - controls;
  - touch targets under 24 px;
  - horizontal overflow;
  - console errors and HTTP errors.
- I read first-screen screenshots of every tab.
- I also ran `tools/interaction_cost.py`.

Re-run:

```bash
python3 notes/ux/2026-11-09/audit.py "$PWD" /tmp/ux-shots     # needs .venv with playwright
python3 tools/interaction_cost.py
```

Raw numbers are in `audit.json`.

**What is fine:**
- Zero console errors, zero failed requests, and no horizontal overflow at any width.
- Two font families.
- Every scripted task finishes in 0–6 taps.

**What is wrong:** the problem is not depth. The site does not tell a reader where they are, the same thing goes by different names in different places, and the same quantity shows different numbers in different places. A reader who checks one number against another loses trust.

---

## P1 — Fix first (confusing or contradictory)

### 1. The same number differs between Home and the tab it links to

| Home card | Tab header | Why they differ |
|---|---|---|
| Policy Frameworks "127 in effect" | Frameworks "**114** Laws, orders, and deals in effect" | Home counts company plans; the tab excludes `scope: company` (app.js:3196) |
| Benefits "34 · 21 signed" | Frameworks "**45** Benefit agreements or funds" | Home counts benefit-agreement records; the tab counts the `community_benefits_framework` flag across all instruments (app.js:3199) |
| Elections "37 officeholders · 17 ballot measures" | Elections "**20** New officeholders · **15** Measures passed" | Different subsets: winners vs. changed seats, all measures vs. passed |
| Static summary "158 executive orders, laws, regulations and local ordinances" | — | The 158 also includes benefit agreements and company plans |

**Repro:**
1. Open `/#overview` and note the Policy Frameworks card.
2. Click it, and compare with the first stat on `/#policies`.

**Do:** derive each Home number and its tab-header number from one shared function, or label both by the same rule ("127 in effect, incl. company plans"). Add a test that asserts Home card numbers equal the tab's lead stat.

### 2. Tab names, page titles and the Home summary use different words for the same place

| Tab bar | Page heading | Home / static summary | Old names still in docs |
|---|---|---|---|
| Benefits | "Benefits" | "benefit agreements" | Benefit Agreements |
| Regulatory | "Regulatory" | "Who pays for the power…" / tariffs & rate cases | Tariffs & Rate Cases |
| Policy Frameworks (phone: "Frameworks") | "Policy frameworks" | — | Local Policy Frameworks / Policy Playbook |
| Sites | "Data center sites" | — | — |
| International (phone: "World") | "International" | — | — |
| Companies | "Companies" | "Published commitments from 17 operators" | — |

**Repro:**
1. Compare the tab bar at 1366 px with the bar at 390 px.
2. Read `docs/llms.txt`.

**Do:**
- Pick one name per tab and use it in the tab label, the heading, the Home card, llms.txt and the hash.
- "Regulatory" and "Benefits" say least about what they hold. Consider "Power costs" (tariffs + rate cases) and "Benefit agreements".

### 3. The phone masthead drops the word "Policy"

At 390 px the title renders as **"Data Center Tracker"**. `.title-long` hides the middle word, and the middle word is now "Policy", the one word the rename was for.

**Repro:**
1. Load `/` at 390×844.
2. Read the top-left heading.

**Do:** shorten it to "DC Policy Tracker", or let "Data Center Policy Tracker" wrap or shrink. Never drop "Policy".

### 4. The site-wide summary block renders at the bottom of the Sites tab

The static summary ("The record at a glance"), which covers all 9 questions and links to every tab, sits inside `<section id="view-explorer">` (index.html:712, before `view-ratepayer` at 733). It appears under the Sites map and list and nowhere else.

**Repro:**
1. Open `/#explorer`.
2. Scroll to the bottom; "What changed in the November election?" and the rest show up there.

**Do:** move the block inside `#view-overview`, or make it `<noscript>`/visually hidden if it exists only for crawlers. It also duplicates the Home cards.

### 5. The Moratoriums directory has no state and no date column

Rows read "Northampton", "Wells", "Littleton", "Frederick (city)", with no state, so a reader cannot tell Littleton CO from Littleton NH. The list is sorted newest-first, but no date is shown, so the order looks random. The desktop page is **27 screens** long because only phones page the list.

**Repro:**
1. Open `/#moratoriums` at 1366 px.
2. Read the first 10 rows, then scroll to the end.

**Do:**
- Add the state to the jurisdiction cell ("Northampton, MA").
- Add a date column (enacted, or proposed / failed).
- Page the list at every width; use `phonePageSize()` / `showMoreControl()` with a desktop size of about 50.
- Stop truncating Duration mid-phrase ("180 days from November 3, 2026…"). Show the length, and put the dates in the detail view.

### 6. The Pledge tab answers its own question last

The heading says the tab shows "who signed … and which sites show it". Before the first site, the reader passes:
- a dark band (collapsed);
- the roster (collapsed);
- Coverage (open, with a 50-state grid);
- Signer categories;
- Utilities.

That is **224 words**. The site scorecard starts **1.5 screens down on desktop and 2.5 on a phone**. The Coverage state grid also says "Darker states have more records" without saying records of what; it is not pledge data alone.

**Repro:**
1. Open `/#ratepayer` at 390×844.
2. Count swipes until the first site card.

**Do:**
- Put "Tracked sites" second, right under the commitments band, and move Coverage, categories and utilities below it.
- Label the grid legend with what it counts.
- Show the roster and Coverage count chip once, not twice ("350 signatories · as of Nov 4" appears on both).

---

## P2 — Wayfinding and clarity

### 7. Home opens with two unexplained buttons and no one-line purpose

The first things on Home are "Draft a benefit plan" and "Check impact claims", with no context. Nothing says what the site is, who it is for, or what "Latest" covers (introW = 7 words).

**Do:** add one dek line under the masthead ("Sourced tracker of US data-center policy: pauses, rules, agreements, power costs, elections"), and move the two tools into the Frameworks / Benefits tabs where they belong, or label them as tools.

### 8. A tab's stat row describes a different pane than the one that opens

On Regulatory, the stats ("29 Tariffs tracked · 22 Approved · 6 Proposed · 21 States covered") describe tariffs, but the default sub-tab is **Rate cases**. The same mismatch occurs on Frameworks: the stats sit above Principles.

**Do:** make the stat row describe the whole tab ("20 rate cases (10 pending) · 29 tariffs"), or move the stats into each sub-tab.

### 9. The Sites map is hard to read

- The legend box covers the Mid-Atlantic and Northeast, where VA, PA, OH and GA cluster: the densest part of the map.
- The default view spans Edmonton to Guadalajara.
- Markers use many colours. The theme chips above the map also have coloured dots, and the legend explains only size and a grey status scale. Readers will assume colour means theme, and it does not.
- There are 6 dropdowns, 8 theme chips, a sort control, Reset, CSV and PDF before the map (desktop).

**Repro:**
1. Open `/#explorer` at 1366×900.
2. Look at Virginia.

**Do:**
- Make the legend collapsible or move it outside the map.
- Fit the bounds to the US.
- Make marker colour encode one documented thing, or none.
- Collapse the less-used filters (constituency, stance, sort) behind "More filters", as Elections does.

### 10. Elections rows are dense and their buttons are ambiguous

- Each row packs a state link, the office, a "Statements" button and two people into one cell.
- The buttons "Moratorium" and "Current policy" don't say what they open.
- Citations show as bare "[1] [2]".
- The page has no dek, and on a phone it runs **17.7 screens**.

**Do:**
- Name the buttons by destination ("Open TX moratorium record", "Abbott's current policy").
- Add a one-line dek.
- Page the list on a phone.

### 11. Touch targets

The audit counted interactive elements under 24×24 px:

| Tab | Desktop | Tablet | Phone |
|---|---|---|---|
| The Pledge | 151 | 184 | 46 |
| Elections | 141 | — | — |
| Companies | 137 | — | — |

Most are inline source links and matrix cells.

**Do:** pad the inline links to 24 px hit areas; the project already has a 44 px floor for sub-tabs.

---

## P3 — Polish

- The Moratoriums search placeholder is cut off ("Search place, state or").
- The Elections "Statements" toggles look like buttons but sit inline beside text.
- The Companies "Specific / General / None found" legend is good. Reuse the same pattern to explain the Pledge state grid and the map.
- Ten top-level tabs wrap into two rows on tablet and phone (88 px of chrome). If any tab is merged (for example Companies into Sites, or Elections into Frameworks after the election cycle), the bar fits on one row.

## Suggested order

1. Items 1, 3 and 4. These are small code changes that remove contradictions; each should land with a guard test.
2. Item 5: moratorium state and date columns, plus paging.
3. Item 2: one name per tab. This is a decision, then a mechanical sweep.
4. Items 6, 7 and 8: reorder the Pledge tab, add a Home dek, and align the stat rows.
5. Items 9 and 10: map legend and filters; Elections buttons.
