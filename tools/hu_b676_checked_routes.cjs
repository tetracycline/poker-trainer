const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = {innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const ctx = {console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
  document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
  vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
ctx.__linesQA.render('3bp');
const nodes=new Map(ctx.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const catalog=ctx.__linesQA.lineCatalog('3bp');
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id){
  const part=app.innerHTML.split('id="'+id+'"')[1];assert.ok(part,id);
  const section=part.split('<div class="sec"')[0];
  return textures.flatMap(texture=>{
    const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
    assert.ok(row,id+' '+texture);
    return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map((m,i)=>[texture+':'+i,texture,m[1]]);
  });
}
function incoming(from,to){
  const keys=[];
  for(const [key,texture,html] of cells(from))
    for(const m of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g))
      if(m[1]===to+'-'+texture){
        assert.equal(m[2].replace(/≈$/,''),'過');
        keys.push(key);
      }
  return keys;
}
const out={};
for(const [rank,id] of Object.entries({229:'ln-3bp-3b_r_model-16dlc3j',230:'ln-3bp-3b_r_model-jaiium'})){
  const model=nodes.get(id);assert.ok(model,id);
  assert.equal(model.pre,'翻前：BTN 開， 你 SB 3-bet ，BTN 跟');
  assert.deepEqual([model.facts.root.spot,model.facts.pot,model.facts.stack],['SB3_BTN',21,90]);
  const parent=nodes.get(model.source);
  const roots=parent?[parent.source]:catalog.filter(n=>n.st===0 && app.innerHTML.includes('id="'+n.id+'"')).map(n=>n.id);
  const flop=[...new Set(roots.flatMap(from=>incoming(from,model.source)))].sort();
  const turn=[...new Set(incoming(model.source,id))].sort();
  assert.ok(flop.length,rank+' has no checked flop route');
  assert.deepEqual(turn,Array.from(model.allowed).sort());
  const river={};
  for(const [key,texture,html] of cells(id)){
    if(!model.allowed.includes(key))continue;
    const label=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
    assert.ok(['過','下注 ⅓','下注 ½','下注 ¾'].includes(label),label);
    river[key]=label;
  }
  out[rank]={model:id,parent:model.source,flop:Object.fromEntries(flop.map(k=>[k,'過'])),
    turn:Object.fromEntries(turn.map(k=>[k,'過'])),river};
}
console.log(JSON.stringify(out));
