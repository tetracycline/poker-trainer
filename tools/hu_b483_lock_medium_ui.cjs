const fs=require('node:fs'), zlib=require('node:zlib'), vm=require('node:vm'), assert=require('node:assert/strict');
const read=p=>JSON.parse(fs.readFileSync(p));
const report=read(process.argv[2]||'data/nl2_hu_b483_locked_medium.json');
const registry=read('data/'+report.registry);
const cases=new Map(), inputs=[];
const viewer=fs.readFileSync('nl2-multiboard.js','utf8');
const helper=fs.readFileSync('nl2_locked_medium.js','utf8');
function element(){
  return {children:[],value:'',textContent:'',checked:true,appendChild(v){this.children.push(v);return v;},
    replaceChildren(){this.children=[];this.textContent='';},get options(){return this.children;},addEventListener(){}};
}
const dom=new Map(), get=id=>{if(!dom.has(id))dom.set(id,element());return dom.get(id);};
const document={getElementById:get,createElement:element,createDocumentFragment:element,
  createTextNode:s=>({textContent:s})};
const ctx=vm.createContext({document,console,location:{search:''},URLSearchParams,atob,TextEncoder,DecompressionStream,Response,
  crypto:require('node:crypto').webcrypto,fetch:async path=>{
    if(path==='data/nl2_hu_b483_locked_medium.json')return {ok:true,json:async()=>report};
    return new Response(fs.readFileSync(path));
  }});
vm.runInContext(helper,ctx);
vm.runInContext(viewer.slice(viewer.indexOf("const el="),viewer.indexOf("el('model').addEventListener")),ctx);
function original(row){
  if(!cases.has(row.source_run_id)){
    const code=Object.entries(registry.independently_verified_completed_batches).find(([,b])=>b.run_id===row.source_run_id)[0];
    const path='data/solver_evidence/NL2_MULTIBOARD_'+code+'.json.gz';
    cases.set(row.source_run_id,JSON.parse(zlib.gunzipSync(fs.readFileSync(path))).artifacts.flatMap(a=>a.cases));
  }
  return cases.get(row.source_run_id).find(c=>c.source_sha256===row.source_sha256&&c.version===row.version&&c.spot===row.spot);
}
async function main(){
  const audit=ctx.nl2LockedMedium;
  const counts={POSITIVE_JOINT_REACH:0,ZERO_JOINT_REACH:0};
  for(const [key,row] of Object.entries(report.references)){
    const [id,board,line,seat,run,sha]=JSON.parse(key),model=registry.records[id];
    const b=model.certified_3_to_5_exact_flop_boards.find(x=>x.public_board===board&&x.actual_exact_action_line===line&&x.acting_seat===seat);
    const i=b.nl2_locked_variants.findIndex(v=>v.run_id===run&&v.sha256===sha), lock=b.nl2_locked_variants[i];
    assert.equal(audit.lookup(report,model,b,lock),row);counts[row.status]++;
    assert.equal(audit.lookup(report,model,b,{...lock,sha256:'0'.repeat(64)}),null);
    const g={version:'gto',source_run_id:b.source_run_id,source_sha256:b.source_sha256};
    if(row.gto)assert.equal(audit.lookup(report,model,b,g).source_sha256,row.gto.source_sha256);
    for(const actualRow of [row,row.gto].filter(Boolean)){
      const actual=original(actualRow);
      assert.ok(actual);
      const node=actual.nodes.find(n=>n.public_board===board&&n.exact_node_line===line&&n.acting_seat===seat);
      if(node){
        await audit.bindMask(actualRow,actual,node);
        if(actualRow===row)inputs.push({model,b,i,row,actual,node});
      }else assert.equal(actualRow.status,'ZERO_JOINT_REACH');
    }
  }
  assert.equal(counts.POSITIVE_JOINT_REACH,report.totals.lock_positive);
  assert.equal(counts.ZERO_JOINT_REACH,report.totals.lock_zero);
  const positive=inputs.find(x=>x.row.strict_legal_combos>0&&x.row.strict_legal_combos<x.node.strictly_reachable_combos);
  const zero=inputs.find(x=>x.row.status==='ZERO_JOINT_REACH');
  for(const input of [positive,zero]){
    assert.ok(input);
    Object.assign(ctx,{modelForTest:input.model,boardForTest:input.b,registryForTest:registry});
    vm.runInContext('chosenModel=modelForTest; chosenBoard=boardForTest; status=registryForTest;',ctx);
    get('version').value=input.row.version+'@'+input.i;
    await vm.runInContext('selectVersion()',ctx);
    assert.match(get('locked-medium').textContent,/雙方可達/);
    if(input===zero){
      assert.equal(get('combo-rows').children.length,0);
      assert.match(get('details').textContent,/沒有相容/);
    }else{
      const rows=get('combo-rows').children[0]?.children;
      assert.equal(rows?.length,input.row.strict_legal_combos,get('details').textContent);
      const mask=Buffer.from(input.row.compatible_action_mask_b64,'base64');
      const expected=input.actual.hands_by_seat[input.row.acting_seat].filter((_,i)=>mask[i]);
      assert.deepEqual(rows.map(r=>r.children[0].textContent),expected);
      await assert.rejects(()=>audit.bindMask({...input.row,source_hand_order_sha256:'bad'},input.actual,input.node));
      const altered={...input.node,source_actions:[...input.node.source_actions].reverse()};
      await assert.rejects(()=>audit.bindMask(input.row,input.actual,altered));
    }
    const box=element();audit.showBoard(box,input.model,input.b);
    await new Promise(resolve=>setImmediate(resolve));
    const lines=box.children[0].children.flatMap(n=>[n,...n.children]).map(n=>n.textContent).join(' ');
    assert.ok(lines.includes(audit.describe(input.row)));
  }
  const statuses=new Set(Object.values(report.references).filter(x=>x.b50).map(x=>x.b50.status));
  for(const status of statuses){
    const sample=Object.values(report.references).find(x=>x.b50?.status===status);
    assert.doesNotMatch(audit.describe(sample),/undefined/);
  }
  for(const page of ['nl2.html','nl2-multiboard.html'])assert.ok(fs.readFileSync(page,'utf8').includes('src="nl2_locked_medium.js'));
  console.log('PASS exact locked/GTO mask identities, real board/version views, EV rows and zero-deal rejection');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
