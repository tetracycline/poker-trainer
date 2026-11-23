// Exercise both real fetch chains, the source resolver and exact actor-node combo masks.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = 'data/nl2_hu_multiboard_status_v52_b463_rank45.json';
const registry = JSON.parse(fs.readFileSync(path));
const shared = fs.readFileSync('nl2_cert_registry.js', 'utf8');
const viewer = fs.readFileSync('nl2-multiboard.js', 'utf8');

async function main() {
  for (const file of ['nl2_hu_multiboard_ui.js', 'nl2-multiboard.js']) {
    const code = fs.readFileSync(file, 'utf8');
    const fetcher = code.slice(code.indexOf('function fetchCertifiedRegistry(){'),
      code.lastIndexOf('\nfetchCertifiedRegistry()'));
    assert.ok(fetcher.endsWith('}\n') || fetcher.trimEnd().endsWith('}'));
    const visits = [];
    const runtime = vm.createContext({fetch: async url => {
      visits.push(url);
      return { ok: true, json: async () => registry };
    }});
    vm.runInContext(shared + '\n' + fetcher, runtime);
    assert.equal(await vm.runInContext('fetchCertifiedRegistry()', runtime), registry);
    assert.equal(visits.at(-1), path);
    for (const field of ['GTO_strict_combos','NL2_strict_combos','actual_NL2_SHA256']) {
      const corrupt = structuredClone(registry);
      corrupt.B463_rank45_three_true_original_GTO_NL2_OOP_flops.pins[0][field] = 0;
      assert.throws(() => runtime.nl2ValidateRank45(corrupt));
    }
  }
  const start = viewer.indexOf('async function getProof(run){');
  const stop = viewer.indexOf('let versionRequest=', start);
  assert.ok(start > 0 && stop > start);
  const runtime = vm.createContext({
    status: registry, proofCache: {}, Response, DecompressionStream,
    fetch: async url => new Response(fs.readFileSync(url)),
    sourceRun: s => s.source_run_id ?? s.run_id, sourceSha: s => s.source_sha256 ?? s.sha256
  });
  vm.runInContext(viewer.slice(start, stop), runtime);
  const ranks = [32,45,107,166,214,219];
  let checked = 0;
  for (const rank of ranks) {
    const model = Object.values(registry.records).find(m => m.frequency_rank === rank);
    runtime.chosenModel = model;
    for (const board of model.certified_3_to_5_exact_flop_boards) {
      runtime.chosenBoard = board;
      const gto = {version:'gto', source_run_id:board.source_run_id, source_sha256:board.source_sha256};
      for (const source of [gto, ...board.nl2_locked_variants]) {
        const proof = await runtime.getProof(runtime.sourceRun(source));
        assert.ok(proof, 'missing proof rank '+rank+' '+board.flop);
        const actual = runtime.verifiedCase(source, proof);
        const node = actual.nodes.find(n => n.public_board === board.public_board &&
          n.exact_node_line === board.actual_exact_action_line && n.acting_seat === board.acting_seat);
        assert.ok(node?.strictly_reachable_combos > 0);
        const hands = actual.hands_by_seat[board.acting_seat];
        const masks = Buffer.from(node.strictly_reachable_masks_b64,'base64');
        assert.equal(masks.length,hands.length);
        assert.equal(masks.filter(byte => byte !== 0).length,node.strictly_reachable_combos);
        assert.throws(() => runtime.verifiedCase({...source,source_sha256:'0'.repeat(64)},proof));
        checked++;
      }
    }
  }
  console.log('PASS B463 V52 NL2 browser loaders and '+checked+' exact GTO/EXP sources');
}
main().catch(err => { console.error(err); process.exitCode = 1; });
