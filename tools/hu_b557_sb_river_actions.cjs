// Verify the primary action in every playable rank17/18 river cell.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = {innerHTML:'', querySelectorAll:()=>[], addEventListener(){}};
const ctx = {console, __LINES_QA:true, location:{hash:'#lines'}, scrollTo(){}, addEventListener(){},
  document:{querySelector:()=>app, querySelectorAll:()=>[], getElementById:()=>null}};
ctx.window = ctx;
vm.createContext(ctx);
for (const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js']) {
  vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
}
ctx.__linesQA.render('opfr');
const output = {};
for (const [rank,id] of [[17,'ln-opfr-r_model-j5b75a'],[18,'ln-opfr-r_model-ka3vbv']]) {
  const model = ctx.__HU_MODEL_LAST.nodes.find(n=>n.id===id);
  const section = app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  const actions = {};
  for (const texture of ['low','mid_high','KQ_high','A_high','paired','mono']) {
    const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
    assert.ok(row);
    for (const [i,cell] of [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()) {
      const primary=cell[1].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
      if (primary==='—') continue;
      const token={'過':'x','下注 ¾':'b75'}[primary];
      assert.ok(token,primary);
      actions[texture+':'+i]=token;
    }
  }
  assert.deepEqual(Object.keys(actions).sort(),Array.from(model.allowed).sort());
  output[rank]=actions;
}
console.log(JSON.stringify(output));
