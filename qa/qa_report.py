"""QA del reporte en PDF en GitHub Pages (v2.23), en modo demo.

Sirve el repo como lo publica GitHub Pages y comprueba que vendor/ (pdfmake +
Inter) está, que la página lo carga desde su propia carpeta (sin CDN) y que un
manager baja el reporte completo con los datos del demo.
"""
import os, re, threading, subprocess, http.server, functools
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = []
def check(desc, cond, detail=''):
    res.append(bool(cond))
    print(('  PASS  ' if cond else '  FAIL  ') + desc + (('  -> ' + str(detail)) if detail != '' and not cond else ''))

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_port}/index.html?demo'

print("\n=== Archivos ===\n")
V = os.path.join(ROOT, 'vendor', 'pdfmake-0.2.10')
for f in ['pdfmake.min.js', 'vfs_inter.js', 'LICENSE-pdfmake.txt', 'LICENSE-Inter.txt']:
    check(f'vendor/pdfmake-0.2.10/{f} está publicado', os.path.isfile(os.path.join(V, f)))
idx = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
check('la página no pide pdfmake a ningún CDN', not re.search(r'(cdn\.jsdelivr|unpkg|cdnjs)[^"\']*pdfmake', idx))

print("\n=== Manager en demo: baja el reporte ===\n")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(accept_downloads=True, viewport={'width': 390, 'height': 844})
    pg = ctx.new_page()
    errs, outside = [], []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('request', lambda r: outside.append(r.url) if 'pdfmake' in r.url and not r.url.startswith(f'http://127.0.0.1:{srv.server_port}/') else None)
    pg.goto(URL); pg.wait_for_function("document.querySelector('#loginName').options.length > 0")
    pg.select_option('#loginName', 'Luis'); pg.fill('#loginPin', '0000'); pg.click('#btnLogin')
    pg.wait_for_selector('#app', state='visible'); pg.click('#navTeam'); pg.wait_for_timeout(400)
    with pg.expect_download(timeout=30000) as dl:
        pg.click('#btnGenerateReport')
    d = dl.value
    path = os.path.join(ROOT, 'qa', '_demo_report.pdf'); d.save_as(path)
    txt = subprocess.run(['pdftotext', path, '-'], capture_output=True, text=True).stdout
    check('se baja como "CapyBros Team Report - fecha.pdf"', re.fullmatch(r'CapyBros Team Report - \d{4}-\d{2}-\d{2}\.pdf', d.suggested_filename), d.suggested_filename)
    check('es el reporte nuevo, no el simple', 'Key takeaways' in txt and 'How to read this report' in txt and 'simple' not in pg.inner_text('#reportHint'))
    check('cargó pdfmake desde la propia página', not outside, outside)
    check('sin errores de JS', not errs, errs)
    os.remove(path)
    b.close()
srv.shutdown()
print(f"\nReporte en Pages: {sum(res)} pass, {len(res) - sum(res)} fail")
