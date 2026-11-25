// B873: read actual rank152 ingress and turn action cells; never infer another model's sizes.
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);
for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(f,'utf8'),c,{filename:f});
c.__linesQA.render('ipc');
const heads=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
const sec=new Map(heads.map((x,i)=>[x[1],app.innerHTML.slice(x.index,heads[i+1]?.index??app.innerHTML.length)]));
const id='ln-ipc-t_model-1jnj1k6',n=c.__HU_MODEL_LAST.nodes.find(n=>n.id===id);
const reg=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json')),m=reg.records[id];
assert.deepEqual([m.frequency_rank,m.label,m.solver_profile,m.street],[152,'APPROX','SB_BB',1]);
assert.equal(n.key,'對手下注、你加注、對手跟|對手過');
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id,tx){const row=sec.get(id)?.match(new RegExp('<tr[^>]+id="'+id+'-'+tx+'">([\\s\\S]*?)</tr>'));return row?[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]):[];}
const flop={},turn={};
for(const tx of textures){
 const src=cells(n.source,tx),dst=cells(id,tx);
 for(let i=0;i<5;i++){
  const k=tx+':'+i;
  if(src[i]){
   const a=[...src[i].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)];
   if(a.some(x=>x[1]===id+'-'+tx))flop[k]=a.find(x=>x[1]===id+'-'+tx)[2].replace(/≈$/,'').trim();
  }
  if(dst[i]&&n.allowed.includes(k))turn[k]=dst[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈/g,'').trim();
 }
}
assert(sec.has(id));
console.log(JSON.stringify({id,source:n.source,history:n.key,root:n.facts.root,pot:n.facts.pot,stack:n.facts.stack,spr:m.assumed_model_node_spr,flop,turn}));
