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
context.__linesQA.render('opfr');
const byId = new Map(context.__HU_MODEL_LAST.nodes.map(m=>[m.id,m]));
const targets = {15:'ln-opfr-r_model-1bv0680',16:'ln-opfr-r_model-j55znd'};
const routes = {};
for (const [rank,id] of Object.entries(targets)) {
  const model=byId.get(id), turn=byId.get(model.source);
  assert.equal(model.key,'你下注、對手跟|你下注、對手跟|');
  function verifiedCells(target, from, label) {
    const section = app.innerHTML.split('id="' + from + '"')[1].split('<div class="sec"')[0];
    const mapped=new Set();
    for(const row of section.matchAll(/<tr data-cl="[^"]*" id="([^"]+)">([\s\S]*?)<\/tr>/g)){
      const texture=row[1].slice(from.length+1);
      for(const [i,c] of [...row[2].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()){
        for(const l of c[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)){
          if(l[1]!==target.id+'-'+texture)continue;
          assert.equal(l[2].replace(/≈$/, ''),label);
          mapped.add(texture+':'+i);
        }
      }
    }
    assert.deepEqual([...mapped].sort(), [...target.allowed].sort());
    return [...mapped].sort();
  }
  routes[rank]=[verifiedCells(turn,turn.source,rank==='15'?'下注 ¾':'下注 1'),verifiedCells(model,turn.id,'下注 ½')];
}
console.log(JSON.stringify(routes));
