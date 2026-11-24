const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = {innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const ctx = {console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
  document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
  vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
ctx.__linesQA.render('iso');
const nodes=new Map(ctx.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const catalog=ctx.__linesQA.lineCatalog('iso');
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
const records=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json')).records;
const facing='ln-iso-lmp_f_vs_cbet-1v97kap';
const intro=app.innerHTML.split('id="'+facing+'"')[1].split('<table')[0].replace(/<[^>]+>/g,' ').replace(/\s+/g,' ');
assert.match(intro,/CO.*limp，BB 過牌（底池 2.5bb）.*BB 下注 33%/);
function primary(from,to,label){
  const links={};
  for(const [key,texture,cell] of cells(from)){
    const first=cell.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);
    if(first?.[1]!==to+'-'+texture)continue;
    assert.equal(first[2].replace(/≈$/,''),label);
    links[key]=label;
  }
  assert(Object.keys(links).length);
  return links;
}
const result={};
for(const [rank,id,label,pct] of [
  [115,'ln-iso-lmp_r_model-17dzvwx','下注 ⅓',33],
  [116,'ln-iso-lmp_r_model-1c6f833','下注 ½',50],
  [118,'ln-iso-lmp_r_model-zhthyp','下注 ⅔',66],
]){
  const model=nodes.get(id),record=records[id];
  assert.deepEqual([record.frequency_rank,record.solver_profile,model.facts.root.family,model.facts.root.pot,model.facts.root.stack],[rank,'LMP_CO_BB','LMP',2.5,99]);
  assert.equal(model.pre,'翻前： 你 CO 溜入 ，BB 過');
  assert.equal(model.key,'對手下注、你跟|對手過、你下注、對手跟|對手過');
  const flop=primary(facing,model.source,'跟'),turn=primary(model.source,id,label),river={};
  for(const [key,,cell] of cells(id)){
    if(!model.allowed.includes(key))continue;
    river[key]=cell.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈$/,'').trim();
    assert(river[key] && river[key]!=='—');
  }
  assert.deepEqual(Object.keys(turn).sort(),Object.keys(river).sort());
  result[rank]={id,facing,parent:model.source,example_flop_pct:33,turn_pct:pct,model_spr:record.assumed_model_node_spr,flop,turn,river};
}
assert.deepEqual(Object.keys(result[115].turn),['low:1']);
assert.deepEqual(Object.keys(result[116].turn).sort(),['paired:0','paired:2','paired:4']);
console.log(JSON.stringify(result));
