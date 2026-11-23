const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const sourceFile = process.argv[2] || 'data/nl2_hu_b590_rank3_barrels.json';
const report = JSON.parse(fs.readFileSync(sourceFile));
const models = JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json')).records;
const element = () => ({children: [], appendChild(child) { this.children.push(child); }});
const ctx = vm.createContext({
  document: {createElement: element},
  fetch: async path => {
    if(['data/nl2_hu_b573_restricted_turn.json','data/nl2_hu_b578_conditional_turns.json','data/nl2_hu_b575_delayed_cbet.json'].includes(path))return {ok:true,json:async()=>JSON.parse(fs.readFileSync(path))};
    assert.equal(path,sourceFile);
    return {ok: true, json: async () => report};
  }
});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),ctx);
async function main() {
  for (const row of report.records) {
    const model = models[row.model_id], board = model.certified_3_to_5_exact_flop_boards.find(b => b.public_board === row.public_board);
    const ok = element(), wrong = element(), other = element();
    ctx.nl2HalfPotLeads.showBoard(ok,model,board);
    ctx.nl2HalfPotLeads.showMatchedBarrels(wrong,model,{...board,source_run_id: 0});
    ctx.nl2HalfPotLeads.showMatchedBarrels(other,model,board,'wrong-source');
    await new Promise(resolve => setImmediate(resolve));
    const content = ok.children[0].children[0].children.map(child => child.textContent).join('\n');
    assert.ok(content.includes(row.locked.half_pot.eligible+' / '+row.locked.legal_combos));
    const groups=ok.children[0].children[0].children.filter(x=>x.children.length===2);
    for(const [label,p] of [['原 GTO',row.gto],['實測回應鎖',row.locked]]){
      const group=groups.find(x=>x.children[0].textContent===label+' 的逐手半池頻率');
      const hands=Object.entries(p.eligible_hand_frequencies);
      assert.equal(Boolean(group),hands.length>0);
      for(const [hand,freq] of hands)assert.ok(group.children[1].textContent.includes(hand+' '+(100*freq).toFixed(1)+'%'));
    }
    if(model.solver_profile==='BTN_BB')assert.ok(content.includes('探測下注') && content.includes('位置內'));
    if(model.solver_profile==='BB3_BTN')assert.ok(content.includes('大盲三次加注') && content.includes('按鈕位') && content.includes('半池、滿池或全下'));
    if(model.solver_profile==='SB3_BTN')assert.ok(content.includes('三次加注') && content.includes('按鈕位') && content.includes('半池或全下'));
    if(model.solver_profile==='UTG_CO')assert.ok(content.includes('UTG'));
    if(row.line==='x x/')assert.ok(content.includes('同一組合併樣本頻率'));
    for (const r of row.rules) assert.ok(content.includes(r.n.toLocaleString('zh-TW')));
    assert.equal(wrong.children[0].children.length,0);
    assert.equal(other.children.length,0);
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
