const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = { innerHTML: '', querySelectorAll: () => [], addEventListener() {} };
const context = {
  console, __LINES_QA: true, location: { hash: '#lines' }, scrollTo() {}, addEventListener() {},
  document: { querySelector: () => app, querySelectorAll: () => [], getElementById: () => null }
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, { filename: file });
}

context.__linesQA.render('iso');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id) {
  const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  return textures.flatMap(texture=>{
    const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
    assert.ok(row,id);
    return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map((cell,i)=>[texture+':'+i,texture,cell[1]]);
  });
}
function incoming(source, target, label) {
  const keys = [];
  for (const [key, texture, html] of cells(source)) {
    for (const m of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)) {
      if (m[1] === target + '-' + texture) {
        assert.equal(m[2].replace(/≈$/, ''), label);
        keys.push(key);
      }
    }
  }
  assert.ok(keys.length, source + ' -> ' + target);
  return keys;
}



const id='ln-iso-lmp_t_model-1iwngt8';
const source='ln-iso-lmp_f_vs_xr-50pww0', root='ln-iso-lmp_f_lead-aqcv9i';
const model=nodes.get(id);
assert.equal(model.source,source);
assert.deepEqual([model.facts.root.pot,model.facts.root.stack],[2.5,99]);
assert.equal(model.key,'你下注、對手加注、你跟|');
const ingress=incoming(source,id,'跟');
const rootCells=new Map(cells(root).map(([key,tx,html])=>[key,{tx,html}]));
for(const key of ingress){
  const {tx,html}=rootCells.get(key);
  const primary=html.match(/<a class="jmp" href="#[^"]+">([^<]+)<.a>/);
  assert.equal(primary[1].replace(/≈$/,''),'下注 ½');
  assert.ok(html.includes('class="jmp sub" href="#'+source+'-'+tx+'"'));
}
assert.equal(ingress.length,24);
const turn={};
for(const [key,texture,html] of cells(id)){
  if(!model.allowed.includes(key))continue;
  const label=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈/g,'').trim();
  assert.ok(['過','下注 ⅓','下注 ½','下注 ¾'].includes(label));
  turn[key]=label;
}
assert.equal(Object.keys(turn).length,24);
const rows=context.NLL.rows.filter(row=>row.sp==='iso'&&row.nd==='lmp_f_vs_xr');
const examples=rows.flatMap(row=>row.eg||[]).filter(e=>e.me==='BB' && e.t==='LMP' && e.l.endsWith('CO:r3'));
assert.ok(examples.length);

const ranks={222:['ln-iso-lmp_r_model-1n1ge2d','下注 ¾',3.51],223:['ln-iso-lmp_r_model-1otnixw','下注 ⅓',5.539],224:['ln-iso-lmp_r_model-1wo1hx8','下注 ½',4.513],234:['ln-iso-lmp_r_model-1iqsf2n','過',9.525]};
const children={};
for(const [rank,[child,label,spr]] of Object.entries(ranks)){
 const river=nodes.get(child);
 assert.equal(river.source,id);assert.equal(river.facts.spr,spr);
 const here=incoming(id,child,label);const riverActions={};
 assert.deepEqual([...river.allowed].sort(),here.slice().sort());
 for(const [key,texture,html] of cells(child)){
  if(!river.allowed.includes(key))continue;
  const action=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈/g,'').trim();
  riverActions[key]=action;
 }
 children[rank]={model:child,label,price:spr,ingress:here,river:riverActions};
}
console.log(JSON.stringify({parent:id,flop:ingress,turn,children}));
