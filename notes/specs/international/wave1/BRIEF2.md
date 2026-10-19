# Wave-1 research, pass 2 — VERIFIED records only

Read BRIEF.md in this folder for the record format, owner decisions and hard rules. Changes for this pass:

1. **Verification is mechanical, not by summary.** A WebFetch result is a model summary, NOT page text.
   For every verbatim you record, run (from the repo root):
     `.venv/bin/python scripts/probe.py "<URL>" "<distinctive phrase from your verbatim>"`
   It fetches the raw page and prints HIT/MISS with context. Copy the verbatim from probe's printed
   context. Only HIT verbatims count; set "verified": true only when every factual field's phrase HITs.
   If probe gets 403/blocked, try the official alternative (gov page, regulator, company newsroom,
   Wikipedia for coordinates); if none HITs, mark verified false.
   For PDFs probe can't read: `curl -sL -A "Mozilla/5.0" -o /tmp/x.pdf URL` then
   `osascript -l JavaScript /tmp/pdftext.js /tmp/x.pdf | grep -i "<phrase>"` (that script prints PDF
   text via macOS PDFKit; create it if missing with: ObjC.import('PDFKit'); function run(a){return
   $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(a[0])).string.js;} ).
2. Budget: up to ~45 fetches (WebFetch + probe). Space requests to one host ≥2 s.
3. Aim for 3–6 VERIFIED records per country. Fewer verified beats more unverified.
4. Spanish ("es"), French, Swedish, Finnish, Greek quotes stay in the original; add an English
   "translation" (by "machine").
5. Include a lat/lon for every project from a page you probed (Wikipedia town coordinates are fine).
6. Context facts: at least 1 per country (a sourced number), verbatim probe-HIT.
Write your output JSON (same format as BRIEF.md) AS YOU GO. Do not edit the repo except your output file.
