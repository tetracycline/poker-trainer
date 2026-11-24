// Replay the real registry through the production loader and reject altered turn prices.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const args=process.argv.slice(2),option=name=>args.includes(name)?args[args.indexOf(name)+1]:null;
const registry=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json','utf8'));
const base=JSON.parse(fs.readFileSync('data/'+registry.base_registry,'utf8'));
const manifest=JSON.parse(fs.readFileSync('data/nl2_hu_verified_extensions.json','utf8'));
const source=fs.readFileSync(option('--loader')||'nl2_cert_registry.js','utf8');
const targets={
  'ln-opfr-r_model-1phsqr4':{spr:7.833,oldSpr:6.63,turn:'x b50 c',oldTurn:'x bet c'},
  'ln-ipfr-r_model-bqgbuq':{spr:8.614,oldSpr:7.323,turn:'b50 c',oldTurn:'bet c'}
};
const clone=value=>structuredClone(value),plain=value=>JSON.parse(JSON.stringify(value));
async function apply(script,value,initial=base){
  const ctx=vm.createContext({fetch:async()=>({ok:true,json:async()=>value})});
  vm.runInContext(script,ctx);
  return plain(await ctx.nl2ApplyVerifiedExtensions(clone(initial)));
}
async function run(){
  const oldManifest=clone(manifest),priced=clone(manifest);
  const oldRecords=clone(registry.records),newRecords=clone(registry.records);
  for(const[id,t]of Object.entries(targets)){
    oldManifest.trainer_route_contract.routes[id].streets[1]=t.oldTurn;
    delete oldManifest.trainer_route_contract.routes[id].priced_model_spr;
    priced.trainer_route_contract.routes[id].streets[1]=t.turn;
    priced.trainer_route_contract.routes[id].priced_model_spr=t.spr;
    oldRecords[id].assumed_model_node_spr=t.oldSpr;
    newRecords[id].assumed_model_node_spr=t.spr;
  }
  const oldResult=await apply(source,oldManifest),result=await apply(source,priced);
  assert.deepEqual(oldResult.records,oldRecords,'Existing flop-price behavior changed');
  assert.deepEqual(result.records,newRecords,'The loader must reproduce all392 records with only two price corrections');
  assert.equal(result.CERT_MULTIBOARD,registry.CERT_MULTIBOARD);
  assert.equal(result.APPROX,registry.APPROX);
  assert.deepEqual(result.exact_source_extensions,registry.exact_source_extensions);
  const protectedIds=Object.entries(registry.records).filter(([,r])=>r.label==='CERT-MULTIBOARD').map(([id])=>id);
  assert.ok(protectedIds.length>=150);
  for(const id of protectedIds)assert.deepEqual(result.records[id],registry.records[id],id);
  if(option('--legacy-loader')){
    const previous=fs.readFileSync(option('--legacy-loader'),'utf8');
    await assert.rejects(()=>apply(previous,priced),/來源尺寸或 SPR 不符/);
  }
  let rejected=0;
  async function reject(change,initial=base){
    const wrong=clone(priced);change(wrong);
    await assert.rejects(()=>apply(source,wrong,initial));rejected++;
  }
  for(const[id,t]of Object.entries(targets)){
    await reject(m=>{m.trainer_route_contract.routes[id].seat=1-m.trainer_route_contract.routes[id].seat;});
    await reject(m=>{m.trainer_route_contract.routes[id].streets[0]='b50 c';});
    await reject(m=>{m.trainer_route_contract.routes[id].streets[1]=t.turn.replace('b50','b75');});
    await reject(m=>{m.trainer_route_contract.routes[id].streets.pop();});
    await reject(m=>{m.trainer_route_contract.routes[id].priced_model_spr=t.spr+.001;});
    await reject(m=>{m.trainer_route_contract.routes[id].priced_model_spr=String(t.spr);});
    await reject(m=>{delete m.trainer_route_contract.routes[id].priced_model_spr;});
    for(const[field,value]of [['source_model_id','unknown-source'],['solver_profile','SB3_BTN'],['street',1],['abstract_action_history','你下注、對手跟|你過、對手過|']]){
      const wrongBase=clone(base);wrongBase.records[id][field]=value;
      await reject(()=>{},wrongBase);
    }
  }
  await reject(m=>{m.trainer_route_contract.routes['unknown-turn-price']=clone(m.trainer_route_contract.routes[Object.keys(targets)[0]]);});
  const flopId=Object.keys(priced.trainer_route_contract.routes).find(id=>!targets[id]&&priced.trainer_route_contract.routes[id].priced_model_spr!==undefined);
  assert.ok(flopId);
  await reject(m=>{m.trainer_route_contract.routes[flopId].streets[0]='x x';});
  await reject(m=>{m.trainer_route_contract.routes[flopId].priced_model_spr=0;});
  console.log(JSON.stringify({verified_records:392,preserved_certificates:protectedIds.length,exact_turn_prices:2,tampered_inputs_rejected:rejected,legacy_flop_price_gate_preserved:true}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
