const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const context={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
context.window=context;vm.createContext(context);
for(const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(file,'utf8'),context,{filename:file});
context.__linesQA.render('3bp');
const nodes=new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const model=nodes.get('ln-3bp-3b_r_model-rlw959'),parent=nodes.get(model.source);
assert.equal(parent.id,'ln-3bp-3b_t_model-n5cvfv');
assert.equal(parent.source,'ln-3bp-3b_f_cbet-ke0pam');
assert.deepEqual([model.facts.root.spot,model.facts.pot,model.facts.stack],['BB3_BTN',20.5,90]);
assert.deepEqual(Array.from(model.allowed).sort(),['low:2','mid_high:2']);
function cells(id){
 const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
 return ['low','mid_high','KQ_high','A_high','paired','mono'].flatMap(texture=>{
  const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));assert.ok(row,id);
  return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map((m,i)=>[texture+':'+i,texture,m[1]]);
 });
}
function incoming(source,target){
 const result={};
 for(const [key,texture,html]of cells(source))for(const m of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/g)){
  if(m[1]===target+'-'+texture){assert.equal(m[2].replace(/≈$/,''),'過');result[key]='過';}
 }
 assert.ok(Object.keys(result).length);return result;
}
const flop=incoming(parent.source,parent.id),turn=incoming(parent.id,model.id),river={};
for(const [key,,html]of cells(model.id))if(model.allowed.includes(key)){
 const label=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
 assert.equal(label,'過');river[key]=label;
}
assert.deepEqual(Object.keys(turn).sort(),Array.from(model.allowed).sort());
console.log(JSON.stringify({flop,turn,river}));
