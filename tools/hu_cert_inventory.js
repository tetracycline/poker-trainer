#!/usr/bin/env node
/** Freeze the full 392-node modeled NL2 HU solver backlog at PR commit.
 * No synthetic line can be certified from family, approximate SPR, or texture.
 * Output contains one stable entry for every currently rendered model node. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const output=process.argv[2]||path.join(root,'data','nl2_hu_stage2_queue.json');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const ctx={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
  document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;vm.createContext(ctx);
const sources=['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'];
const sourceHash={};
for(const name of sources){const b=fs.readFileSync(path.join(root,name));sourceHash[name]=crypto.createHash('sha256').update(b).digest('hex');
  vm.runInContext(b.toString('utf8'),ctx,{filename:name});}
const records=[],seen=new Set(),byId=new Map(),spotCounts={};
for(const spot of ctx.NLL.spots){
  ctx.__linesQA.render(spot.id);
  const data=ctx.__HU_MODEL_LAST;
  if(!data||data.spot!==spot.id||!Array.isArray(data.nodes))throw Error('Missing render inventory for '+spot.id);
  spotCounts[spot.id]=data.nodes.length;
  for(const n of data.nodes){
    if(seen.has(n.id))throw Error('Duplicate model id '+n.id);
    seen.add(n.id);
    const profile=n.facts.root, family=profile.family;
    const eligibleTexts=n.allowed||[];
    if(!profile.rootSPR||!profile.pot||!profile.stack||!eligibleTexts.length)throw Error('Invalid model metadata '+n.id);
    const priority={SRP:0,'3BP':1,ISO:2,LMP:3}[family];
    if(priority===undefined)throw Error('Unknown family '+family);
    const solver=family==='ISO'?'ISO_BTN_CO':family==='LMP'?'LMP_CO_BB':profile.spot;
    const status='MODEL_UNCERTIFIED';
    const rec={
      model_id:n.id,source_id:n.source,spot:n.sp,node_name:n.nd,street:n.st,
      priority,preflop_text:n.pre,abstract_action_history:n.key,
      source_action:n.action,source_action_assumed_size_pot:n.size,
      family,solver_profile:solver,
      preflop_ranges_source:profile.range,root_pot_bb:profile.pot,
      root_remaining_bb:profile.stack,root_spr:profile.rootSPR,
      approx_pot_bb:n.facts.pot,approx_remaining_bb:n.facts.stack,
      approx_spr:n.facts.spr,
      represented_class_textures:eligibleTexts,
      represented_class_texture_count:eligibleTexts.length,
      exact_turn_board:null,exact_river_board:null,exact_action_tokens:null,
      exact_node_pot_bb:null,exact_node_spr:null,source_run_id:null,
      source_sha256:null,per_combo_proof_sha256:null,
      pool_lock_coverage:null,certified_cells:0,
      status,blockers:[
       'NO_EXACT_PUBLIC_BOARD_RUNOUT',
       'NO_PROVEN_COMPLETE_BET_SIZE_LINEAGE',
       'NO_MATCHED_CFR_COMBO_REACH_AND_SPR',
       'NO_MATCHED_NL2_POOL_LOCK_PROOF'
      ]
    };
    records.push(rec);byId.set(rec.model_id,rec);
  }
}
for(const rec of records){
  if(!rec.source_id.startsWith('ln-'))throw Error('invalid source id '+rec.model_id);
  if(rec.street===2&&byId.has(rec.source_id)&&byId.get(rec.source_id).street!==1)
    throw Error('river model has non-turn model parent '+rec.model_id);
}
records.sort((a,b)=>a.priority-b.priority||
  a.street-b.street||
  b.represented_class_texture_count-a.represented_class_texture_count||
  a.model_id.localeCompare(b.model_id));
const families={},stages={};
for(const rec of records){families[rec.family]=(families[rec.family]||0)+1;
  stages[rec.street]=(stages[rec.street]||0)+1;}
if(records.length!==392||stages[1]!==79||stages[2]!==313)throw Error('Unexpected coverage: '+JSON.stringify({count:records.length,stages}));
const outputJson={
 schema:'HU_NL2_CERT_QUEUE_V2',certification_standard:'Identical preflop range source, pot family, exact public flop/turn/river, exact bet history/size, exact node SPR, nonzero per-combo reach, solver convergence and pool lock scope. Never certify generic texture as an exact board.',
 source_sha256:sourceHash,
 summary:{model_nodes:records.length,certified_model_nodes:0,with_exact_board:0,
  by_family:families,by_street:stages,by_spot:spotCounts,
  queued_groups:[...new Set(records.map(x=>[x.family,x.solver_profile,x.street].join(':')))].length},
 records
};
fs.mkdirSync(path.dirname(output),{recursive:true});
fs.writeFileSync(output,JSON.stringify(outputJson,null,2)+'\n');
console.log(JSON.stringify(outputJson.summary));
