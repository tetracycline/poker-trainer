const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
const {createHash,webcrypto}=require('node:crypto');
const helper=fs.readFileSync('nl2_locked_medium.js','utf8');
const original=JSON.parse(fs.readFileSync('data/nl2_hu_b485_locked_medium.json'));
const [key,row]=Object.entries(original.references).find(([,r])=>r.strict_legal_combos&&r.subgame_applied_rust_lock_nodes===0&&r.gto);
const [mid,board,line,seat]=JSON.parse(key), gto=row.gto;
const gkey=JSON.stringify([mid,board,line,seat,gto.source_run_id,gto.source_sha256]);
const earlier={...row};
for(const f of ['root_applied_rust_lock_nodes','subgame_applied_rust_lock_nodes','gto'])delete earlier[f];
async function load(extra,modify=()=>{},base={references:{[key]:earlier}}){
  const contents=new Map(), reports=[];
  for(const [number,data] of [[483,base],[490,extra]]){
    const path='data/nl2_hu_b'+number+'_locked_medium.json', schema='NL2_HU_B'+number+'_ORIGINAL_LOCKED_MEDIUM_V1';
    const bytes=JSON.stringify({schema,...data});
    reports.push({path,schema,sha256:createHash('sha256').update(bytes).digest('hex')});
    contents.set(path,bytes);
  }
  modify(reports);
  const ctx=vm.createContext({crypto:webcrypto,atob,TextDecoder,TextEncoder,fetch:async path=>{
    if(path==='data/nl2_hu_verified_extensions.json')return Response.json({schema:'NL2_EXACT_VERIFIED_EXTENSIONS_V1',locked_medium_reports:reports});
    assert.ok(contents.has(path),path);return new Response(contents.get(path));
  }});
  vm.runInContext(helper,ctx);
  const audit=ctx.nl2LockedMedium;
  return [audit,await audit.load()];
}
async function main(){
  const model={model_id:mid,family:row.family,solver_profile:row.spot};
  const lock={version:row.version,run_id:row.source_run_id,sha256:row.source_sha256};
  const b={public_board:board,actual_exact_action_line:line,acting_seat:seat,flop:row.flop,turn:row.turn,
    source_run_id:gto.source_run_id,source_sha256:gto.source_sha256,nl2_locked_variants:[lock]};
  const refs={references:{[key]:row},gto_references:{[gkey]:gto}};
  for(const r of [refs,{references:refs.references},{references:{[key]:earlier},gto_references:refs.gto_references}]){
    const [audit,combined]=await load(r);
    assert.equal(Object.keys(combined.references).length,1);
    assert.equal(Object.keys(combined.gto_references).length,1);
    const found=audit.lookup(combined,model,b,lock);
    assert.equal(found.compatible_action_mask_b64,row.compatible_action_mask_b64);
    if(r.references[key]===row)assert.match(audit.describe(found),/翻牌父樹 [1-9]\d* 個、轉河子樹 0 個/);
    assert.equal(audit.lookup(combined,model,b,gto).compatible_action_mask_b64,gto.compatible_action_mask_b64);
  }
  await assert.rejects(load({references:{[key]:{...row,compatible_hole_card_pairs:row.compatible_hole_card_pairs+1}}}),/相衝/);
  await assert.rejects(load({references:{[gkey]:gto}}),/座位/);
  await assert.rejects(load({references:{},gto_references:{[key]:row}}),/座位/);
  await assert.rejects(load(refs,descs=>{descs[1].path='../unregistered.json';}),/路徑/);
  await assert.rejects(load(refs,descs=>{descs[1].sha256='0'.repeat(64);}),/SHA/);
  const pending={references:{},unresolved:{[key]:{version:row.version,reason:'ORIGINAL_RUST_SUBGAME_NOT_PUBLISHED',spot:row.spot}}};
  const [av,missing]=await load(pending,()=>{},{references:{}});
  const u=av.lookup(missing,model,b,lock);
  assert.equal(u.status,'UNRESOLVED_JOINT_REACH');
  assert.match(av.describe(u),/仍待核對/);
  assert.equal(u.strict_legal_combos,undefined);
  const node={board:row.public_board,line:row.line,acting_seat:row.acting_seat};
  const bound=await av.bindCase(missing,{source_run_id:row.source_run_id,source_sha256:row.source_sha256,
    version:row.version,spot:row.spot,nodes:[node]});
  assert.equal(bound.get(node).row.status,u.status);assert.equal(bound.get(node).mask,null);
  const dom=new Map();
  const get=id=>{if(!dom.has(id))dom.set(id,{textContent:'',value:'0',children:[],replaceChildren(){this.children=[];}});
    return dom.get(id);};
  const page=vm.createContext({nl2LockedMedium:av,by:get,el:get,game:{nodes:[node]},selN:{value:'0'},
    current:null,jointNodes:bound,jointFor:n=>bound.get(n),caseData:{nodes:[node]},
    setMessage:message=>{get('details').textContent=message;get('combo-rows').replaceChildren();}});
  const cfr=fs.readFileSync('nl2-cfr.js','utf8');
  const multi=fs.readFileSync('nl2-multiboard.js','utf8');
  vm.runInContext(cfr.slice(cfr.indexOf('function selectNode(){'),cfr.indexOf('for(const [el,cb]')),page);
  vm.runInContext('selectNode();renderCombos();',page);
  assert.match(get('details').textContent,/仍待核對/);assert.equal(get('combos').children.length,0);
  Object.assign(page,{chosenBoard:b});
  vm.runInContext(multi.slice(multi.indexOf('function selectNode(){'),multi.indexOf('function fillCombos(){')),page);
  vm.runInContext('selectNode();',page);
  assert.match(get('details').textContent,/仍待核對/);assert.equal(get('combo-rows').children.length,0);
  assert.doesNotMatch(get('details').textContent,/為 0/);
  const [ar,resolved]=await load(pending);
  assert.equal(ar.lookup(resolved,model,b,lock).status,row.status);
  console.log('Verified named report SHA, safe paths, source roles, incremental GTO and displayed root-only lock scope.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
