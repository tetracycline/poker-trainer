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
  const sec=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];const acts={};
  for(const m of sec.matchAll(/<tr data-cl="[^"]*" id="([^"]+)">([\s\S]*?)<\/tr>/g)){
    const tx=m[1].slice(id.length+1);
    for(const [i,c] of [...m[2].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()){
      if(!model.allowed.includes(tx+':'+i))continue;
      acts[tx+':'+i]=c[1].replace(/<[^>]+>/g,'').split(' APPROX')[0].replace(/≈/g,'');
    }
  }
  routes[rank]=acts;
}
assert.deepEqual(routes,{
  '15':{'A_high:0':'下注 ½','A_high:3':'過'},
  '16':{'mid_high:0':'下注 ½','KQ_high:0':'下注 ½','KQ_high:3':'過','paired:3':'過'}
});
console.log(JSON.stringify(routes));