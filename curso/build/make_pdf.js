// Gera um PDF por aula (resumo, passos, materiais, tarefa e checklist) na identidade do Renda com IA.
// Uso: node make_pdf.js [N ...]   (sem argumentos gera as 6)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const LOGO = '<svg viewBox="0 0 415 350"><path fill="#fff" d="M62 2h238c72 0 113 58 113 128 0 66-47 117-110 122l69 96H265l-85-120 28-56h82c24 0 40-20 40-42 0-24-16-44-40-44H120z"/><path fill="#b6f23e" stroke="#b6f23e" stroke-width="18" stroke-linejoin="round" d="M106 133h74L88 321H16z"/></svg>';
const CK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
const slug = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');

const css = `
@page{size:A4;margin:14mm 14mm 16mm;background:#060806}
*{box-sizing:border-box;margin:0;padding:0}
html{background:#060806;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font:400 11pt/1.55 "Inter Tight",system-ui,sans-serif;color:#eef2ea}
.top{display:flex;align-items:center;gap:10px;font:700 10pt/1 "Inter Tight";letter-spacing:.09em;color:#c3cbbf}
.top svg{width:26px}.top b{margin-left:auto;color:#101800;background:#b6f23e;border-radius:99px;padding:6px 13px;letter-spacing:.04em}
h1{font:800 29pt/1.04 "Plus Jakarta Sans","Inter Tight";letter-spacing:-.035em;margin-top:20px}
h1 em{font-style:normal;color:#b6f23e}
.sub{margin-top:8px;font-size:12pt;color:#c3cbbf}
.intro{margin-top:14px;padding:12px 16px;border-left:3px solid #b6f23e;background:rgba(182,242,62,.07);border-radius:0 12px 12px 0;color:#dfe6da}
h2{font:800 14pt/1.1 "Plus Jakarta Sans","Inter Tight";letter-spacing:-.02em;margin:22px 0 9px;color:#fff}
h2 i{font-style:normal;color:#b6f23e}
.card{border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);border-radius:14px;padding:12px 16px;margin-bottom:10px;break-inside:avoid}
.card h3{font:800 11.5pt/1.2 "Plus Jakarta Sans","Inter Tight";margin-bottom:6px}
ul{list-style:none}
li{position:relative;padding:3px 0 3px 24px}
li svg{position:absolute;left:0;top:6px;width:15px;height:15px;padding:2px;border-radius:50%;background:#b6f23e;color:#101800}
pre{white-space:pre-wrap;font:500 9.6pt/1.5 "JetBrains Mono",monospace;color:#eef2ea;background:#070a07;border:1px solid rgba(182,242,62,.3);border-radius:10px;padding:11px 13px}
.task{margin-top:6px;padding:14px 16px;border-radius:14px;background:linear-gradient(180deg,#dcff7d,#b6f23e);color:#101800;break-inside:avoid}
.task b{font:800 11pt "Plus Jakarta Sans"}.task p{margin-top:3px;font-weight:500}
.chk li{padding-left:28px}.chk li:before{content:"";position:absolute;left:0;top:5px;width:15px;height:15px;border:1.6px solid #b6f23e;border-radius:4px}
.aviso{margin-top:22px;padding-top:10px;border-top:1px solid rgba(255,255,255,.12);font-size:8.5pt;line-height:1.45;color:#8e998b}
.foot{margin-top:8px;font-size:8.5pt;color:#8e998b}
`;

function html(L) {
  const P = L.pdf, n = String(L.n).padStart(2, '0');
  const list = a => `<ul>${a.map(x => `<li>${CK}${esc(x)}</li>`).join('')}</ul>`;
  return `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>${css}</style></head><body>
<div class="top">${LOGO}<span>RENDA COM IA</span><b>AULA ${n}</b></div>
<h1>${esc(L.titulo)}</h1><p class="sub">${esc(L.sub)}</p>
<div class="intro">${esc(P.intro)}</div>
<h2><i>01</i> Resumo da aula</h2><div class="card">${list(P.resumo)}</div>
${P.blocos.map((b, i) => `<div class="card"><h3>${esc(b.h)}</h3>${list(b.items)}</div>`).join('')}
<h2><i>02</i> Modelos e materiais</h2>
${P.materiais.map(m => `<div class="card"><h3>${esc(m.h)}</h3><pre>${esc(m.texto)}</pre></div>`).join('')}
<h2><i>03</i> Tarefa da aula</h2><div class="task"><b>Para fazer agora</b><p>${esc(P.tarefa)}</p></div>
<h2><i>04</i> Checklist</h2><div class="card chk"><ul>${P.checklist.map(x => `<li>${esc(x)}</li>`).join('')}</ul></div>
<p class="aviso">${esc(P.aviso)}</p>
<p class="foot">Renda com IA · Aula ${n}: ${esc(L.titulo)}</p>
</body></html>`;
}

(async () => {
  const nums = process.argv.length > 2 ? process.argv.slice(2).map(Number) : [1, 2, 3, 4, 5, 6];
  const out = path.join(ROOT, 'pdf'); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage();
  for (const n of nums) {
    const L = JSON.parse(fs.readFileSync(path.join(ROOT, 'conteudo', `aula-0${n}.json`), 'utf8'));
    const tmp = path.join(out, `.tmp-${n}.html`); fs.writeFileSync(tmp, html(L));
    await p.goto('file://' + tmp); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
    const f = path.join(out, `Aula-0${n}-${slug(L.titulo)}.pdf`);
    await p.pdf({ path: f, format: 'A4', printBackground: true, preferCSSPageSize: true });
    fs.unlinkSync(tmp); console.log('ok', path.basename(f));
  }
  await b.close();
})();
