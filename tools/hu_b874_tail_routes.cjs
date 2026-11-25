// B874: final three >=0.2% SRP ranks, exact live route and chip-price inventory.
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const targets=[[154,'ipfr','ln-ipfr-r_model-1ovsfhk','BTN_BB'],[157,'opfr','ln-opfr-r_model-1puypid','UTG_CO'],[158,'opfr','ln-opfr-r_model-tl6ij8','UTG_CO']];
const reg=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json'));
const pri=JSON.parse(fs.readFileSync('data/nl2_hu_b838_234_approx_frequency_priority.json'));
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);
for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(f,'utf8'),c,{filename:f});
const txs=['low','mid_high','KQ_high','A_high','paired','mono'];
const out=[];
for(const [rank,spot,id,profile] of targets){
 c.__linesQA.render(spot);
 const nodes=new Map(c.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
 const heads=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
 const sec=new Map(heads.map((x,i)=>[x[1],app.innerHTML.slice(x.index,heads[i+1]?.index??app.innerHTML.length)]));
 const n=nodes.get(id),m=reg.records[id],p=pri.rows.find(x=>x.rank===rank);
 assert(n&&m&&p&&sec.has(id));
 assert.deepEqual([m.frequency_rank,m.label,m.solver_profile,m.street],[rank,'APPROX',profile,2]);
 assert(p.passes_min_0_2_pct_frequency&&p.model_id===id&&n.key===p.action_history);
 function cells(k,t){const row=sec.get(k)?.match(new RegExp('<tr[^>]+id="'+k+'-'+t+'">([\\s\\S]*?)</tr>'));return row?[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(x=>x[1]):[];}
 function ingress(src,dst){
  const a=[];
  for(const t of txs)for(const [i,html] of cells(src,t).entries()){
   for(const x of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g))
    if(x[1]===dst+'-'+t)a.push({cell:t+':'+i,action:x[2].replace(/≈$/,'').trim()});
  }
  return a;
 }
 const turn=nodes.get(n.source);
 assert(turn&&sec.has(n.source));
 const flopIngress=ingress(turn.source,turn.id),turnIngress=ingress(turn.id,id);
 const river=[];
 for(const t of txs)for(const [i,html] of cells(id,t).entries()){
  if(n.allowed.includes(t+':'+i))river.push({cell:t+':'+i,action:html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈/g,'').trim()});
 }
 out.push({rank,id,profile,history:n.key,root:n.facts.root,pot:n.facts.pot,stack:n.facts.stack,spr:m.assumed_model_node_spr,flop_source:turn.source,turn_source:turn.id,flopIngress,turnIngress,river});
}
console.log(JSON.stringify(out));
