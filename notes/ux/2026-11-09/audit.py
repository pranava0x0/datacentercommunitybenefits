import json, subprocess, sys, time, socket
from pathlib import Path
from playwright.sync_api import sync_playwright
REPO = Path(sys.argv[1]); OUT = Path(sys.argv[2])
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(REPO / "docs")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
VIEWS = ["overview","ratepayer","policies","agreements","moratoriums","elections","tariffs","comparison","explorer","world"]
SIZES = {"desktop": (1366, 900, False), "tablet": (820, 1180, True), "phone": (390, 844, True)}
MEASURE = r"""
() => {
  const vh = innerHeight, vw = innerWidth;
  const view = document.querySelector('.view:not([hidden])');
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width>0 && r.height>0 && cs.visibility!=='hidden' && cs.display!=='none'; };
  const q = s => [...(view||document).querySelectorAll(s)].filter(vis);
  const top = el => el.getBoundingClientRect().top + scrollY;
  // first "data" element: table row, card, list item with link, chart
  const dataSel = 'table tbody tr, .card, [class*="-card"], .rp-card, li.project, #project-list li, .matrix-body tr, .mor-row, svg, canvas, .leaflet-container';
  const firstData = q(dataSel)[0];
  const headings = q('h2,h3').map(h => h.textContent.trim().replace(/\s+/g,' ').slice(0,70));
  const small = [...document.querySelectorAll('a,button,select,input,summary,[role=button],[role=tab]')].filter(vis).filter(e => { const r=e.getBoundingClientRect(); return (r.width<24||r.height<24) && r.top < document.body.scrollHeight; }).length;
  const overflow = [...document.querySelectorAll('nav, .tabbar, .subtabs, .filter-bar, main, header, .view > *')].filter(vis).filter(e => e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX !== 'auto' && getComputedStyle(e).overflowX !== 'scroll').map(e => (e.id||e.className||e.tagName).toString().slice(0,40));
  const fonts = new Set(); const sizes = new Set();
  q('h1,h2,h3,h4,p,li,td,th,span,a,button,summary,label').slice(0,800).forEach(e => { const cs=getComputedStyle(e); fonts.add(cs.fontFamily.split(',')[0]); sizes.add(cs.fontSize); });
  const tabs = [...document.querySelectorAll('[role=tab]')].filter(vis);
  const tabbar = document.querySelector('.tabbar, nav[aria-label*="ections"], .tabs');
  return {
    page_screens: +(document.documentElement.scrollHeight / vh).toFixed(1),
    first_data_screens: firstData ? +(top(firstData)/vh).toFixed(2) : null,
    first_data: firstData ? (firstData.className || firstData.tagName).toString().slice(0,50) : null,
    headings: headings.length, heading_list: headings.slice(0,25),
    accordions: q('details').length, accordions_closed: q('details:not([open])').length,
    subtabs: q('.subtabs [role=tab], .subtab').length,
    selects: q('select').length, inputs: q('input:not([type=hidden])').length, buttons: q('button').length,
    links: q('a').length, small_targets: small, overflow,
    font_families: [...fonts], font_sizes: sizes.size,
    words: ((view||document.body).innerText||'').split(/\s+/).length,
    intro_words_above_data: firstData ? (() => { let w=0; const walker=document.createTreeWalker(view||document.body, NodeFilter.SHOW_TEXT); let n; while((n=walker.nextNode())){ const p=n.parentElement; if(!p||!vis(p)) continue; if(top(p) >= top(firstData)) break; w += n.textContent.trim().split(/\s+/).filter(Boolean).length; } return w; })() : null,
    nav_tabs_visible: [...document.querySelectorAll('.tab, #tabs a, nav [role=tab]')].filter(vis).length,
    tabbar_height: tabbar ? Math.round(tabbar.getBoundingClientRect().height) : null,
    header_height: Math.round((document.querySelector('header')||document.body).getBoundingClientRect().height),
  };
}
"""
res = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for dev,(w,h,touch) in SIZES.items():
        ctx = b.new_context(viewport={"width":w,"height":h}, is_mobile=touch and w<700, has_touch=touch)
        for v in VIEWS:
            pg = ctx.new_page(); errs=[]; bad=[]
            pg.on("console", lambda m, errs=errs: m.type in ("error","warning") and errs.append(m.text[:160]))
            pg.on("pageerror", lambda e, errs=errs: errs.append("PAGEERROR "+str(e)[:160]))
            pg.on("response", lambda r, bad=bad: r.status>=400 and bad.append(f"{r.status} {r.url[-60:]}"))
            t0=time.time(); pg.goto(f"http://127.0.0.1:{port}/?u={dev}{v}#{v}", wait_until="load")
            try: pg.wait_for_load_state("networkidle", timeout=8000)
            except Exception: pass
            pg.wait_for_timeout(600)
            m = pg.evaluate(MEASURE); m["load_s"]=round(time.time()-t0,2); m["console"]=errs; m["http_errors"]=[x for x in bad if "arcgisonline" not in x and "tile" not in x]
            res[f"{dev}:{v}"]=m
            if dev!="tablet": pg.screenshot(path=str(OUT/f"{dev}-{v}.png"))
            pg.close()
        ctx.close()
    b.close()
srv.terminate()
(OUT.parent/"audit.json").write_text(json.dumps(res, indent=1))
for k,m in res.items():
    print(f"{k:22} screens={m['page_screens']:5} firstData@{m['first_data_screens']} introW={m['intro_words_above_data']} h={m['headings']} acc={m['accordions']}({m['accordions_closed']}c) sub={m['subtabs']} sel={m['selects']} btn={m['buttons']} small={m['small_targets']} fs={m['font_sizes']} ff={len(m['font_families'])} tabbarH={m['tabbar_height']} hdrH={m['header_height']} ovf={m['overflow']} err={len(m['console'])+len(m['http_errors'])}")
