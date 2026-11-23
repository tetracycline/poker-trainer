const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const read=file=>JSON.parse(fs.readFileSync(file));
const report=read('data/nl2_hu_b573_restricted_turn.json');
const registry=read('data/nl2_hu_multiboard_status_current.json');
const model=registry.records[report.model_id],board=model.certified_3_to_5_exact_flop_boards.find(b=>b.public_board===report.public_board);
const element=()=>({textContent:'',children:[],appendChild(child){this.children.push(child);}});
const ctx=vm.createContext({document:{createElement:element},fetch:async()=>({ok:true,json:async()=>report})});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),ctx);
const {matchRestrictedTurn,showBoard,showRestrictedTurn}=ctx.nl2HalfPotLeads;
assert.equal(matchRestrictedTurn(report,model,board,'wrong'),false);
assert.equal(matchRestrictedTurn(report,model,{...board,nl2_locked_variants:[]}),false);
for(const p of Object.values(report.policies))assert.equal(matchRestrictedTurn(report,model,board,p.parent.source_sha256),true);
const summary=element(),viewer=element();
showBoard(summary,model,board);showRestrictedTurn(viewer,model,board,board.source_sha256);
setImmediate(()=>{
 for(const parent of [summary,viewer]){
   const text=parent.children[0].children[0].children.map(el=>el.textContent).join('');
   for(const value of ['24 / 33','8 / 345','12 組屬中段勝率','11,019','31.9%','11.6%'])assert.ok(text.includes(value),value);
 }
 console.log('Verified both ranked turn views against the original and conditional source policies.');
});
