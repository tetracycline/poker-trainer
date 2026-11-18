#!/usr/bin/env node
// HU-only NL2 contract audit. Reads the same data and renderer as the site.
// This is a structural audit, NOT a claim that absent solver nodes are solved.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const ctx = {
  console, __LINES_QA: true, location: {hash:'#lines'},
  scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll:()=>[], getElementById:()=>null}
};
ctx.window = ctx;
vm.createContext(ctx);
for (const name of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2.js']) {
  vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),ctx,{filename:name});
}
if (!ctx.__linesQA || !ctx.NLL) throw new Error('NL2 renderer/data unavailable');
const EXPECT = ['頂對好','頂對弱','中小對','強聽','弱聽'];
const ROWS = ['9 以下低牌面','J/T 高面','K/Q 高面','A 高面','成對面','單色面'];
const errors = [];
const stats = {spots:0,tables:0,huRows:ctx.NLL.rows.length,missingNextCells:0,nonFoldCells:0,bySpot:[]};
if (ctx.NLL.spots.some(s => s.id === 'mw')) errors.push('multiway spot is still present');
if (ctx.NLL.rows.some(r => r.sp === 'mw' || (r.eg || []).some(e=>e.mw)))
  errors.push('multiway rows/examples are still present');
const clean = s => String(s).replace(/<[^>]*>/g,'').replace(/\s+/g,' ').trim();
for (const spot of ctx.NLL.spots) {
  stats.spots++;
  ctx.__linesQA.render(spot.id);
  const html = app.innerHTML;
  const tables = [...html.matchAll(/<table class="rt lt">([\s\S]*?)<\/table>/g)];
  let tc = 0;
  for (const match of tables) {
    const markup=match[1];
    const header=markup.match(/<tr><th><\/th>([\s\S]*?)<\/tr>/);
    if (!header) {errors.push(spot.id+': missing five-column header');continue;}
    const actual=[...header[1].matchAll(/<th>([\s\S]*?)<\/th>/g)].map(m=>clean(m[1]));
    if (JSON.stringify(actual)!==JSON.stringify(EXPECT))
      errors.push(spot.id+': columns '+JSON.stringify(actual));
    const actualRows=[...markup.matchAll(/<th class="cl">([\s\S]*?)<\/th>/g)].map(m=>clean(m[1]));
    if (JSON.stringify(actualRows)!==JSON.stringify(ROWS))
      errors.push(spot.id+': expected six rows, got '+JSON.stringify(actualRows));
    stats.tables++; tc++;
    for (const td of markup.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)) {
      const txt=clean(td[1]);
      if (txt==='—' || /^棄|^全下|^加注 全下/.test(txt)) continue;
      stats.nonFoldCells++;
      if (txt.includes('待解：缺下一街')) stats.missingNextCells++;
    }
  }
  stats.bySpot.push({id:spot.id,tables:tc});
}
if (!stats.tables) errors.push('no rendered tables');
console.log(JSON.stringify({stats,errors},null,2));
if (errors.length) process.exitCode=1;
