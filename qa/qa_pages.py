"""QA de la versión GitHub Pages (pantallas fuera de Apps Script).

Corre la página como la serviría GitHub Pages (un servidor HTTP local) y
revisa: que la app sea la misma que la de Apps Script, el modo demo, las
sesiones recordadas, los íconos, y el puente api.js contra un /exec falso
(formato del pedido, errores, sin internet, tiempo agotado).

    python3 qa/qa_pages.py <ruta/al/Index.html de Apps Script>
"""
import http.server, json, os, socketserver, subprocess, sys, threading
from functools import partial
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '..', 'uamatchtracker', 'Index.html')

res = []
def check(desc, cond, detail=''):
    res.append(bool(cond))
    print(('  PASS  ' if cond else '  FAIL  ') + desc + (('  -> ' + str(detail)) if detail != '' and not cond else ''))

print("\n=== Build ===\n")
subprocess.run(['node', 'tools/build.mjs', SRC, 'abcdef1234'], cwd=ROOT, check=True, capture_output=True)
built = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
orig = open(SRC, encoding='utf-8').read()
check('el index.html dice que es generado', 'GENERADO por tools/build.mjs' in built.split('\n')[1])
b_start = built.index('<link rel="preconnect"'); o_start = orig.index('<link rel="preconnect"')
check('después de la cabecera, la app es idéntica a la de Apps Script', built[b_start:] == orig[o_start:])
check('sin <base target="_top">', '<base target' not in built)
check('carga config, demo y api antes que la app', built.index('config.js') < built.index('demo.js') < built.index('api.js') < built.index('<link rel="preconnect"'))
check('trae título, íconos y manifest', all(x in built for x in ['<title>Union Arena Tracker</title>', 'apple-touch-icon', 'manifest.webmanifest', 'name="viewport"']))
check('anota versión y commit', '"commit":"abcdef1"' in built and '"version":"' in built)
bad = os.path.join(ROOT, 'qa', '_bad.html')
open(bad, 'w').write(orig.replace('<base target="_top">', ''))
r = subprocess.run(['node', 'tools/build.mjs', bad], cwd=ROOT, capture_output=True, text=True)
check('si la cabecera cambia, el build falla y no publica a medias', r.returncode != 0 and 'esperaba 1' in r.stderr, r.stderr)
os.remove(bad)
subprocess.run(['node', 'tools/build.mjs', SRC, 'abcdef1234'], cwd=ROOT, check=True, capture_output=True)
m = json.load(open(os.path.join(ROOT, 'manifest.webmanifest')))
check('manifest válido con íconos 192 y 512', {i['sizes'] for i in m['icons']} >= {'192x192', '512x512'} and m['display'] == 'standalone')

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), partial(Quiet, directory=ROOT))
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{PORT}/'

def watch(pg):
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'fonts.g' not in m.text and 'Failed to load resource' not in m.text else None)
    return errs

def login(pg, name, pin='0000'):
    pg.wait_for_function("document.querySelector('#loginName').options.length > 0")
    pg.select_option('#loginName', name); pg.fill('#loginPin', pin); pg.click('#btnLogin')

no_overflow = "document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"

with sync_playwright() as p:
    b = p.chromium.launch()

    print("\n=== Íconos y archivos ===\n")
    ctx = b.new_context()
    pg = ctx.new_page()
    for path in ['icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png', 'icons/favicon.png', 'manifest.webmanifest', 'config.js', 'api.js', 'demo.js']:
        r = pg.request.get(BASE + path)
        check(f'{path} responde 200', r.status == 200, r.status)
    ctx.close()

    print("\n=== Modo demo (sin apiUrl) ===\n")
    for role, name in [('member', 'Sofia'), ('manager', 'Luis'), ('admin', 'Hector')]:
        ctx = b.new_context(viewport={'width': 390, 'height': 844})
        pg = ctx.new_page(); errs = watch(pg)
        reqs = []
        pg.on('request', lambda r: reqs.append(r.url) if r.method == 'POST' else None)
        pg.goto(BASE); login(pg, name)
        pg.wait_for_selector('#app', state='visible')
        check(f'{role}: entra', pg.is_visible('#app'))
        check(f'{role}: modo demo con aviso visible', pg.evaluate('window.UAT_MODE') == 'demo' and pg.is_visible('#demoRibbon'))
        tabs = pg.evaluate("[...document.querySelectorAll('#appNav button')].filter(b => b.offsetParent).map(b => b.id)")
        for t in tabs:
            pg.click('#' + t); pg.wait_for_timeout(450)
            check(f'{role}: pestaña {t} sin desborde', pg.evaluate(no_overflow))
        if role == 'member':
            pg.click('#navLog'); pg.wait_for_timeout(300)
            pg.fill('#formRival', 'Titan Ramp'); pg.click('#btnWin'); pg.click('#btnSave'); pg.wait_for_timeout(700)
            check('member: guardar muestra el aviso con Undo', pg.is_visible('#toast') and pg.is_visible('#btnUndo'))
            pg.click('#btnUndo'); pg.wait_for_timeout(700)
            check('member: Undo responde', 'Undone' in pg.inner_text('#toastText'), pg.inner_text('#toastText'))
            pg.click('#navStats'); pg.wait_for_timeout(300); pg.click('#memberViewByRival'); pg.wait_for_timeout(200)
            pg.fill('#rivalStatsSearch', 'ken')
            check('member: buscar rival funciona', '32%' in pg.inner_text('#personalStatsList'))
        check(f'{role}: el demo no llama a ningún servidor', len(reqs) == 0, reqs)
        check(f'{role}: sin errores de consola', len(errs) == 0, errs)
        ctx.close()

    print("\n=== Sesión recordada (cerrar y abrir) ===\n")
    ctx = b.new_context(viewport={'width': 390, 'height': 844})
    pg = ctx.new_page(); errs = watch(pg)
    pg.goto(BASE); login(pg, 'Sofia'); pg.wait_for_selector('#app', state='visible')
    pg.close(); pg = ctx.new_page(); pg.goto(BASE)
    pg.wait_for_selector('#app', state='visible', timeout=5000)
    check('al volver a abrir entra solo, sin PIN', pg.is_visible('#app') and not pg.is_visible('#screenLogin'))
    pg.click('#btnAccount'); pg.click('#btnLogout'); pg.wait_for_timeout(300)
    pg.goto(BASE); pg.wait_for_timeout(800)
    check('después de Log out pide PIN otra vez', pg.is_visible('#screenLogin'))
    ctx.close()

    print("\n=== Anchos de pantalla ===\n")
    for w, h in [(320, 640), (390, 844), (768, 1024), (1280, 800), (1920, 1080)]:
        ctx = b.new_context(viewport={'width': w, 'height': h})
        pg = ctx.new_page(); pg.goto(BASE); login(pg, 'Hector'); pg.wait_for_selector('#app', state='visible'); pg.wait_for_timeout(500)
        check(f'{w}px: sin desborde horizontal', pg.evaluate(no_overflow))
        ctx.close()

    print("\n=== Modo real: puente api.js contra un /exec falso ===\n")
    EXEC = 'https://script.google.com/macros/s/FAKE/exec'
    def live_ctx(handler, timeout_ms=None):
        ctx = b.new_context(viewport={'width': 390, 'height': 844})
        extra = f", timeoutMs: {timeout_ms}" if timeout_ms else ''
        ctx.route('**/config.js', lambda r: r.fulfill(status=200, content_type='application/javascript',
                  body=f"window.UAT_CONFIG = {{ apiUrl: '{EXEC}'{extra} }};"))
        ctx.route(EXEC, handler)
        return ctx
    seen = []
    def api(route):
        req = route.request
        body = json.loads(req.post_data)
        seen.append({'method': req.method, 'ctype': req.headers.get('content-type', ''), 'body': body})
        fn, args = body['fn'], body['args']
        out = {'listNamesForLogin': ['Ana', 'Beto'],
               'login': {'ok': True, 'token': 'T1', 'name': args[0] if args else '', 'role': 'member'} if args and args[1] == '2222' else {'ok': False, 'error': 'Wrong PIN.'},
               'resumeSession': {'ok': False}}.get(fn)
        if fn == 'getMemberScreen':
            route.fulfill(status=200, content_type='application/json', body=json.dumps({'ok': False, 'error': 'Session expired. Log in again.'})); return
        if out is None:
            out = {}
        route.fulfill(status=200, content_type='application/json', body=json.dumps({'ok': True, 'result': out}))
    ctx = live_ctx(api)
    pg = ctx.new_page(); errs = watch(pg)
    pg.goto(BASE); pg.wait_for_timeout(600)
    check('modo real (sin cinta de demo)', pg.evaluate('window.UAT_MODE') == 'live' and not pg.is_visible('#demoRibbon'))
    names = pg.evaluate("[...document.querySelectorAll('#loginName option')].map(o => o.value).filter(Boolean)")
    check('la lista de nombres viene del servidor', names == ['Ana', 'Beto'], names)
    first = seen[0]
    check('pide con POST', first['method'] == 'POST')
    check('con Content-Type text/plain (sin preflight CORS)', first['ctype'].startswith('text/plain'), first['ctype'])
    check('cuerpo {fn, args, v}', first['body']['fn'] == 'listNamesForLogin' and first['body']['args'] == [] and first['body']['v'] != '', first['body'])
    pg.select_option('#loginName', 'Ana'); pg.fill('#loginPin', '9999'); pg.click('#btnLogin'); pg.wait_for_timeout(500)
    check('PIN malo: muestra el error del servidor', 'Wrong PIN.' in pg.inner_text('#loginError'), pg.inner_text('#loginError'))
    check('los argumentos llegan tal cual', seen[-1]['body']['args'] == ['Ana', '9999'], seen[-1]['body'])
    pg.fill('#loginPin', '2222'); pg.click('#btnLogin'); pg.wait_for_timeout(900)
    check('PIN bueno: entra', pg.is_visible('#app'))
    ms = [s for s in seen if s['body']['fn'] == 'getMemberScreen']
    check('pide la pantalla con el token de la sesión', ms and ms[0]['body']['args'][0] == 'T1', ms[:1])
    check('un {ok:false} del servidor llega como error a la pantalla (sin romperla)', len(errs) == 0, errs)
    stored = pg.evaluate("localStorage.getItem('uat.session.v1')")
    check('la sesión se guarda en el teléfono', stored and 'T1' in stored)
    ctx.close()

    print("\n=== Sin internet, error del servidor, demora ===\n")
    def offline(route):
        route.abort('internetdisconnected')
    ctx = live_ctx(offline); pg = ctx.new_page()
    pg.goto(BASE); pg.wait_for_timeout(800)
    pg.evaluate("google.script.run.withFailureHandler(e => window.__e = e.message).login('A', '1'); 0"); pg.wait_for_timeout(500)
    check('sin internet: mensaje claro', pg.evaluate('window.__e') == 'no internet connection. Try again.', pg.evaluate('window.__e'))
    ctx.close()
    ctx = live_ctx(lambda r: r.fulfill(status=500, body='oops')); pg = ctx.new_page()
    pg.goto(BASE); pg.wait_for_timeout(500)
    pg.evaluate("google.script.run.withFailureHandler(e => window.__e = e.message).login('A', '1'); 0"); pg.wait_for_timeout(500)
    check('error 500: lo dice', 'answered 500' in (pg.evaluate('window.__e') or ''), pg.evaluate('window.__e'))
    ctx.close()
    ctx = live_ctx(lambda r: r.fulfill(status=200, content_type='text/html', body='<html>Google sign-in</html>')); pg = ctx.new_page()
    pg.goto(BASE); pg.wait_for_timeout(500)
    pg.evaluate("google.script.run.withFailureHandler(e => window.__e = e.message).login('A', '1'); 0"); pg.wait_for_timeout(500)
    check('respuesta que no es JSON (p. ej. página de Google): error claro', 'unexpected reply' in (pg.evaluate('window.__e') or ''), pg.evaluate('window.__e'))
    ctx.close()
    import time
    def slow(route):
        time.sleep(1.2)
        try: route.fulfill(status=200, content_type='application/json', body='{"ok":true,"result":1}')
        except Exception: pass
    ctx = live_ctx(slow, timeout_ms=400); pg = ctx.new_page()
    pg.goto(BASE); pg.wait_for_timeout(1800)
    pg.evaluate("window.__s = 0; google.script.run.withSuccessHandler(() => window.__s++).withFailureHandler(e => window.__e = e.message).login('A', '1'); 0"); pg.wait_for_timeout(2000)
    check('demora: corta y avisa', pg.evaluate('window.__e') == 'the server took too long. Try again.' and pg.evaluate('window.__s') == 0, pg.evaluate('window.__e'))
    ctx.close()
    seen2 = []
    def cap(route):
        seen2.append(json.loads(route.request.post_data)); route.fulfill(status=200, content_type='application/json', body='{"ok":true,"result":null}')
    ctx = live_ctx(cap); pg = ctx.new_page()
    pg.goto(BASE); pg.wait_for_timeout(500)
    pg.evaluate("google.script.run.getMatchHistory('t', 'All', 0, 20, undefined, undefined); google.script.run.withUserObject('x').withSuccessHandler((v, u) => window.__u = u).logout('t'); 0"); pg.wait_for_timeout(500)
    gm = [s for s in seen2 if s['fn'] == 'getMatchHistory']
    check('undefined al final no viaja como null', gm and gm[0]['args'] == ['t', 'All', 0, 20], gm)
    check('withUserObject funciona como en Apps Script', pg.evaluate('window.__u') == 'x')
    ctx.close()

    print("\n=== Modo QA (?qa → la copia de prueba) ===\n")
    QA_EXEC = 'https://script.google.com/macros/s/QA/exec'
    hits = []
    def any_api(route):
        hits.append(route.request.url)
        route.fulfill(status=200, content_type='application/json', body=json.dumps({'ok': True, 'result': ['Qa']}))
    def cfg_ctx(cfg):
        ctx = b.new_context(viewport={'width': 390, 'height': 844})
        ctx.route('**/config.js', lambda r: r.fulfill(status=200, content_type='application/javascript', body='window.UAT_CONFIG = ' + json.dumps(cfg) + ';'))
        ctx.route('https://script.google.com/**', any_api)
        ctx.route('https://evil.example/**', any_api)
        return ctx
    ctx = cfg_ctx({'apiUrl': '', 'qaApiUrl': QA_EXEC}); pg = ctx.new_page()
    pg.goto(BASE); pg.wait_for_timeout(500)
    check('sin ?qa y sin apiUrl: demo', pg.evaluate('window.UAT_MODE') == 'demo')
    hits.clear(); pg.goto(BASE + '?qa'); pg.wait_for_timeout(600)
    check('con ?qa: modo qa', pg.evaluate('window.UAT_MODE') == 'qa')
    check('con su aviso azul, sin el de demo', pg.is_visible('#qaRibbon') and not pg.is_visible('#demoRibbon') and 'QA' in pg.inner_text('#qaRibbon'))
    check('llama a la copia de prueba', hits and all(h == QA_EXEC for h in hits), hits)
    ctx.close()
    ctx = cfg_ctx({'apiUrl': EXEC, 'qaApiUrl': QA_EXEC}); pg = ctx.new_page()
    hits.clear(); pg.goto(BASE); pg.wait_for_timeout(600)
    check('con las dos: sin ?qa usa la real', pg.evaluate('window.UAT_MODE') == 'live' and hits and all(h == EXEC for h in hits), hits)
    hits.clear(); pg.goto(BASE + '?qa'); pg.wait_for_timeout(600)
    check('y con ?qa la de prueba', hits and all(h == QA_EXEC for h in hits), hits)
    hits.clear(); pg.goto(BASE + '?api=https://evil.example/exec&apiUrl=https://evil.example/exec'); pg.wait_for_timeout(600)
    check('un link con ?api=otro servidor no cambia a dónde van los PINs', hits and all(h == EXEC for h in hits), hits)
    ctx.close()
    ctx = cfg_ctx({'apiUrl': EXEC, 'qaApiUrl': ''}); pg = ctx.new_page()
    hits.clear(); pg.goto(BASE + '?qa'); pg.wait_for_timeout(600)
    check('?qa sin copia de prueba configurada: usa la real (no se rompe)', pg.evaluate('window.UAT_MODE') == 'live' and all(h == EXEC for h in hits))
    ctx.close()
    b.close()
srv.shutdown()

print(f"\nPages: {sum(res)} pass, {len(res) - sum(res)} fail\n")
sys.exit(1 if not all(res) else 0)
