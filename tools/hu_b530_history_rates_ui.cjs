const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor() { this.children = []; this.textContent = ''; }
  appendChild(child) { this.children.push(child); return child; }
  text() { return [this.textContent, ...this.children.map(child => child.text())].join(' '); }
}

async function main() {
  const report = JSON.parse(fs.readFileSync('data/nl2_hu_b475_verified_lock_scope.json'));
  const context = vm.createContext({
    document: {createElement: () => new Element()},
    fetch: async () => ({ok: true, json: async () => report})
  });
  vm.runInContext(fs.readFileSync('nl2_pool_rate_scope.js', 'utf8'), context);
  const registry = JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json'));
  let decisions = 0, bets = 0, facing = 0, assumed = 0;
  for (const model of Object.values(registry.records)) {
    for (const board of model.certified_3_to_5_exact_flop_boards || []) {
      for (const lock of board.nl2_locked_variants.filter(v => v.viewer_archive_code?.startsWith('B530_'))) {
        const element = new Element();
        await context.nl2PoolRateScope.show(element, model, board, [lock]);
        const message = element.text();
        for (const r of lock.applied_street_rates) {
          assert.ok(message.includes(r.n.toLocaleString('zh-TW')));
          if (r.opportunity === 'BET') {
            assert.ok(message.includes(r.size_proxy) && message.includes('實測下注'));
            ++bets;
          } else if (r.opportunity === 'FACING_BET') {
            assert.ok(message.includes('實測棄／加 '+r.target_fold_pct.toFixed(1)+'%／'+r.target_raise_pct.toFixed(1)+'%'));
            ++facing;
          }
        }
        assert.ok(!message.includes('istory%'));
        if (lock.turn_checked_to_bet_assumption) {
          assert.ok(message.includes('45% 假設'));
          ++assumed;
        }
        ++decisions;
      }
    }
  }
  assert.equal(decisions, 49);
  assert.ok(bets > 0 && facing > 0 && assumed > 0);
  console.log('Verified 49 source-bound turn and river disclosures, including sizing proxies and assumptions.');
}
main().catch(error => {console.error(error); process.exitCode = 1;});
