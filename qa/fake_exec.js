// Servidor local que imita el /exec de Apps Script para la prueba de punta
// a punta: corre el Code.gs real (del repo privado) sobre el mock de Sheets
// del QA privado y responde con su doPost. Agrega el mismo encabezado CORS
// que pone Apps Script en las respuestas de ContentService.
//
//   node qa/fake_exec.js <ruta/repo-privado> <puerto>
const path = require('path');
const http = require('http');
const [repo, port] = process.argv.slice(2);
process.chdir(path.join(repo, 'qa_suite'));
require(path.resolve('mock_gas.js'));
eval(require('fs').readFileSync('../Code.gs', 'utf8'));
const H = ['ID', 'Date', 'Player', 'Own Deck', 'Rival Deck', 'Result', 'Turn', 'Rival Name', 'Own Brick', 'Rival Brick'];
const today = new Date();
__initSheets({
  Members: [['Name', 'PIN', 'Role', 'Active'], ['Hector', '1234', 'admin', true], ['Ana', '0222', 'member', true], ['Luis', '3333', 'manager', true]],
  Decks: [['Name', 'Anime', 'Color', 'Type'], ['Reze Chainsawman Purple', 'CSM', 'Purple', 'Own'], ['Titan Ramp', '', '', 'Rival']],
  Rivals: [['Name'], ['Kenji']],
  Matches: [H, ['m1', today, 'Ana', 'Reze Chainsawman Purple', 'Titan Ramp', 'Win', 'First', 'Kenji', '', '']],
});
http.createServer((req, res) => {
  let body = '';
  req.on('data', c => { body += c; });
  req.on('end', () => {
    const headers = { 'Access-Control-Allow-Origin': '*' };
    if (req.method !== 'POST') { res.writeHead(405, headers); res.end(); return; }
    global.__lastCT = req.headers['content-type'];
    const out = doPost({ postData: { contents: body } });
    res.writeHead(200, Object.assign(headers, { 'Content-Type': out.mime }));
    res.end(out.getContent());
  });
}).listen(Number(port), '127.0.0.1', () => console.log('fake exec on ' + port));
