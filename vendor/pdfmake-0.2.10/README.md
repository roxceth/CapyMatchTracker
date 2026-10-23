# pdfmake 0.2.10 + Inter (para el reporte en PDF)

Se cargan solo al tocar "Generate PDF report" (v2.23). Se sirven desde GitHub
Pages junto a la app, sin depender de un CDN externo.

- `pdfmake.min.js`: copia sin cambios de `build/pdfmake.min.js` del tag 0.2.10 de
  https://github.com/bpampuch/pdfmake (MIT, ver `LICENSE-pdfmake.txt`).
- `vfs_inter.js`: Inter (SIL OFL 1.1, ver `LICENSE-Inter.txt`) en 5 pesos
  (Regular, Medium, SemiBold, Bold, Display Bold), recortada con `pyftsubset`
  a Latin-1 + los símbolos del reporte (· – — “ ” ▲ ▼ ● …) para que pese
  ~285 KB en vez de ~3 MB. Para agregar un carácter, regenerar así (Inter
  4.0 instalada como fonts-inter; luego base64 de cada .otf en `vfs_inter.js`):

      pyftsubset Inter-Regular.otf --layout-features='kern,tnum,liga' \
        --unicodes='U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+2013-2014,U+2018-201A,U+201C-201E,U+2022,U+2026,U+2030,U+2039-203A,U+2190-2193,U+2212,U+2264-2265,U+25B2,U+25BC,U+25CF,U+25CB,U+2713,U+00D7'

  (igual para Inter-Medium, Inter-SemiBold, Inter-Bold e InterDisplay-Bold).

No se usan los Roboto de `vfs_fonts.js` de pdfmake.
