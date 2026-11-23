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
const nodes=new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const turn=nodes.get('ln-opfr-t_model-19umlco');
const river=nodes.get('ln-opfr-r_model-8w3cpr');
assert.equal(turn.source,'ln-opfr-f_vs_donk-1cci9ku');
assert.equal(river.source,turn.id);
assert.equal(turn.facts.root.spot,'UTG_CO');
assert.equal(turn.key,'你過、對手下注、你跟|');
assert.equal(river.key,'你過、對手下注、你跟|你過、對手過|');
const result={};
for(const [rank,model,action] of [[68,turn,'跟'],[205,river,'過']]){
  const section=app.innerHTML.split('id="'+model.source+'"')[1].split('<div class="sec"')[0];
  const allowed=[];
  for(const [,id,row] of section.matchAll(/<tr data-cl="[^"]+" id="([^"]+)">([\s\S]*?)<\/tr>/g)) {
    const type=id.replace(model.source+'-','');
    for(const [col,cell] of [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()){
      for(const [,href,text] of cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)){
        if(!href.startsWith(model.id+'-'))continue;
        assert.equal(href,model.id+'-'+type);
        assert.equal(text.replace(/≈$/,''),action);
        allowed.push(type+':'+col);
      }
    }
  }
  assert.deepEqual(allowed.sort(),Array.from(model.allowed).sort());
  assert.ok(allowed.length>0);
  result[rank]={model:model.id,allowed};
}
process.stdout.write(JSON.stringify(result));
