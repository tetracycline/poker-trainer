// B883: stage exact UTG/CO flop-call settlement in memory, not production.
// No native solver invocation, no CERT promotions, no modification of registry.
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const path=require('node:path');
const out=process.argv[2]; assert(out);
const bytes=p=>fs.readFileSync(p);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const gitBlob=b=>crypto.createHash('sha1').update('blob '+b.length+'\0').update(b).digest('hex');
const source=bytes('nl2_hu_model.js');
assert.equal(gitBlob(source),'b3dea42d0478e178aefda628e539ec7d95fbe6bd');
const status=JSON.parse(bytes('data/nl2_hu_multiboard_status_current.json'));
const frozen=JSON.parse(bytes('data/nl2_hu_multiboard_prerank.json'));
const priority=JSON.parse(bytes('data/nl2_hu_b838_234_approx_frequency_priority.json'));
const parent='ln-opfr-t_model-19umlco', ingress='ln-opfr-f_vs_donk-1cci9ku';
const targets={
  [parent]:[68,'CERT-MULTIBOARD',13,94.25,7.25],
  'ln-opfr-r_model-1puypid':[157,'APPROX',32.5,84.5,2.6],
  'ln-opfr-r_model-tl6ij8':[158,'APPROX',21.66,89.92,4.151],
  'ln-opfr-r_model-8w3cpr':[205,'APPROX',13,94.25,7.25]
};
assert.deepEqual([status.CERT_MULTIBOARD,status.APPROX,status.EST,status.TOTAL],[158,234,0,392]);
const weights=new Map(frozen.nodes.map(x=>[x.model_id,x.estimated_NL2_hand_opportunity_fraction]));
assert.equal(weights.size,392);
const allWeight=[...weights.values()].reduce((a,b)=>a+b,0);
const certWeight=Object.entries(status.records).filter(([,r])=>r.label==='CERT-MULTIBOARD').reduce((a,[id])=>a+weights.get(id),0);
assert.equal(Number((100*certWeight/allWeight).toFixed(6)),84.700987);
assert.deepEqual(Object.keys(status.records).filter(k=>status.records[k].source_model_id===parent).sort(),Object.keys(targets).filter(k=>k!==parent).sort());
assert.equal(status.records[parent].source_model_id,ingress);
for(const [id,[rank,label]] of Object.entries(targets)){
  const r=status.records[id];
  assert.deepEqual([r.frequency_rank,r.label,r.solver_profile,r.family],[rank,label,'UTG_CO','SRP']);
  if(rank===157||rank===158)assert(priority.rows.some(x=>x.rank===rank&&x.model_id===id&&x.passes_min_0_2_pct_frequency));
}
const oldProofs=status.records[parent].certified_3_to_5_exact_flop_boards;
assert.equal(oldProofs.length,3);
assert.equal(new Set(oldProofs.map(x=>x.flop)).size,3);
for(const b of oldProofs){
  assert.equal(b.actual_pot_bb,13);
  assert.equal(b.actual_effective_stack_bb,94.25);
  assert.equal(b.actual_spr,7.25);
  assert.equal(b.model_assumed_spr,7);
  assert(Math.abs(b.actual_spr/b.model_assumed_spr-1)<=.05);
  assert.match(b.source_sha256,/^[a-f0-9]{64}$/);
  assert(b.strict_full_street_combo_reachable>0);
  assert(b.nl2_locked_variants.length>0);
}
const oldText=source.toString('utf8');
const needle='    const next = limpRaiseCall\n';
assert.equal(oldText.split(needle).length,2);
const replacement=[
'    // B883 candidate: the UTG check-call pays only the outstanding 50% flop bet.',
"    const utgCall = id === 'ln-opfr-t_model-19umlco';",
"    if (utgCall && (s.modelMeta || s.id !== 'ln-opfr-f_vs_donk-1cci9ku' ||",
"        s.st !== 0 || action !== 'call' || m.root.spot !== 'UTG_CO' ||",
"        s.key !== '你過、對手下注' || m.root.pot !== 6.5 || m.root.stack !== 97.5))",
"      throw Error('Changed exact UTG half-pot flop-call source');",
"    const utgChild = s.id === 'ln-opfr-t_model-19umlco';",
"    if (utgChild && (s.st !== 1 || m.pot !== 13 || m.stack !== 94.25 ||",
"        !['bet','check'].includes(action))) throw Error('Changed UTG continuation');",
"    const utgPaid = utgChild && action === 'bet' ? Math.round(m.pot*size*100)/100 : 0;",
"    const next = utgCall ? {pot:13,stack:94.25,root:m.root}",
"      : utgChild ? {pot:round(m.pot+2*utgPaid),stack:round(m.stack-utgPaid),root:m.root}",
"      : limpRaiseCall",""
].join('\n');
const candidate=oldText.replace(needle,replacement);
function render(modelSource){
  const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
  const ctx={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
  ctx.window=ctx;vm.createContext(ctx);
  for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js']){
    vm.runInContext(f==='nl2_hu_model.js'?modelSource:bytes(f).toString('utf8'),ctx,{filename:f});
  }
  const nodes={};
  for(const spot of ctx.NLL.spots){
    ctx.__linesQA.render(spot.id);
    for(const n of ctx.__HU_MODEL_LAST.nodes){
      assert(!nodes[n.id]); nodes[n.id]=JSON.parse(JSON.stringify(n));
    }
  }
  assert.equal(Object.keys(nodes).length,392);
  return nodes;
}
const before=render(oldText),after=render(candidate);
assert.deepEqual(Object.keys(before).sort(),Object.keys(after).sort());
const changed=[];
for(const id of Object.keys(before)){
  const a=before[id],b=after[id];
  if(!targets[id]){assert.deepEqual(b,a,id);continue;}
  const {facts:af,...ar}=a,{facts:bf,...br}=b;
  assert.deepEqual(br,ar,id);
  const [rank,label,pot,stack,spr]=targets[id];
  assert.deepEqual([bf.pot,bf.stack,bf.spr],[pot,stack,spr],id);
  assert.deepEqual(bf.root,af.root);
  assert.equal(af.spr,status.records[id].assumed_model_node_spr);
  changed.push({id,rank,label,before:af,after:bf});
}
assert.equal(changed.length,4);
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'nl2_hu_model.candidate.js'),candidate);
const report={schema:'NL2_B883_STAGED_UTG_HALF_POT_CALL_PRICE_V1',candidate_only:true,active_registry_unchanged:true,
  candidate_sha256:sha(Buffer.from(candidate)),original_sha256:sha(source),changed,
  unchanged_other_model_nodes:388,existing_rank68_certificates:oldProofs.map(b=>({flop:b.flop,turn:b.turn,source_run_id:b.source_run_id,source_sha256:b.source_sha256,old_assumed_spr:b.model_assumed_spr,actual_spr:b.actual_spr})),
  rank68_certificate_geometry_requires_atomic_metadata_reconciliation:true,
  rank68_existing_evidence_not_reclassified:true,CERT:158,APPROX:234,coverage_pct:84.700987,new_native_solves:0,new_certifications:0,new_locks:0,new_medium:0};
fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({affected:changed.map(x=>x.rank),unchanged:388,coverage_pct:report.coverage_pct,certifications:0}));
