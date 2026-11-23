const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const read=f=>JSON.parse(fs.readFileSync(f));
const reports=read('data/nl2_hu_b575_delayed_cbet.json');
const model=read('data/nl2_hu_multiboard_status_current.json').records['ln-opfr-t_model-1ocorr7'];
const el=()=>({children:[],textContent:'',appendChild(x){this.children.push(x);}});
const ctx=vm.createContext({document:{createElement:el},fetch:async()=>({ok:true,json:async()=>reports})});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),ctx);
const {matchRestrictedTurn,showRestrictedTurn}=ctx.nl2HalfPotLeads;
for(const r of reports.records){
 const board=model.certified_3_to_5_exact_flop_boards.find(b=>b.public_board===r.public_board),root=el();
 assert.equal(matchRestrictedTurn(r,model,board,r.original_locked_sha256),true);
 assert.equal(matchRestrictedTurn(r,model,{...board,nl2_locked_variants:[]}),false);
 assert.equal(matchRestrictedTurn(r,model,board,'unrelated'),false);
 showRestrictedTurn(root,model,board,board.source_sha256);
 setImmediate(()=>{
   const text=root.children[0].children[0].children.map(e=>e.textContent).join('');
   assert.ok(text.includes('26,780') && text.includes('各尺寸'));
   assert.equal(text.includes('原 GTO 翻牌範圍'),r.policies.exp_oop.parent_version==='gto');
   for(const p of Object.values(r.policies)){
     assert.ok(text.includes(p.half_pot.eligible+' / '+p.legal_combos));
     assert.ok(p.half_pot_reply_pairs>0);
   }
 });
}
