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
context.__linesQA.render('opfr');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const parent = nodes.get('ln-opfr-t_model-trdt3w');
const routes = {};
for (const [rank,id,label] of [[17,'ln-opfr-r_model-j5b75a','下注 ⅓'],[18,'ln-opfr-r_model-ka3vbv','下注 ¾']]) {
  const river = nodes.get(id);
  assert.equal(river.source,parent.id);
  assert.equal(parent.facts.root.spot,'SB_BB');
  assert.equal(parent.facts.pot,12);
  for (const [node,expected] of [[parent,'下注 ½'],[river,label]]) {
    const section = app.innerHTML.split('id="'+node.source+'"')[1].split('<div class="sec"')[0];
    const rendered = [];
    for (const texture of ['A_high','KQ_high','mid_high','low','paired','mono']) {
      const row = section.match(new RegExp('<tr[^>]+id="'+node.source+'-'+texture+'">([\\s\\S]*?)</tr>'));
      for (const [column,cell] of [...(row?.[1] || '').matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()) {
        const links = [...cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)];
        const relevant = links.filter(m=>m[1]===node.id+'-'+texture);
        if (relevant.length) {
          assert.ok(relevant.every(m=>m[2].replace(/≈$/,'')===expected));
          rendered.push(texture+':'+column);
        }
      }
    }
    assert.deepEqual(rendered.sort(),Array.from(node.allowed).sort());
  }
  routes[rank] = {model:id,flop:parent.allowed,turn:river.allowed};
}
process.stdout.write(JSON.stringify(routes));
