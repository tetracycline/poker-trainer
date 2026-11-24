const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const c = {console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null}};
c.window = c;
vm.createContext(c);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js'])
  vm.runInContext(fs.readFileSync(file, 'utf8'), c, {filename: file});

c.__linesQA.render('bb');
const id='ln-bb-t_model-jenhr8',start='ln-bb-f_first-1qu5u1x',facing='ln-bb-f_vs_cbet-cdkvuf';
const model=c.__HU_MODEL_LAST.nodes.find(n=>n.id===id);
assert.equal(model.source,facing);assert.equal(model.facts.root.spot,'BTN_BB');assert.equal(model.key,'你過、對手下注、你加注、對手跟|');
const sec=n=>app.innerHTML.split('id="'+n+'">')[1].split('<div class="sec"')[0];
assert(sec(facing).split('<table')[0].includes('BTN 下注 75%（4.1bb），你要跟 4.1bb（底池 9.6bb）'));
const cells=(n,t)=>[...sec(n).split('id="'+n+'-'+t+'">')[1].split('</tr>')[0].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
const first=h=>h.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);
const route={flop:{},turn:{}};
for(const t of ['low','mid_high','KQ_high','A_high','paired','mono']){
 let [x,r,next]=[start,facing,id].map(n=>cells(n,t));
 for(let i=0;i<5;i++){
  const key=t+':'+i;
  if(first(x[i])?.[2]==='過' && x[i].includes('class="jmp sub" href="#'+facing+'-'+t+'"') &&
      first(r[i])?.[1]===id+'-'+t && first(r[i])?.[2].replace(/≈$/,'')==='加注')route.flop[key]='加注';
  if(model.allowed.includes(key)) route.turn[key]=next[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
 }
}
assert.deepEqual(Object.keys(route.flop).sort(), Array.from(model.allowed).sort());
assert.deepEqual(Object.keys(route.turn).sort(), Object.keys(route.flop).sort());
assert.deepEqual([model.facts.root.pot,model.facts.root.stack,model.facts.spr],[5.5,97.5,2.887]);
console.log(JSON.stringify({id, start, facing, actor:0, model_spr:model.facts.spr, route}));