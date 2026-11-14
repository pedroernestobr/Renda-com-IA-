const { chromium } = require('playwright');
(async () => {
  const ts = process.argv.slice(3).map(Number);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + __dirname + '/vsl.html');
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(800);
  for (const t of ts) { await p.evaluate(t => render(t), t); await p.screenshot({ path: `${process.argv[2]}/f_${t}.jpg`, type: 'jpeg', quality: 70 }); }
  await b.close();
})();
