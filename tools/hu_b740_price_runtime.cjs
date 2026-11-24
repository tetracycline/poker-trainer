// Replay the exact five raise-call routes and reject altered source geometry.
const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const status=read('data/nl2_hu_multiboard_status_current.json'), base=read('data/'+status.base_registry);
const manifest=read('data/nl2_hu_verified_extensions.json'), report=read('data/nl2_hu_b740_raise_call_prices.json');
const source=fs.readFileSync('nl2_cert_registry.js','utf8');
async function apply(m,b=base){
  const ctx=vm.createContext({fetch:async()=>({ok:true,json:async()=>m})});
  vm.runInContext(source,ctx);
  return JSON.parse(JSON.stringify(await ctx.nl2ApplyVerifiedExtensions(structuredClone(b))));
}
async function main(){
  const valid=await apply(manifest);
  assert.deepEqual(valid.records,status.records);
  assert.equal(valid.CERT_MULTIBOARD,status.CERT_MULTIBOARD);
  let rejected=0;
  for(const [id,target] of Object.entries(report.outcomes)){
    assert.equal(valid.records[id].assumed_model_node_spr,target.spr);
    assert.equal(valid.records[id].label,'APPROX');
    for(const change of [r=>{r.seat=1;},r=>{r.priced_model_spr+=.001;},r=>{delete r.priced_model_spr;},
      r=>{r.streets[0]='b33 r c';},r=>{r.streets[0]='b50 r75 c';},r=>{r.streets[0]='b50 r c x';},
      r=>{delete r.priced_model_spr;r.streets[0]='b75 r c';},r=>{r.streets[1]='x bet c';}]){
      const bad=structuredClone(manifest);change(bad.trainer_route_contract.routes[id]);
      await assert.rejects(()=>apply(bad),/SPR|行動線/);rejected++;
    }
    for(const [field,value] of [['solver_profile','ISO_BTN_CO'],['street',0],['abstract_action_history','你過|'],['source_model_id','unknown']]){
      const b=structuredClone(base);b.records[id][field]=value;
      await assert.rejects(()=>apply(manifest,b),/SPR|行動線/);rejected++;
    }
  }
  const old=structuredClone(manifest),expected=structuredClone(status.records);
  for(const [id,t] of Object.entries(report.outcomes)){
    const r=old.trainer_route_contract.routes[id];r.streets[0]='bet raise c';delete r.priced_model_spr;
    expected[id].assumed_model_node_spr=t.previous_spr;
  }
  assert.deepEqual((await apply(old)).records,expected);
  console.log(JSON.stringify({records:392,exact_raise_call_prices:5,preserved_certificates:status.CERT_MULTIBOARD,tampered_routes_rejected:rejected}));
}
main().catch(err=>{console.error(err);process.exitCode=1;});

