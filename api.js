/*
 * Puente entre las pantallas y el servidor de Apps Script.
 *
 * Las pantallas se escribieron para correr dentro de Apps Script y llaman al
 * servidor con google.script.run. Aquí se crea un google.script.run igual,
 * pero que por debajo usa fetch() contra el /exec del Apps Script. Así el
 * código de las pantallas no cambia.
 *
 * Protocolo (POST, Content-Type text/plain para evitar el preflight CORS):
 *   pedido:    {"fn": "getMatchHistory", "args": [...], "v": "<build>"}
 *   respuesta: {"ok": true, "result": ...}  o  {"ok": false, "error": "..."}
 *
 * Modo demo: sin apiUrl en config.js, o con ?demo en el link, responde con
 * los datos de prueba de demo.js y no llama a ningún servidor.
 * Modo QA: con ?qa en el link, usa qaApiUrl (la copia de prueba de la hoja).
 */
(function () {
  'use strict';
  var cfg = window.UAT_CONFIG || {};
  var params = new URLSearchParams(location.search);
  // ?qa usa el Apps Script de la copia de prueba de la hoja (qaApiUrl). El
  // link sale de config.js y no del URL a propósito: un ?api=<cualquiera>
  // permitiría armar un link que mande los PINs a otro servidor.
  var qa = params.has('qa') && !!cfg.qaApiUrl;
  var apiUrl = qa ? cfg.qaApiUrl : cfg.apiUrl;
  var demo = params.has('demo') || !apiUrl;
  var TIMEOUT_MS = cfg.timeoutMs || 30000;
  window.UAT_MODE = demo ? 'demo' : (qa ? 'qa' : 'live');

  function fail(message) { return new Error(message); }

  function liveCall(fn, args) {
    // JSON convierte undefined en null; se quitan los del final para que el
    // servidor vea "parámetro ausente", igual que con google.script.run.
    while (args.length && args[args.length - 1] === undefined) args.pop();
    var ctrl = typeof AbortController === 'function' ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, TIMEOUT_MS) : null;
    return fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ fn: fn, args: args, v: (window.UAT_BUILD || {}).version || '' }),
      redirect: 'follow',
      signal: ctrl ? ctrl.signal : undefined
    }).then(function (r) {
      if (timer) clearTimeout(timer);
      if (!r.ok) throw fail('the server answered ' + r.status + '. Try again.');
      return r.json().catch(function () { throw fail('unexpected reply from the server. Try again.'); });
    }, function (e) {
      if (timer) clearTimeout(timer);
      if (e && e.name === 'AbortError') throw fail('the server took too long. Try again.');
      throw fail('no internet connection. Try again.');
    }).then(function (resp) {
      if (!resp || resp.ok !== true) throw fail((resp && resp.error) || 'unknown server error');
      return resp.result;
    });
  }

  function demoCall(fn, args) {
    return new Promise(function (resolve, reject) {
      setTimeout(function () {
        try {
          var f = (window.UAT_DEMO || {})[fn];
          if (!f) throw fail('"' + fn + '" is not available in the demo');
          resolve(f.apply(null, args));
        } catch (e) { reject(e); }
      }, cfg.demoDelayMs != null ? cfg.demoDelayMs : 250);
    });
  }

  var call = demo ? demoCall : liveCall;

  // Igual que google.script.run: cada with...() devuelve un runner nuevo, y
  // cualquier otro nombre es una función del servidor.
  function runner(st) {
    return new Proxy({}, {
      get: function (t, p) {
        if (p === 'withSuccessHandler') return function (f) { return runner(Object.assign({}, st, { s: f })); };
        if (p === 'withFailureHandler') return function (f) { return runner(Object.assign({}, st, { f: f })); };
        if (p === 'withUserObject') return function (o) { return runner(Object.assign({}, st, { u: o })); };
        if (typeof p !== 'string') return undefined;
        return function () {
          var args = Array.prototype.slice.call(arguments);
          call(p, args).then(
            function (v) { if (st.s) st.s(v, st.u); },
            function (e) { if (st.f) st.f(e, st.u); else console.error(e); }
          );
        };
      }
    });
  }

  window.google = window.google || {};
  window.google.script = window.google.script || {};
  window.google.script.run = runner({});

  if (demo || qa) {
    document.addEventListener('DOMContentLoaded', function () {
      var b = document.createElement('div');
      b.id = demo ? 'demoRibbon' : 'qaRibbon';
      b.setAttribute('role', 'status');
      b.textContent = demo ? 'DEMO · fake data · any PIN works' : 'QA · test copy of the sheet';
      b.style.cssText = 'display:block;width:max-content;max-width:100%;margin:0 auto 12px;' +
        (demo ? 'background:#e4b73f;color:#0e0d13;' : 'background:#35a7e6;color:#0e0d13;') +
        'font:600 12px/1 Inter,Arial,sans-serif;letter-spacing:.04em;padding:6px 12px;border-radius:999px;';
      document.body.insertBefore(b, document.body.firstChild);
    });
  }
})();
