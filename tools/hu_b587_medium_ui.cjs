const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const read=path=>JSON.parse(fs.readFileSync(path));
const report=read('data/nl2_hu_b583_frozen_rivers.json');
const recovery=read('data/nl2_hu_b587_raw_river_weights.json');
const models=read('data/nl2_hu_multiboard_status_current.json').records;
const el=()=>({children:[],textContent:'',appendChild(child){this.children.push(child);}});
const ctx=vm.createContext({document:{createElement:el},fetch:async path=>({ok:true,json:async()=>read(path)})});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),ctx);
const api=ctx.nl2HalfPotLeads;
for(const r of recovery.records){
  const m=models[r.model_id],b=m.certified_3_to_5_exact_flop_boards.find(b=>b.public_board===r.public_board);
  const expected=r.policy, source=expected.original.source_sha256;
  assert.equal(api.matchingFrozenPolicies(report,m,b,source)[0].status,'UNRESOLVED_ROUNDED_BOUNDARY');
  assert.equal(api.matchingFrozenPolicies(report,m,b,source,recovery)[0].raw_weights_sha256,expected.raw_weights_sha256);
  const mismatch=structuredClone(recovery);
  mismatch.records.find(v=>v.rank===r.rank).policy.prior_unresolved_output_sha256='0'.repeat(64);
  assert.throws(()=>api.matchingFrozenPolicies(report,m,b,source,mismatch));
  const slot=el();
  api.showFrozenPolicies(slot,m,b,source);
  setImmediate(()=>{
    const text=slot.children[0].children[0].children.map(x=>x.textContent).join('');
    assert.ok(text.includes(expected.original_node_count+' 個原始節點'));
    assert.ok(text.includes(expected.b50.eligible+' / '+expected.legal_combos));
    assert.ok(text.includes('64,272'));
    assert.ok(!text.includes('誤差超出'));
  });
}
