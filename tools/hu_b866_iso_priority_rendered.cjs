// B866: source-blind, read-only ISO exact-route preflight for remaining 0.2%+ models.
// This is rendered UI ingress evidence only, NOT a GTO solve, NL2 lock or CERT.
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const TARGETS={
  122:'ln-iso-iso_t_model-110p2yk',
  123:'ln-iso-iso_t_model-12mapd0',
  139:'ln-iso-iso_r_model-11rm8wu',
  141:'ln-iso-iso_r_model-1w63du3',
  142:'ln-iso-iso_r_model-szxrm3',
  148:'ln-iso-r_model-15ncuqc'
};
const TEXTURES=['low','mid_high','KQ_high','A_high','paired','mono'];
const HANDS=['TPG','TPW','MID','DRAW','WDRAW'];
const FILES=['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'];
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const statusRaw=fs.readFileSync('data/nl2_hu_multiboard_status_current.json');
const priRaw=fs.readFileSync('data/nl2_hu_b838_234_approx_frequency_priority.json');
const status=JSON.parse(statusRaw),priority=JSON.parse(priRaw);
assert.deepEqual([status.CERT_MULTIBOARD,status.APPROX,status.EST,status.TOTAL],[158,234,0,392]);
assert.equal(priority.source_status_git_blob_sha,'996fc513406c8a1207d50bc300453858909493d9');
assert.equal(priority.current_certified_opportunity_share_pct,84.700987);
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);
const sourceSha={};
for(const name of FILES){const bytes=fs.readFileSync(name);sourceSha[name]=sha(bytes);vm.runInContext(bytes.toString('utf8'),c,{filename:name})}
c.__linesQA.render('iso');
const nodes=new Map(c.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const headers=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
const sections=new Map(headers.map((h,i)=>[h[1],app.innerHTML.slice(h.index,headers[i+1]?.index??app.innerHTML.length)]));
function cells(id,texture){
  const html=sections.get(id);
  if(!html)return [];
  const row=html.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
  if(!row)return [];
  return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
}
function links(cell){
  return [...cell.matchAll(/<a\b[^>]*href="#([^"]+)"[^>]*>([^<]*)<\/a>/g)].map(m=>({to:m[1],action:m[2].replace(/≈$/,'').trim()}));
}
const out=[];
for(const [rankText,id] of Object.entries(TARGETS)){
  const rank=Number(rankText),r=priority.rows.find(r=>r.rank===rank);
  const model=status.records[id],n=nodes.get(id);
  assert(r&&r.model_id===id&&r.passes_min_0_2_pct_frequency);
  assert(model&&n);
  assert.equal(model.label,'APPROX');
  assert.equal(model.frequency_rank,rank);
  assert.equal(model.solver_profile,'ISO_BTN_CO');
  assert(['ASSUMED_ISO_4BB','ISO_BTN_CO'].includes(n.facts.root.spot), 'Unexpected ISO root source');
  assert.deepEqual([n.facts.root.pot,n.facts.root.stack],[9.5,96]);
  assert.equal(n.key,r.action_history);
  assert.equal(n.id,id);
  assert.equal(model.street,rank===122||rank===123?1:2);
  assert(sections.has(id),'Missing exact rendered target '+id);
  const source=n.source, sourcePresent=sections.has(source);
  const sourceRows=[],targetRows=[];
  for(const tx of TEXTURES){
    const sr=cells(source,tx),tr=cells(id,tx);
    for(let i=0;i<5;i++){
      const key=tx+':'+i;
      const entry=(sr[i]?links(sr[i]):[]).filter(link=>link.to===id+'-'+tx);
      if(entry.length)sourceRows.push({texture:tx,hand_class:HANDS[i],model_key:key,source_table:source,entry_actions:entry.map(x=>x.action)});
      if(n.allowed.includes(key)){
        const targetLinks=tr[i]?links(tr[i]):[];
        const primary=targetLinks[0]||null;
        targetRows.push({texture:tx,hand_class:HANDS[i],model_key:key,primary_action:primary?.action||null,target_link:primary?.to||null});
      }
    }
  }
  assert(targetRows.length>0);
  assert(sourceRows.length>0 || !sourcePresent);
  out.push({
    rank,model_id:id,street:model.street,original_family:'ISO_BTN_CO',original_preflop_source:n.facts.root.spot,preflop_text:n.pre,
    rendered_history:n.key,source_table:source,source_table_rendered:sourcePresent,
    assumed_root_pot_bb:n.facts.root.pot,assumed_root_stack_bb:n.facts.root.stack,
    model_node_pot_bb:n.facts.pot,model_node_stack_bb:n.facts.stack,assumed_model_node_spr:model.assumed_model_node_spr,
    estimated_per_hand_opportunity_pct:r.estimated_per_hand_frequency_pct,
    primary_ingress:sourceRows,rendered_target_actions:targetRows,
    positive_ingress_cells:sourceRows.length,
    eligibility:'RENDERED_ONLY_NO_NATIVE_SOURCE_OR_COMBO_CERT',
    certification_status:'APPROX'
  });
}
const report={
  schema:'NL2_B866_FROZEN_ISO_122_123_139_141_142_148_REACH_PREFLIGHT_V1',
  origin:'SOURCE_BLIND_B838_FREQUENCY_ORDER',source_files_sha256:sourceSha,
  status_sha256:sha(statusRaw),frozen_priority_sha256:sha(priRaw),
  selected_ranks:Object.keys(TARGETS).map(Number),
  source_blind_all_selected_above_0_2pct:true,
  reran_native_solver:false,recorded_original_GTO_subgames:0,recorded_original_actor_locked_subgames:0,
  strict_legal_combo_certifications:0,CERT_promotions:0,CERT:158,APPROX:234,NL2_model_opportunity_coverage_pct:84.700987,
  observed_private_card_NL2_frequencies:false,
  note:'UI-rendered ingress is only a first source gate. Check actor, full chip prices/SPR, GTO SHA, exact both-seat legal combo reach, and real NL2 partial locks before certification.',
  models:out
};
const text=JSON.stringify(report,null,2)+'\n';
if(process.argv[2])fs.writeFileSync(process.argv[2],text);
console.log(JSON.stringify({schema:report.schema,selected_ranks:report.selected_ranks,ingress_cells:out.map(x=>[x.rank,x.positive_ingress_cells,x.source_table_rendered]),cert:report.CERT,approx:report.APPROX,source_only:true}));
