// Read the rendered ISO paths and their original examples. This audit performs no solves or registry writes.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');

const app = {innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const ctx = {console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
  document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
ctx.window=ctx;
vm.createContext(ctx);
for(const path of ['learn_data.js','lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js']){
  vm.runInContext(fs.readFileSync(path,'utf8'),ctx,{filename:path});
}
ctx.__linesQA.render('iso');
const rendered=new Map(ctx.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const registry=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json'));
const records=Object.values(registry.records);
const byRank=Object.fromEntries(records.map(r=>[r.frequency_rank,r]));
const parent='ln-iso-iso_f_stab-lvef1p', btnParent='ln-iso-f_cbet-hd3ik2';
const targetRanks=[122,123], controls=[124,125];
const pre=byRank[122].preflop_text;
assert.equal(pre,byRank[123].preflop_text);
assert.match(pre,/你 CO 溜入.*SB 加注隔離.*你 CO 跟/);
assert.match(byRank[124].preflop_text,/CO 溜入.*你 BTN 加注隔離.*CO 跟/);
const affected=records.filter(r=>r.preflop_text===pre).map(r=>r.frequency_rank).sort((a,b)=>a-b);
assert.deepEqual(affected,[122,123,225,247,248,257,274,275,276,277,278]);
assert.ok(affected.every(r=>byRank[r].label==='APPROX'&&byRank[r].solver_profile==='ISO_BTN_CO'));

function section(id){
  const body=app.innerHTML.split('id="'+id+'"')[1];
  assert.ok(body,id);
  return body.split('<div class="sec"')[0];
}
function firstLink(id,cell){
  const [texture,column]=cell.split(':');
  const row=section(id).match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
  assert.ok(row,cell);
  const cells=[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)];
  const link=cells[Number(column)][1].match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);
  assert.ok(link,cell);
  return {target:link[1],action:link[2].replace(/≈$/,'')};
}
const facts={};
for(const r of [...targetRanks,...controls]){
  const m=byRank[r],node=rendered.get(m.model_id),root=node.facts.root;
  assert.equal(node.source,m.source_model_id);
  assert.equal(root.spot,'ASSUMED_ISO_4BB');
  assert.equal(root.pot,r<=123?9:9.5);
  assert.equal(root.stack,96);
  assert.equal(node.source,r<=123?parent:btnParent);
  const size=r%2===0?'下注 ½':'下注 ⅓';
  const actual={};
  for(const cell of node.allowed){
    const tex=cell.split(':')[0],entry=firstLink(node.source,cell),decision=firstLink(node.id,cell);
    assert.equal(entry.target,node.id+'-'+tex);
    assert.equal(entry.action,size);
    actual[cell]=[entry.action,decision.action];
  }
  facts[r]={model_id:node.id,source:node.source,root_pot_bb:root.pot,root_stack_bb:root.stack,
    assumed_turn_spr:m.assumed_model_node_spr,role_aware_preflop_text:m.preflop_text,primary_by_visible_cell:actual};
}
const prices={};
for(const name of ['iso_f_stab','iso_t_barrel']){
  const entries=ctx.NLL.rows.filter(r=>r.sp==='iso'&&r.nd===name).flatMap(r=>r.eg)
    .filter(e=>e.t==='ISO'&&e.me==='CO'&&e.pa==='SB'&&e.pc.length===1&&e.pc[0]==='CO');
  assert.equal(entries.length,name==='iso_f_stab'?38:42);
  assert.ok(entries.every(e=>e.pot===9.5&&e.stk===95.5));
  prices[name]={example_entries:entries.length,root_pot_bb:9.5,root_stack_bb:95.5};
}
assert.match(section(parent),/加注到 4.3bb/);
assert.match(section(parent),/底池 9.5bb/);
const chart={};
for(const key of ['CO>SB','CO>BTN']){
  const v=ctx.LD.iso[key];
  assert.equal(v.size,key==='CO>SB'?5:4);
  chart[key]={iso_to_bb:v.size,chart_pct:v.pct,core_classes:v.core.length,conditional_pool_source:v.sc,
    pooled_limper_response_pct:{fold:v.lf,call:v.lc,raise:v.lr},solver_node_status:v.gv};
}
const comparison={};
for(const [i,r] of targetRanks.entries()){
  const ctl=byRank[controls[i]],b=ctl.certified_3_to_5_exact_flop_boards;
  assert.equal(b.length,3);
  assert.ok(b.every(x=>x.actual_spr===b[0].actual_spr&&x.acting_seat===1&&x.actual_exact_action_line===(r===122?'x b50 c/x':'x b33 c/x')));
  const delta=100*Math.abs(b[0].actual_spr/byRank[r].assumed_model_node_spr-1);
  assert.ok(delta>5);
  comparison[r]={different_role_control_rank:controls[i],actual_control_spr:b[0].actual_spr,
    relative_spr_error_pct:Number(delta.toFixed(6)),control_original_flops:b.map(x=>x.flop),transferable_original_boards:0};
}
const checked=JSON.parse(execFileSync(process.env.PYTHON||'python3',['-c',`
import json,sys
sys.path.insert(0,'tools')
from hu_b568_caller_rivers import hand_cell
from hu_b580_rank27_rivers import suit_isomorphism_class
from solve_hu_assumed_pots import RULES
spec=[('9h7d3c','2s','7c8c','9cJc'),('Kh9c4d','2s','9hTh','JcKc'),('Qs8s5d','2c','8d9d','JdQd')]
assert len({suit_isomorphism_class(f) for f,t,a,b in spec})==3
iso={k:v for k,v in RULES.items() if v['kind']=='ISO'}
assert set(iso)=={'ISO_BTN_CO'} and (iso['ISO_BTN_CO']['oop'],iso['ISO_BTN_CO']['ip'],iso['ISO_BTN_CO']['pfr'])==('CO','BTN','ip')
out=[]
for f,t,a,b in spec:
    hands={}
    for rank,h in [('122',a),('123',b)]:
        c=hand_cell(h,f);d=hand_cell(h,f+t);cards=f+t+h+'AcAd'
        assert len(set(cards[i:i+2] for i in range(0,len(cards),2)))==8
        assert c[1]==d[1]==('MID' if rank=='122' else 'TPG')
        hands[rank]=dict(caller_hand=h,flop_cell=c[0],turn_cell=d[0],hand_class=c[1])
    out.append(dict(flop=f,turn=t,hands=hands))
print(json.dumps(dict(only_available_iso_profile=iso,candidates=out)))
`],{encoding:'utf8'}));
for(const candidate of checked.candidates){
  for(const [rank,h] of Object.entries(candidate.hands)){
    const id=byRank[rank].model_id;
    assert.equal(firstLink(parent,h.flop_cell).target,id+'-'+h.flop_cell.split(':')[0]);
    const decision=firstLink(id,h.turn_cell).action;
    assert.equal(decision,rank==='122'?'過':'下注 ½');
    h.rendered_turn_decision=decision;
  }
}
const knownIso=JSON.parse(fs.readFileSync('data/solver_evidence/STAGE2_ISO_LMP_LOCKED.json')).artifacts
  .filter(a=>a.spot.startsWith('ISO'));
assert.ok(knownIso.length>0&&knownIso.every(a=>a.spot==='ISO_BTN_CO'));
const scenarios={};
for(const [name,pot,stack] of [['rendered_model_4bb',900,9600],['raw_postflop_example',950,9550],['preflop_chart_5bb_100bb_start',1100,9500]]){
  const ys={};
  for(const [rank,pct] of [[122,50],[123,33]]){
    const bet=Math.floor((pot*pct+50)/100),nodePot=pot+2*bet,nodeStack=stack-bet;
    ys[rank]={flop_bet_chips:bet,turn_pot_bb:nodePot/100,turn_stack_bb:nodeStack/100,
      integer_percent_turn_spr:Number((nodeStack/nodePot).toFixed(6))};
  }
  scenarios[name]={root_pot_bb:pot/100,root_stack_bb:stack/100,native_integer_percent_branch_projections:ys};
}
const result={schema:'NL2_HU_B716_CO_CALLER_SB_ISOLATOR_READ_ONLY_PRICE_AUDIT_V1',
  target_ranks:targetRanks,affected_approx_ranks:affected,affected_certified_ranks:[],rendered_models:facts,
  raw_example_prices:prices,alternative_root_scenarios:scenarios,existing_stage2_locked_iso_profiles:[...new Set(knownIso.map(a=>a.spot))],
  story_display:{raw_dead_blind_bb:1,implied_raise_bb:4.25,rounded_display_bb:4.3},
  preflop_training_chart:chart,available_conditional_solver_profiles:checked.only_available_iso_profile,
  price_and_role_comparison:comparison,static_candidates:checked.candidates,native_solves:0,
  actor_locked_public_boards:0,medium_assessed_public_boards:0,
  proposed_candidate_scope:'UI_ONLY_PENDING_EXPLICIT_SB_ISOLATOR_OOP_CO_CALLER_IP_RANGES_ROOT_PRICE_AND_NATIVE_REACH'};
console.log(JSON.stringify(result,null,2));
