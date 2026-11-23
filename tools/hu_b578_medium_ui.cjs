const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const read = path => JSON.parse(fs.readFileSync(path));
const report = read('data/nl2_hu_b578_conditional_turns.json');
const registry = read('data/nl2_hu_multiboard_status_current.json');
const element = () => ({children: [], textContent: '', appendChild(child) { this.children.push(child); }});
const context = vm.createContext({document: {createElement: element}, fetch: async path => {
  assert.equal(path, 'data/nl2_hu_b578_conditional_turns.json');
  return {ok: true, json: async () => report};
}});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'), context);
const {matchRestrictedTurn, showBoard, showRestrictedTurn} = context.nl2HalfPotLeads;

for (const r of report.records) {
  const model = registry.records[r.model_id];
  const board = model.certified_3_to_5_exact_flop_boards.find(b => b.public_board === r.public_board);
  assert.equal(matchRestrictedTurn(r,model,board,r.original_locked_sha256),true);
  assert.equal(matchRestrictedTurn({...r,original_locked_run:r.source_run},model,board),false);
  assert.equal(matchRestrictedTurn(r,model,board,'unrelated'),false);
  const summary=element(), viewer=element();
  showBoard(summary,model,board);
  showRestrictedTurn(viewer,model,board,r.original_locked_sha256);
  setImmediate(() => {
    for (const container of [summary,viewer]) {
      const text=container.children[0].children[0].children.map(el=>el.textContent).join('');
      const phrases=r.rank===46?['1 / 1','Tc4c 100.0%','144,567','單挑玩家池']:['0 / 1','11,019'];
      for (const phrase of phrases) assert.ok(text.includes(phrase),phrase);
      assert.ok(text.includes('未達非極化研究門檻'));
      assert.ok(!text.includes('undefined'));
    }
  });
}
