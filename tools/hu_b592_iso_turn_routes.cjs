const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const context = {
  console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null}
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file,'utf8'), context, {filename: file});
}
const rank=process.argv[2] || '124';
const config={
  67:{section:'iso',id:'ln-iso-iso_t_model-q429lu',pot:9.5,stack:96,label:'跟'},
  124:{section:'iso', id:'ln-iso-t_model-1gjwm8f',pot:9.5,stack:96,label:'下注 ½'},
  133:{section:'ipc', id:'ln-ipc-t_model-day18r',pot:6.5,stack:97.5,label:'下注 1'},
  198:{section:'3bp', id:'ln-3bp-3b_t_model-wsml7c',pot:16.5,stack:92.5,label:'過'}
}[rank];
assert.ok(config,'unknown turn study');
context.__linesQA.render(config.section);
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
// Keep the exact parent action and the visible turn classes for this model.
const targets = {[rank]:config.id};
const classes = ['TPG','TPW','MID','DRAW','WDRAW'];
function cells(id, texture) {
  const section = app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  const row = section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'))[1];
  return [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
}
const out = {};
for (const [rank,id] of Object.entries(targets)) {
  const model=nodes.get(id);
  assert.deepEqual([model.facts.root.pot,model.facts.root.stack],[config.pot,config.stack]);
  const route={};
  for (const texture of new Set(model.allowed.map(x=>x.split(':')[0]))) {
    const prior=cells(model.source,texture);
    const current=cells(id,texture);
    const parents=[], decisions={};
    for (const [i,name] of classes.entries()) {
      const links=[...prior[i].matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/g)];
      if (links.some(m=>m[1]===id+'-'+texture && m[2].replace(/≈$/,'')===config.label)) parents.push(name);
      if (model.allowed.includes(texture+':'+i)) {
        const label=current[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
        assert.ok(label && label!=='—');
        decisions[name]=label;
      }
    }
    route[texture]={parents, decisions};
  }
  out[rank]=route;
}
console.log(JSON.stringify(out));
