const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const group=JSON.parse(fs.readFileSync(process.argv[2]||'data/solver_evidence/reverified/rank15.json'));
const script=fs.readFileSync('nl2-multiboard.js','utf8');
function element(tag){return {tag,textContent:'',children:[],appendChild(n){this.children.push(n);}};}
const env={document:{createElement:element},fmt:(n,p)=>n.toFixed(p)};
vm.createContext(env);
vm.runInContext(script.slice(script.indexOf('function renderedPolicyComparison('),script.indexOf('function fillCombos()')),env);
let count=0;
for(const board of group.boards){
 const evidence=group.pins.find(p=>p.public_board===board.public_board);
 assert.equal(evidence.original_GTO_SHA256,board.source_sha256);
 assert.equal(evidence.actual_NL2_SHA256,board.nl2_locked_variants[0].sha256);
 const node={public_board:board.public_board};
 assert.equal(env.renderedPolicyComparison(evidence,node,'unrelated-source'),null);
 for(const source of [evidence.original_GTO_SHA256,evidence.actual_NL2_SHA256]){
  const panel=env.renderedPolicyComparison(evidence,node,source);
  const rows=panel.children[1].children.slice(2);
  assert.equal(rows.length,evidence.rendered_decision_hands.length);
  for(const tr of rows){
   const [hand,display,gto,lock]=tr.children.map(td=>td.textContent);
   const expected=evidence.rendered_decision_hands.find(r=>r.hand===hand); assert.equal(display,expected.displayed_suggestion);
   for(const [cell,policy] of [[gto,expected.gto],[lock,expected.nl2]]){
    assert.equal(policy.action_order.length,Object.keys(policy.strategy).length);
    assert.ok(Math.abs(Object.values(policy.strategy).reduce((a,b)=>a+b,0)-1)<.002);
    assert.ok(policy.accepted_mask>0 && policy.accepted_mask<(1<<policy.action_order.length));
    for(const [i,act] of policy.action_order.entries())assert.ok(cell.includes(act+' '+(100*policy.strategy[act]).toFixed(2)+'%'+((policy.accepted_mask&(1<<i))?' ✓':'')));
   }
   count++;
  }
 }
}
assert.ok(count>=6);
console.log('Verified both solver policies and their independent action masks on every ranked river hand.');
