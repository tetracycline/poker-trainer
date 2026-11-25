// B875 fixes B874: authored turn parents are not in the synthetic model list.
// Inventory only: actual rendered primary links; do not invent a flop parent.
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
 const heads=[...app.innerHTML.matchAll(/<div class="sec" data-node="([^"]+)" id="([^"]+)">/g)];
 const sec=new Map(heads.map((x,i)=>[x[2],app.innerHTML.slice(x.index,heads[i+1]?.index??app.innerHTML.length)]));
 const stage=new Map(heads.map(x=>{const nd=x[1].split('/')[1].replace(/^(3b_|3c_|lmp_|iso_)/,'');return [x[2],nd.startsWith('r_')?2:nd.startsWith('t_')?1:0]}));
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
 // Original authored turn sections are in the DOM but not __HU_MODEL_LAST.nodes.
 // Resolve every actual flop->turn primary edge, retaining its source id.
 const turnId=n.source;
 assert(sec.has(turnId)&&stage.get(turnId)===1,'missing rendered turn parent '+rank+': '+turnId);
 if(turn)assert.equal(turn.id,turnId);
 const flopSources=turn?[turn.source]:[...stage].filter(([k,s])=>s===0).map(([k])=>k);
 const flopIngress=flopSources.flatMap(k=>ingress(k,turnId).map(edge=>({source:k,...edge})));
 const actualFlopSources=[...new Set(flopIngress.map(e=>e.source))].sort();
 const turnIngress=ingress(turnId,id);
 assert(turnIngress.length>0,'no rendered turn->river primary edge '+rank);
 const flopIngressStatus=actualFlopSources.length?'RENDERED_PRIMARY_LINKS':'NO_DIRECT_FLOP_PRIMARY_LINK_FOUND';
 const river=[];
 for(const t of txs)for(const [i,html] of cells(id,t).entries()){
  if(n.allowed.includes(t+':'+i))river.push({cell:t+':'+i,action:html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈/g,'').trim()});
 }
 out.push({rank,id,profile,history:n.key,root:n.facts.root,pot:n.facts.pot,stack:n.facts.stack,spr:m.assumed_model_node_spr,flop_source:actualFlopSources.length===1?actualFlopSources[0]:null,flop_sources:actualFlopSources,turn_source:turnId,turn_source_kind:turn?'SYNTHETIC':'AUTHORED',flopIngressStatus,flopIngress,turnIngress,river});
}
console.log(JSON.stringify(out));
