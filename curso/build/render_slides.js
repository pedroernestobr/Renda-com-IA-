// Renderiza cada slide (e cada estado de revelação) em PNG 1280x720.
// Uso: node render_slides.js N   -> curso/out/aula-0N/s{slide}_{estado}.png + manifest.json
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const n = process.argv[2];
  const L = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'conteudo', `aula-0${n}.json`), 'utf8'));
  const out = path.join(__dirname, '..', 'out', `aula-0${n}`);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.goto('file://' + path.join(__dirname, 'slide.html'));
  await p.evaluate(() => document.fonts.ready);
  const manifest = [];
  for (let i = 0; i < L.slides.length; i++) {
    const k = await p.evaluate(sl => states(sl), L.slides[i]);
    manifest.push(k);
    for (let s = 0; s < k; s++) {
      await p.evaluate(([l, sl, st]) => draw(l, sl, st), [L, L.slides[i], s]);
      await p.waitForTimeout(40);
      await p.screenshot({ path: path.join(out, `s${String(i).padStart(2, '0')}_${s}.png`) });
    }
  }
  fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(manifest));
  await b.close();
  console.log('slides', L.slides.length, 'imagens', manifest.reduce((a, c) => a + c, 0));
})();
