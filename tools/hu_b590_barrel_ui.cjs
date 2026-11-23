const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const report = JSON.parse(fs.readFileSync('data/nl2_hu_b590_rank3_barrels.json'));
const models = JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json')).records;
const element = () => ({children: [], appendChild(child) { this.children.push(child); }});
const ctx = vm.createContext({
  document: {createElement: element},
  fetch: async path => {
    assert.equal(path,'data/nl2_hu_b590_rank3_barrels.json');
    return {ok: true, json: async () => report};
  }
});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),ctx);
async function main() {
  for (const row of report.records) {
    const model = models[row.model_id], board = model.certified_3_to_5_exact_flop_boards.find(b => b.public_board === row.public_board);
    const ok = element(), wrong = element(), other = element();
    ctx.nl2HalfPotLeads.showBoard(ok,model,board);
    ctx.nl2HalfPotLeads.showRestrictedTurn(wrong,model,{...board,source_run_id: 0});
    ctx.nl2HalfPotLeads.showRestrictedTurn(other,model,board,'wrong-source');
    await new Promise(resolve => setImmediate(resolve));
    const content = ok.children[0].children[0].children.map(child => child.textContent).join('\n');
    assert.ok(content.includes(row.locked.half_pot.eligible+' / '+row.locked.legal_combos));
    for (const r of row.rules) assert.ok(content.includes(r.n.toLocaleString('zh-TW')));
    assert.equal(wrong.children[0].children.length,0);
    assert.equal(other.children.length,0);
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
