// Read the live primary links for both sizes and all three model tables.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = {innerHTML:'', querySelectorAll:()=>[], addEventListener(){}};
const context = {console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
  document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
context.window = context;
vm.createContext(context);
for (const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js']) {
  vm.runInContext(fs.readFileSync(f,'utf8'),context,{filename:f});
}
context.__linesQA.render('ipc');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const parent = nodes.get('ln-ipc-t_model-188b2d5');
const routes = {};
for (const [rank,id,label] of [[188,'ln-ipc-r_model-1s0a4ds','下注 ½'],[191,'ln-ipc-r_model-i19djk','下注 ⅓']]) {
  const river = nodes.get(id);
  assert.equal(river.source,parent.id);
  assert.equal(parent.facts.root.spot,'SB_BB');
  assert.equal(parent.facts.pot,18);
  for (const [node,expected] of [[parent,'下注 1'],[river,label]]) {
    const section = app.innerHTML.split('id="'+node.source+'"')[1].split('<div class="sec"')[0];
    const targets = [...section.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)].filter(m=>m[1].startsWith(node.id+'-'));
    assert.deepEqual([...new Set(targets.map(m=>m[2]))],[expected]);
  }
  routes[rank] = {model:id,flop:parent.allowed,turn:river.allowed};
}
process.stdout.write(JSON.stringify(routes));
