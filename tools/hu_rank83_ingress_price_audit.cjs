// Read-only preflight: real primary ingress prices for the unverified rank83 family.
// This does not run CFR, change a model, or certify a board.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const crypto=require('node:crypto'),cp=require('node:child_process');
const TARGET='ln-opfr-t_model-msy0l9',SOURCE='ln-opfr-f_vs_xr-68t7c6',ROOT='ln-opfr-f_cbet-milqtu';
const FILES=['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const registryPath='data/nl2_hu_multiboard_status_current.json';
const registryBytes=fs.readFileSync(registryPath),registry=JSON.parse(registryBytes);
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},
 document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);
const sources={};
for(const f of FILES){const b=fs.readFileSync(f);sources[f]=sha(b);vm.runInContext(b.toString(),c,{filename:f});}
c.__linesQA.render('opfr');
const headings=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];
const sections=new Map(headings.map((h,i)=>[h[1],app.innerHTML.slice(h.index,headings[i+1]?.index??app.innerHTML.length)]));
const strip=s=>s.replace(/<[^>]*>/g,'').replace(/\s+/g,' ').trim();
function cells(id,tx){
 const m=sections.get(id).match(new RegExp('<tr[^>]+id="'+id+'-'+tx+'">([\\s\\S]*?)</tr>'));
 assert(m,id+':'+tx);return [...m[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(x=>x[1]);
}
function first(cell){const m=cell.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);return m?{to:m[1],label:m[2].replace(/≈$/,'')}:null;}
const model=c.__HU_MODEL_LAST.nodes.find(n=>n.id===TARGET);
assert(model && model.source===SOURCE && model.key==='你下注、對手加注、你跟|');
assert.deepEqual([model.facts.root.spot,model.facts.root.pot,model.facts.root.stack],['SB_BB',6,97]);
assert.deepEqual([model.facts.pot,model.facts.stack,model.facts.spr],[21,84,4]);
const family=Array.from(c.__HU_MODEL_LAST.nodes).filter(n=>n.id===TARGET||n.source===TARGET);
assert.equal(family.length,5);
const affected=family.map(n=>{
 const r=registry.records[n.id];assert.equal(r.label,'APPROX');assert.equal(r.proven_exact_board_count,0);
 return {rank:r.frequency_rank,model_id:n.id,source_model_id:n.source,assumed_pot:n.facts.pot,
         assumed_stack:n.facts.stack,assumed_spr:n.facts.spr,label:r.label};
}).sort((a,b)=>a.rank-b.rank);
assert.deepEqual(affected.map(r=>r.rank),[83,174,175,176,227]);
const sourceIntro=strip(sections.get(SOURCE).split('<table')[0]);
assert(sourceIntro.includes('下注 33%（2bb），BB 加注到 6bb，你要跟 4bb（底池 14bb）'));
const modelIntro=strip(sections.get(TARGET).split('<table')[0]);
assert(modelIntro.includes('加注到 3 倍'));
const nonAllInExamples=[];
for(const r of c.NLL.rows.filter(r=>r.sp==='opfr'&&r.nd==='f_vs_xr'))for(const e of r.eg||[]){
 if(e.me==='SB'&&e.pa==='SB'&&JSON.stringify(e.pc)==='["BB"]'&&e.t==='SRP'&&!e.l.includes(':a')){
  assert(/^SB:b0\.(33|75) BB:r3$/.test(e.l));assert.equal(e.pot,6);nonAllInExamples.push(e.l);
 }
}
assert(nonAllInExamples.length>0);
const sizes={'下注 ½':50,'下注 ¾':75,'下注 1':100},classes=['TPG','TPW','MID','DRAW','WDRAW'];
const ingress=[],excluded=[];
for(const tx of ['low','mid_high','KQ_high','A_high','paired','mono']){
 const root=cells(ROOT,tx),source=cells(SOURCE,tx);
 for(let col=0;col<5;col++){
  const call=first(source[col]);
  if(call?.label!=='跟'||call.to!==TARGET+'-'+tx)continue;
  const primary=first(root[col]);
  const secondary=root[col].includes('class="jmp sub" href="#'+SOURCE+'-'+tx+'"');
  if(!primary||!secondary||!(primary.label in sizes)){
   excluded.push({texture:tx,hand_class:classes[col],primary,reason:'NO_PRIMARY_BET_AND_RAISE_LINK'});continue;
  }
  const pct=sizes[primary.label],bet=6*pct/100,raiseTo=3*bet,callAmount=raiseTo-bet;
  const pot=6+2*raiseTo,stack=97-raiseTo,spr=stack/pot;
  ingress.push({texture:tx,hand_class:classes[col],primary_label:primary.label,primary_to:primary.to,
   raise_link_to:SOURCE+'-'+tx,call_to:call.to,flop_bet_pct:pct,raise_to_multiple:3,
   flop_bet_bb:bet,raise_to_bb:raiseTo,call_bb:callAmount,settled_pot_bb:pot,remaining_stack_bb:stack,
   actual_spr:spr,model_spr:4,spr_relative_error:Math.abs(spr/4-1),passes_current_spr_gate:Math.abs(spr/4-1)<=registry.spr_relative_tolerance});
 }
}
assert.equal(ingress.length,10);assert.equal(excluded.length,2);
assert.deepEqual([...new Set(ingress.map(x=>x.flop_bet_pct))].sort((a,b)=>a-b),[50,75,100]);
assert(ingress.every(x=>!x.passes_current_spr_gate));
assert.equal(registry.spr_relative_tolerance,.05);
assert(fs.readFileSync(registryPath).equals(registryBytes));
for(const f of FILES)assert.equal(sha(fs.readFileSync(f)),sources[f]);
console.log(JSON.stringify({schema:'NL2_RANK83_PRIMARY_INGRESS_PRICE_PREFLIGHT_V1',
 source_head:cp.execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),source_sha256:sources,
 registry_sha256:sha(registryBytes),counts:{CERT_MULTIBOARD:registry.CERT_MULTIBOARD,APPROX:registry.APPROX},
 profile:{spot:'SB_BB',actor:0,opponent:1,root_pot_bb:6,root_stack_bb:97},
 source_intro:sourceIntro,non_allin_example_count:nonAllInExamples.length,example_lines:[...new Set(nonAllInExamples)].sort(),
 ingress,excluded_source_call_cells:excluded,affected_models:affected,affected_certified_models:[],
 finding:'NO_LEGAL_PRIMARY_INGRESS_WITHIN_EXISTING_5PCT_SPR_GATE',
 constraint:'A single new scalar price cannot represent the three different primary ingress prices.',
 evidence_kind:'STATIC_RENDERED_ACTION_AND_EXACT_CHIP_ACCOUNTING_ONLY',native_solves:0,node_locked_boards:0,
 medium_assessed_boards:0,labels_or_prices_changed:false},null,2));
