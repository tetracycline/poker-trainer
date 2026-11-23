// Reaching the frozen V48 registry must still require its original source pins.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const file = 'data/nl2_hu_multiboard_status_v48_b390_rank107.json';
const status = JSON.parse(fs.readFileSync(file));
async function replay(script, data) {
  const source = fs.readFileSync(script, 'utf8');
  const start = source.indexOf('function fetchCertifiedRegistry(){');
  const end = source.lastIndexOf('\nfetchCertifiedRegistry()');
  assert.ok(start > 0 && end > start);
  let found = false;
  const context = vm.createContext({fetch: async path => {
    if (path !== file) return {ok:false, status:404};
    found = true;
    return {ok:true, json:async () => data};
  }});
  vm.runInContext(source.slice(start,end), context);
  try { return await context.fetchCertifiedRegistry(); }
  finally { assert.ok(found, script+' never fetched the V48 rank107 registry'); }
}
(async () => {
  for (const script of ['nl2_hu_multiboard_ui.js', 'nl2-multiboard.js']) {
    assert.equal(await replay(script,status), status);
    const forged = structuredClone(status);
    forged.B390_rank107_three_true_original_GTO_NL2_IP_flops.pins[0].GTO_strict_combos = 0;
    await assert.rejects(replay(script,forged));
  }
  console.log('PASS actual V48 fallback and zero-reach rejection in both views');
})().catch(e => {console.error(e); process.exitCode=1;});
