const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
const read=path=>JSON.parse(fs.readFileSync(path));
const report=read('data/nl2_hu_b583_frozen_rivers.json');
const models=read('data/nl2_hu_multiboard_status_current.json').records;
const element=()=>({children:[],textContent:'',appendChild(child){this.children.push(child);}});
const ctx=vm.createContext({document:{createElement:element},fetch:async path=>{
  if(path==='data/nl2_hu_b587_raw_river_weights.json')return {ok:true,json:async()=>({schema:'NL2_HU_B587_RAW_RIVER_RANGE_RECOVERY_V1',records:[]})};
  assert.equal(path,'data/nl2_hu_b583_frozen_rivers.json');
  return {ok:true,json:async()=>report};
}});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),ctx);
for (const row of report.records) {
  const m=models[row.model_id], b=m.certified_3_to_5_exact_flop_boards.find(b=>b.public_board===row.public_board);
  const api=ctx.nl2HalfPotLeads;
  assert.equal(api.matchingFrozenPolicies(report,m,b).length,row.policies.length);
  assert.equal(api.matchingFrozenPolicies(report,m,{...b,actual_exact_action_line:'bad'}).length,0);
  for(const p of row.policies){
    const slot=element();
    const source=p.original.source_sha256;
    assert.equal(api.matchingFrozenPolicies(report,m,b,source).length,1);
    api.showFrozenPolicies(slot,m,b,source);
    setImmediate(()=>{
      const text=slot.children[0].children[0].children.map(x=>x.textContent).join('');
      if(p.status==='VERIFIED'){
        assert.ok(text.includes(p.b50.eligible+' / '+p.legal_combos));
        if(p.applied_reply)assert.ok(text.includes('64,272')&&text.includes('53.1%'));
      }else{
        assert.ok(text.includes('誤差超出'));
        assert.ok(!text.includes('組手牌可以下半池'));
      }
    });
  }
}
