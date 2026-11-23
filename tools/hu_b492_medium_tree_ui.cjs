const assert=require('node:assert/strict');
const fs=require('node:fs'), vm=require('node:vm'), zlib=require('node:zlib');
const crypto=require('node:crypto');
const read=f=>JSON.parse(fs.readFileSync(f));
const files=process.argv[2]?[process.argv[2]]:[492,493].map(n=>'data/nl2_hu_b'+n+'_half_pot_leads.json').filter(f=>fs.existsSync(f));
const reports=files.map(read);
for(const report of reports)assert.equal(report.schema,'NL2_HU_B492_CONDITIONAL_HALF_POT_LEADS_V1');
const records=reports.flatMap(r=>r.records);
const frozen=read(process.argv[3]||'data/nl2_hu_multiboard_status_current.json');
const ctx=vm.createContext({URLSearchParams,console});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),ctx);
const helper=ctx.nl2HalfPotLeads;
let positive=0, others=0, first=null;
for(const row of records){
  const m=frozen.records[row.model_id];
  if(m?.label!=='CERT-MULTIBOARD')continue;
  const old=m.certified_3_to_5_exact_flop_boards.find(b=>b.public_board===row.public_board && b.actual_exact_action_line===row.line);
  if(!old || !old.nl2_locked_variants.some(v=>v.sha256===row.original_lock_sha256))continue;
  assert.equal(helper.match(records,m,old),row);
  assert.equal(helper.match(records,m,{...old,source_sha256:'0'.repeat(64)}),null);
  if(row.status!=='BOTH_POSITIVE'){others++;continue;}
  positive++;
  const bySource=helper.reachReport(m,row);
  assert.equal(Object.values(bySource.gto_references)[0],row.gto);
  assert.equal(Object.values(bySource.references)[0],row.exp_oop);
  const pin=row.pin;
  const bytes=fs.readFileSync('data/solver_evidence/NL2_MULTIBOARD_'+pin.viewer_archive_code+'.json.gz');
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),pin.viewer_sha256);
  const archive=JSON.parse(zlib.gunzipSync(bytes));
  assert.equal(archive.source_run_id,row.gto.source_run_id);
  for(const version of [row.gto,row.exp_oop]){
    const cases=archive.artifacts.flatMap(group=>group.cases);
    const c=cases.find(c=>c.source_sha256===version.source_sha256&&c.version===version.version);
    const node=c.nodes.find(n=>n.public_board===row.public_board&&n.exact_node_line===row.line&&n.acting_seat===row.seat);
    const hands=c.hands_by_seat[row.seat];
    assert.equal(crypto.createHash('sha256').update(JSON.stringify(hands)).digest('hex'),version.source_hand_order_sha256);
    assert.deepEqual(node.source_actions,version.source_actions);
    assert.equal(node.strictly_reachable_masks_b64,version.compatible_action_mask_b64);
    const mask=Buffer.from(version.compatible_action_mask_b64,'base64');
    const action=1<<node.source_actions.indexOf('b50');
    assert.ok(node.source_actions.includes('b50'));
    assert.equal(mask.filter(bits=>bits&action).length,version.b50.eligible);
  }
  first??={m,old,row,archive};
  const corrupt={...row, original_gto_sha256:'f'.repeat(64)};
  assert.equal(helper.match([corrupt],m,old),null);
  assert.throws(()=>helper.match([{...row,board:{...row.board,actual_pot_bb:0}}],m,old));

}

const page=fs.readFileSync('nl2-multiboard.js','utf8');
const view=page.slice(page.indexOf('const el='),page.indexOf("el('model').addEventListener"));
const tick=()=>new Promise(resolve=>setImmediate(resolve));

function element(){
  let content='',value='';
  return {children:[],checked:true,hidden:false,disabled:false,
    get textContent(){return content+this.children.map(c=>c.textContent).join('');},
    set textContent(v){content=String(v);this.children=[];},
    get value(){return value;},set value(v){value=String(v);},
    get lastElementChild(){return this.children.at(-1);},get options(){return this.children;},
    appendChild(child){if(!this.children.length&&child.value)value=child.value;this.children.push(child);return child;},
    replaceChildren(){content='';value='';this.children=[];}};
}
function browser(sample,search='',render=false){
  const elements=new Map();
  const get=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
  const tree=get('lead-tree');
  for(const value of ['base','half-pot']){const option=element();option.value=value;tree.appendChild(option);}
  const document={getElementById:get,createElement:element,createDocumentFragment:element};
  const actual=vm.createContext({document,location:{search},URLSearchParams,atob,TextEncoder,TextDecoder,console,
    Response,DecompressionStream,crypto:crypto.webcrypto,testModel:sample.m,registry:frozen,
    fetch:async path=>fs.existsSync(path)?new Response(fs.readFileSync(path)):new Response('',{status:404})});
  vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),actual);
  vm.runInContext(fs.readFileSync('nl2_locked_medium.js','utf8'),actual);
  vm.runInContext(view,actual);
  const run=code=>vm.runInContext(code,actual);
  run('chosenModel=testModel;status=registry;');
  if(!render)run("selectVersion=()=>{if(!sourceCase(el('version').value))setMessage('尚無符合的 source');};");
  get('board').value=sample.m.certified_3_to_5_exact_flop_boards.indexOf(sample.old);
  return {actual,get,run};
}
function navigationFixture(){
  // Synthetic identities exercise selector wiring only. No case, mask or certification is constructed.
  const old={public_board:'navigation-A',actual_exact_action_line:'b33 c/',acting_seat:0,actual_spr:2,
    exact_node_actions:['x'],source_run_id:1,source_sha256:'a'.repeat(64),
    nl2_locked_variants:[{run_id:2,sha256:'b'.repeat(64),version:'exp_oop'}]};
  const alt={...old,source_run_id:3,source_sha256:'c'.repeat(64),
    nl2_locked_variants:[{run_id:4,sha256:'d'.repeat(64),version:'exp_oop'}]};
  const m={model_id:'navigation-only',certified_3_to_5_exact_flop_boards:[old]};
  const row={public_board:old.public_board,status:'BOTH_POSITIVE',board:alt};
  return {old,m,row};
}
function query(sample,sha,version='gto',tree='half-pot'){
  return '?'+new URLSearchParams({model:sample.m.model_id,board:sample.old.public_board,tree,sha,version});
}
async function navigate(sample){
  const {old,row}=sample;
  const alt=row.board;
  const other={...old,public_board:old.public_board+'-navigation-B',exact_node_actions:['x']};
  const m={...sample.m,certified_3_to_5_exact_flop_boards:[old,other]};
  function open(search,available=row){
    const page=browser({...sample,m},search);
    page.actual.nl2HalfPotLeads.load=async()=>available?[available]:[];
    if(!first)page.actual.nl2HalfPotLeads.match=(rows,model,b)=>rows.find(r=>r.public_board===b.public_board)||null;
    return page;
  }
  const p=open('');
  p.run('selectBoard()');await tick();
  assert.equal(p.get('lead-tree-label').hidden,false);
  assert.equal(p.run("sourceSha(sourceCase('gto'))"),old.source_sha256);
  assert.equal(p.run("sourceSha(sourceCase('exp_oop@0'))"),old.nl2_locked_variants[0].sha256);
  p.get('lead-tree').value='half-pot';p.run('selectLeadTree()');
  assert.equal(p.run("sourceSha(sourceCase('gto'))"),alt.source_sha256);
  assert.equal(p.run("sourceSha(sourceCase('exp_oop@0'))"),alt.nl2_locked_variants[0].sha256);
  assert.equal(p.run("sourceCase('exp_ip@0')"),null);
  assert.match(p.get('version').options[0].textContent,/條件 GTO/);
  p.get('lead-tree').value='base';p.run('selectLeadTree()');
  assert.equal(p.run("sourceSha(sourceCase('gto'))"),old.source_sha256);
  assert.equal(p.run('chosenBoard===originalBoard'),true);
  for(const t of ['base','half-pot']){
    const board=t==='base'?old:alt,chosen=board.nl2_locked_variants[0];
    const direct=open(query(sample,chosen.sha256,'exp_oop',t));
    direct.run('selectBoard()');await tick();
    assert.equal(direct.get('version').value,'exp_oop@0');
    assert.equal(direct.run("sourceSha(sourceCase(el('version').value))"),chosen.sha256);
  }
  const bad=open(query(sample,old.source_sha256));
  bad.run('selectBoard()');await tick();
  assert.equal(bad.get('version').value,'');
  assert.match(bad.get('details').textContent,/SHA/);
  const absent=open(query(sample,alt.source_sha256),null);
  absent.run('selectBoard()');await tick();
  assert.equal(absent.get('version').options.length,0);
  assert.equal(absent.get('lead-tree').lastElementChild.disabled,true);
  assert.match(absent.get('details').textContent,/尚無/);
  const fallback=open('',null);fallback.run('selectBoard()');await tick();
  assert.equal(fallback.get('lead-tree-label').hidden,true);
  assert.equal(fallback.run("sourceSha(sourceCase('gto'))"),old.source_sha256);

  // A slow response for A must never re-enable its comparison after switching to B.
  let resolveA;
  const stale=open('');
  stale.actual.nl2HalfPotLeads.load=()=>new Promise(resolve=>{resolveA=resolve;});
  stale.run('selectBoard()');
  stale.actual.nl2HalfPotLeads.load=async()=>[];
  stale.get('board').value='1';stale.run('selectBoard()');
  await tick();resolveA([row]);await tick();
  assert.equal(stale.run('chosenBoard.public_board'),other.public_board);
  assert.equal(stale.get('lead-tree-label').hidden,true);
  assert.equal(stale.run('leadResult'),null);
}

async function renderOriginalPair(sample){
  const {row,archive}=sample;
  for(const observation of [row.gto,row.exp_oop]){
    const p=browser(sample,query(sample,observation.source_sha256,observation.version),true);
    p.actual.nl2HalfPotLeads.load=async()=>records;
    p.run('selectBoard()');await tick();
    // fillVersions starts the asynchronous renderer; wait deterministically for the selected version.
    await p.run('selectVersion()');
    assert.equal(p.run('caseData?.source_sha256'),observation.source_sha256,p.get('details').textContent);
    assert.equal(p.run('chosenBoard.leadComparison.public_board'),row.public_board);
    assert.match(p.get('details').textContent,/半池領打/);
    assert.ok(p.get('details').textContent.includes(observation.source_sha256));
    assert.ok(p.get('locked-medium').textContent.includes(p.actual.nl2LockedMedium.describe(observation)));
    const lockText=p.get('lock-pool-source').textContent;
    const rates=Object.entries(row.exp_oop.checked_lock_patterns.marginal_targets)
      .filter(([pattern])=>row.exp_oop.applied_rust_rates[pattern]?.nodes);
    assert.ok(rates.length>0);
    for(const [pattern,target] of rates){
      assert.ok(lockText.includes(target.n.toLocaleString('zh-TW')+' 次池決策'));
      assert.ok(lockText.includes('在 '+row.exp_oop.applied_rust_rates[pattern].nodes+' 個節點'));
    }
    const source=archive.artifacts.flatMap(a=>a.cases).find(c=>c.source_sha256===observation.source_sha256&&c.version===observation.version);
    const {public_board:board,line,acting_seat:seat}=observation;
    const node=source.nodes.find(n=>n.public_board===board&&n.exact_node_line===line&&n.acting_seat===seat);
    const mask=Buffer.from(observation.compatible_action_mask_b64,'base64');
    const best=Buffer.from(node.strict_legal_best_ev_action_indices_b64,'base64');
    const expected=source.hands_by_seat[seat].flatMap((hand,i)=>mask[i]?[[hand,
      node.source_actions.filter((_,bit)=>mask[i]&(1<<bit)).join(' / '),
      best[i]!==255&&(mask[i]&(1<<best[i]))?node.source_actions[best[i]]:'原始未收錄']]:[]);
    const displayed=p.get('combo-rows').children[0]?.children.map(tr=>tr.children.map(td=>td.textContent));
    assert.deepEqual(displayed,expected);
  }
}
(async()=>{
  await navigate(first||navigationFixture());
  if(first)await renderOriginalPair(first);
  console.log('Verified '+positive+' authentic conditional pairs and '+others+' other matched results. '+
    (first?'Rendered GTO and NL2 hand rows.':'Exercised navigation with a selector-only fixture.'));
})().catch(e=>{console.error(e);process.exitCode=1;});
