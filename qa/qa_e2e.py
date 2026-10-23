"""Prueba de punta a punta: la página publicada + el Code.gs real.

Levanta la página (como GitHub Pages) y un /exec falso que corre el Code.gs
del repo privado con su doPost. El navegador habla con él igual que hablará
con Apps Script: otro origen, POST text/plain, sin preflight CORS (el /exec
falso rechaza OPTIONS, así que un preflight haría fallar todo).

    python3 qa/qa_e2e.py <ruta/al/repo privado>
"""
import http.server, os, socketserver, subprocess, sys, threading, time
from functools import partial
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '..', 'uamatchtracker'))

res = []
def check(desc, cond, detail=''):
    res.append(bool(cond))
    print(('  PASS  ' if cond else '  FAIL  ') + desc + (('  -> ' + str(detail)) if detail != '' and not cond else ''))

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
# Copia de la página con config.js apuntando al /exec falso. (No se usa
# page.route: con intercepción activa Playwright contesta él mismo los
# preflight CORS y la prueba dejaría de detectarlos.)
import shutil, tempfile
SITE = tempfile.mkdtemp(prefix='capy_e2e_')
for f in ['index.html', 'api.js', 'demo.js', 'manifest.webmanifest']:
    shutil.copy(os.path.join(ROOT, f), SITE)
shutil.copytree(os.path.join(ROOT, 'icons'), os.path.join(SITE, 'icons'))
srv = socketserver.TCPServer(('127.0.0.1', 0), partial(Quiet, directory=SITE))
PAGE = f'http://127.0.0.1:{srv.server_address[1]}/'
threading.Thread(target=srv.serve_forever, daemon=True).start()
API_PORT = 18000 + os.getpid() % 1000
api = subprocess.Popen(['node', os.path.join(ROOT, 'qa', 'fake_exec.js'), REPO, str(API_PORT)], stdout=subprocess.PIPE, text=True)
api.stdout.readline()
EXEC = f'http://127.0.0.1:{API_PORT}/exec'
open(os.path.join(SITE, 'config.js'), 'w').write(f"window.UAT_CONFIG = {{ apiUrl: '{EXEC}' }};")

def page(b):
    ctx = b.new_context(viewport={'width': 390, 'height': 844})
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_TUNNEL_CONNECTION_FAILED' not in m.text else None)
    pre = []
    pg.on('request', lambda r: pre.append(r.url) if r.method == 'OPTIONS' else None)
    pg.goto(PAGE)
    pg.wait_for_function("document.querySelector('#loginName').options.length > 1", timeout=8000)
    return ctx, pg, errs, pre

def login(pg, name, pin):
    pg.select_option('#loginName', name); pg.fill('#loginPin', pin); pg.click('#btnLogin')

try:
    with sync_playwright() as p:
        b = p.chromium.launch()

        print("\n=== Miembro: entrar, registrar, ver, deshacer ===\n")
        ctx, pg, errs, pre = page(b)
        names = pg.evaluate("[...document.querySelectorAll('#loginName option')].map(o => o.value).filter(Boolean)")
        check('los nombres vienen de la hoja (vía doPost)', names == ['Hector', 'Ana', 'Luis'], names)
        login(pg, 'Ana', '0222'); pg.wait_for_selector('#app', state='visible', timeout=8000)
        check('Ana entra con su PIN (con cero adelante)', pg.is_visible('#app'))
        pg.wait_for_timeout(800)
        check('el mazo de la última partida queda elegido', 'Reze Chainsawman Purple' in pg.inner_text('#deckPicker'))
        pg.fill('#formRival', 'Hunter Rush'); pg.click('#rivalAssist [data-add]')     # v2.18: nuevo a propósito
        pg.fill('#formRivalName', 'Lulu'); pg.click('#nameAssist [data-add]')
        pg.click('#btnLoss'); pg.click('#btnSave')
        pg.wait_for_selector('#btnUndo', state='visible', timeout=8000)
        check('guardar responde con Undo', 'Saved' in pg.inner_text('#toastText'), pg.inner_text('#toastText'))
        pg.click('#navHistory'); pg.wait_for_timeout(1200)
        hist = pg.inner_text('#historyList')
        check('la partida nueva sale en History', 'Hunter Rush' in hist and 'Lulu' in hist, hist[:200])
        pg.click('#navStats'); pg.wait_for_timeout(1000)
        check('las stats la cuentan (1 de 2)', '50%' in pg.inner_text('#viewStats'), pg.inner_text('#viewStats')[:200])
        pg.click('#navLog'); pg.wait_for_timeout(300)
        pg.fill('#formRival', 'Titan Ramp'); pg.click('#btnWin'); pg.click('#btnSave')
        pg.wait_for_selector('#btnUndo', state='visible', timeout=8000); pg.wait_for_timeout(200)
        pg.click('#btnUndo'); pg.wait_for_timeout(1500)
        check('Undo se hace en el servidor', 'Undone' in pg.inner_text('#toastText'), pg.inner_text('#toastText'))
        pg.click('#navHistory'); pg.wait_for_timeout(1200)
        check('y la partida deshecha ya no está', pg.evaluate("document.querySelectorAll('#historyList .hist-row').length") == 2)
        pg.click('#historyList .hist-row [data-action="menu"]'); pg.click('#sheetBody [data-action="delete"]')
        pg.wait_for_selector('#btnUndo', state='visible', timeout=8000); pg.wait_for_timeout(1200)
        check('borrar (v2.18) quita la partida y ofrece Undo', pg.evaluate("document.querySelectorAll('#historyList .hist-row').length") == 1 and 'Match deleted' in pg.inner_text('#toastText'))
        pg.click('#btnUndo'); pg.wait_for_timeout(1800)
        check('Undo la restaura en el servidor', 'Restored' in pg.inner_text('#toastText') and pg.evaluate("document.querySelectorAll('#historyList .hist-row').length") == 2, pg.inner_text('#toastText'))
        pg.reload(); pg.wait_for_selector('#app', state='visible', timeout=8000)
        check('al recargar entra solo (resumeSession por la API)', pg.is_visible('#app'))
        check('sin preflight CORS', len(pre) == 0, pre)
        check('sin errores de consola', len(errs) == 0, errs)
        ctx.close()

        print("\n=== Admin y manager ===\n")
        ctx, pg, errs, pre = page(b)
        login(pg, 'Hector', '1234'); pg.wait_for_selector('#app', state='visible', timeout=8000); pg.wait_for_timeout(1200)
        check('admin ve el tablero del equipo', 'TEAM DASHBOARD' in pg.inner_text('#appMain').upper())
        pg.click('#navMembers'); pg.wait_for_timeout(1200)
        check('admin ve Members', 'Ana' in pg.inner_text('#appMain'))
        # v2.19.1: editar color y serie de un mazo se guarda en la hoja y se ve al reabrir.
        pg.click('#navCatalogs'); pg.wait_for_timeout(1200)
        pg.fill('#deckSearch', 'Titan'); pg.wait_for_timeout(300)
        pg.click('#deckEditList .cat-open'); pg.wait_for_timeout(300)
        pg.select_option('#deckEditList .de-color', 'Green'); pg.fill('#deckEditList .de-anime', 'AOT')
        pg.click('#deckEditList .de-save'); pg.wait_for_timeout(1500)
        cat = pg.evaluate(f"""fetch('{EXEC}', {{method:'POST', body: JSON.stringify({{fn:'getDeckCatalog', args:[JSON.parse(localStorage.getItem('uat.session.v1')).token]}})}}).then(r => r.json())""")
        t = [d for d in cat['result'] if d['name'] == 'Titan Ramp'][0]
        check('editar color y serie de un mazo queda en la hoja', t['color'] == 'Green' and t['anime'] == 'AOT', t)
        pg.click('#deckEditList .cat-open'); pg.wait_for_timeout(300)
        check('y al reabrir el editor muestra lo guardado', pg.input_value('#deckEditList .de-color') == 'Green' and pg.input_value('#deckEditList .de-anime') == 'AOT')
        check('sin errores (admin)', len(errs) == 0, errs)
        ctx.close()
        ctx, pg, errs, pre = page(b)
        login(pg, 'Luis', '3333'); pg.wait_for_selector('#app', state='visible', timeout=8000); pg.wait_for_timeout(1000)
        check('manager no tiene Members', not pg.is_visible('#navMembers'))
        r = pg.evaluate(f"""fetch('{EXEC}', {{method:'POST', headers:{{'Content-Type':'text/plain'}},
            body: JSON.stringify({{fn:'listMembersAdmin', args:[JSON.parse(localStorage.getItem('uat.session.v1')).token]}})}}).then(r => r.json())""")
        check('y aunque llame directo a la API, el servidor lo niega', r['ok'] is False and 'permission' in r['error'].lower(), r)
        r = pg.evaluate(f"fetch('{EXEC}', {{method:'POST', body: JSON.stringify({{fn:'sheet_', args:['Members']}})}}).then(r => r.json())")
        check('las funciones internas no se pueden llamar', r == {'ok': False, 'error': 'Bad request.', 'v': '2.18'}, r)
        ctx.close()

        print("\n=== Bloqueo de PIN desde la página ===\n")
        ctx, pg, errs, pre = page(b)
        for i in range(4):
            login(pg, 'Luis', '0000'); pg.wait_for_timeout(500)
        check('4 malos: "Incorrect PIN."', pg.inner_text('#loginError') == 'Incorrect PIN.', pg.inner_text('#loginError'))
        login(pg, 'Luis', '0000'); pg.wait_for_timeout(500)
        msg = pg.inner_text('#loginError')
        check('el 5º muestra el bloqueo', 'Too many wrong PINs' in msg and '15 minutes' in msg, msg)
        login(pg, 'Luis', '3333'); pg.wait_for_timeout(500)
        check('y ni el PIN bueno entra', not pg.is_visible('#app') and 'Too many wrong PINs' in pg.inner_text('#loginError'))
        login(pg, 'Ana', '0222'); pg.wait_for_selector('#app', state='visible', timeout=8000)
        check('otro miembro entra normal', pg.is_visible('#app'))
        ctx.close()

        print("\n=== El admin lo desbloquea desde Members ===\n")
        def admin_members():
            ctx, pg, errs, pre = page(b)
            login(pg, 'Hector', '1234'); pg.wait_for_selector('#app', state='visible', timeout=8000); pg.wait_for_timeout(800)
            pg.click('#navMembers'); pg.wait_for_timeout(1200)
            return ctx, pg, errs
        ctx, pg, errs = admin_members()
        row = pg.locator('.member-row', has_text='Luis')
        check('Members muestra a Luis "Locked · 15 min"', 'Locked · 15 min' in row.inner_text(), row.inner_text())
        row.locator('[data-edit]').click(); pg.wait_for_timeout(300)
        check('al abrirlo explica el bloqueo y ofrece "Unlock now"', pg.is_visible('#mLockBox') and pg.is_visible('#mUnlock'))
        pg.click('#mUnlock'); pg.wait_for_timeout(1500)
        check('al desbloquear avisa', 'Luis can log in again' in pg.inner_text('#toastText'), pg.inner_text('#toastText'))
        check('y la lista ya no lo marca', 'Locked' not in pg.locator('.member-row', has_text='Luis').inner_text())
        check('sin errores (desbloqueo)', len(errs) == 0, errs)
        ctx.close()
        ctx, pg, errs, pre = page(b)
        login(pg, 'Luis', '3333'); pg.wait_for_selector('#app', state='visible', timeout=8000)
        check('Luis entra con su MISMO PIN', pg.is_visible('#app'))
        ctx.close()

        print("\n=== O le pone un PIN nuevo ===\n")
        ctx, pg, errs, pre = page(b)
        for i in range(5):
            login(pg, 'Luis', '0000'); pg.wait_for_timeout(450)
        check('Luis bloqueado otra vez', 'Too many wrong PINs' in pg.inner_text('#loginError'))
        ctx.close()
        ctx, pg, errs = admin_members()
        pg.locator('.member-row', has_text='Luis').locator('[data-edit]').click(); pg.wait_for_timeout(300)
        pg.fill('#mPin', '7777'); pg.click('#mSave'); pg.wait_for_timeout(1500)
        check('guardar el PIN nuevo avisa', 'PIN updated for Luis' in pg.inner_text('#toastText'), pg.inner_text('#toastText'))
        ctx.close()
        ctx, pg, errs, pre = page(b)
        login(pg, 'Luis', '7777'); pg.wait_for_selector('#app', state='visible', timeout=8000)
        check('Luis entra con el PIN nuevo', pg.is_visible('#app'))
        ctx.close()
        b.close()
finally:
    api.terminate()
    srv.shutdown()
    shutil.rmtree(SITE, ignore_errors=True)

print(f"\nPunta a punta: {sum(res)} pass, {len(res) - sum(res)} fail\n")
sys.exit(0 if all(res) else 1)
