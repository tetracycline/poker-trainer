const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const report=JSON.parse(fs.readFileSync('data/nl2_hu_b475_verified_lock_scope.json'));
const registry=JSON.parse(fs.readFileSync(process.argv[2]));
const context=vm.createContext({});
vm.runInContext(fs.readFileSync('nl2_pool_rate_scope.js','utf8'),context);
const {select}=context.nl2PoolRateScope;
const seen=new Set(),checked=new Set(),confirmed=new Set(),models=new Set(),boards=new Set();
let refs=0;
for(const [id,model] of Object.entries(registry.records)){
  if(model.label!=='CERT-MULTIBOARD') continue;
  for(const board of model.certified_3_to_5_exact_flop_boards){
    for(const lock of board.nl2_locked_variants){
      const key=lock.run_id+'/'+lock.sha256;
      seen.add(key);
      const row=select(report,model,board,lock);
      if(!row)continue;
      checked.add(key);
      assert.equal(select(report,model,board,{...lock,sha256:'0'.repeat(64)}),null);
      assert.equal(select(report,model,{...board,turn:'--'},lock),null);
      if(row.scope==='CONFIRMED'){
        confirmed.add(key);refs++;models.add(id);boards.add([id,board.public_board,board.actual_exact_action_line,board.acting_seat].join('|'));
        assert.ok(row.evidence.length>0);
        for(const e of row.evidence){
          assert.ok(e.first_matching_source_n>0 && e.first_matching_source_street===1);
          assert.ok(Object.values(e.observed_later_street_node_counts).some(n=>n>0));
        }
      } else {assert.equal(row.scope,'CHECKED_WITHOUT_CONFIRMATION');assert.equal(row.evidence.length,0);}
    }
  }
}
assert.deepEqual([seen.size,checked.size,confirmed.size,refs,boards.size,models.size],[361,195,121,261,247,103]);
console.log('PASS historical lock evidence and unresolved scope for all 361 pinned source identities');

class Element{
  constructor(){this.textContent='';this.children=[];}
  appendChild(child){this.children.push(child);return child;}
  content(){return this.textContent+' '+this.children.map(c=>c.content()).join(' ');}
}
context.document={createElement:()=>new Element()};
context.fetch=async()=>({ok:true,json:async()=>report});
(async()=>{
  const model=registry.records['ln-iso-lmp_t_model-19hfq8v'];
  const board=model.certified_3_to_5_exact_flop_boards.find(b=>b.public_board==='2d4h4s8s');
  const lock=board.nl2_locked_variants[0], parent=new Element();
  await context.nl2PoolRateScope.show(parent,model,board,[lock]);
  assert.ok(parent.content().includes('已核實跨街沿用翻牌頻率'));
  assert.ok(parent.content().includes('275,923')&&parent.content().includes('64,272'));
  const unknown=new Element();
  await context.nl2PoolRateScope.show(unknown,model,board,[{...lock,run_id:0}]);
  assert.ok(unknown.content().includes('本輪未核對此來源'));
  console.log('PASS source-bound hand sample disclosure in browser');
})().catch(err=>{console.error(err);process.exitCode=1;});
