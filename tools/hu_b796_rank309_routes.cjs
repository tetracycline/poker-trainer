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
const rank = 309;
const id = 'ln-3bp-3b_r_model-sk61px';
const root = 'ln-3bp-3b_f_cbet-1h4do36';
const parent = 'ln-3bp-3b_t_delay-1jcjii2';
const model = nodes.get(id);
const entry = catalog.find(row=>row.id===root);
assert.equal(model.pre,'翻前：CO 開， 你 BTN 3-bet ，CO 跟');
assert.equal(model.source,parent);
assert.deepEqual([model.facts.root.spot,model.facts.pot,model.facts.stack],['CO3_BTN',16.5,92.5]);
assert.equal(entry.ln.eg.me,'BTN');
assert.equal(entry.ln.eg.role.join('/'),'tb/COopen>BTN');
assert.equal(entry.ln.eg.l,'CO:x');
assert.equal(entry.ln.hands[2],'MID');
const flop = incoming(root,parent).sort();
const turn = incoming(parent,id).sort();
assert.deepEqual(flop,['A_high:2','KQ_high:2','mono:2','paired:2']);
assert.deepEqual(turn,['KQ_high:2','mono:2']);
assert.deepEqual(turn,Array.from(model.allowed).sort());
const river={};
for(const [key,,html] of cells(id)){
  if(!model.allowed.includes(key))continue;
  const text=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  assert.equal(text,'過');river[key]=text;
}
const labels = keys => Object.fromEntries(keys.map(key=>[key,'過']));
console.log(JSON.stringify({rank,id,root,parent,flop:labels(flop),turn:labels(turn),river}));
