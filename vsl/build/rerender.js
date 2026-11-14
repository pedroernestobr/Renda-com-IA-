const { chromium } = require('playwright');
const FPS = 30;
(async () => {
  const [out, a, z] = [process.argv[2], +process.argv[3], +process.argv[4]];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + __dirname + '/vsl.html');
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(1000);
  for (let f = Math.round(a * FPS); f <= Math.round(z * FPS); f++) {
    await p.evaluate(t => render(t), f / FPS);
    await p.screenshot({ path: `${out}/${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 92 });
  }
  await b.close();
})();
