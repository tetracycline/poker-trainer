const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const zlib = require('node:zlib');
const registry = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const base = JSON.parse(fs.readFileSync('data/'+registry.base_registry, 'utf8'));
const manifest = JSON.parse(fs.readFileSync('data/nl2_hu_verified_extensions.json', 'utf8'));
const source = fs.readFileSync('nl2_cert_registry.js', 'utf8');
async function run() {
  const ctx=vm.createContext({fetch:async () => ({ok:true,json:async()=>manifest})});
  vm.runInContext(source,ctx);
  const result=await ctx.nl2ApplyVerifiedExtensions(base);
  assert.equal(result.CERT_MULTIBOARD,registry.CERT_MULTIBOARD);
  assert.equal(result.APPROX,registry.APPROX);
  for(const id of Object.keys(manifest.board_reach_updates || {})){
    const browserRecord=JSON.parse(JSON.stringify(result.records[id]));
    assert.deepEqual(browserRecord,registry.records[id],id);
    if(browserRecord.label==='APPROX'){
      assert.ok(browserRecord.remaining_exact_board_evidence.length<3);
      assert.equal(browserRecord.certified_3_to_5_exact_flop_boards.length,0);
    }
  }
  const viewer=fs.readFileSync('nl2-multiboard.js','utf8');
  const proof=viewer.slice(viewer.indexOf('async function getProof(run){'),viewer.indexOf('function verifiedCase('));
  const cases=manifest.models.concat(manifest.reverified_models || []);
  // Exercise both genuine historical sources even before a third rank146 board qualifies.
  if (!cases.some(e=>e.rank===146)) {
    cases.push(JSON.parse(fs.readFileSync('data/nl2_hu_b471_rank146_original_pairs.json','utf8')));
  }
  for (const item of cases) {
    const model=result.records[item.model_id];
    const viewStatus={...result,exact_source_extensions:{...result.exact_source_extensions,[item.model_id]:item.pins}};
    for(const board of item.boards) {
      const pin=item.pins.find(p=>p.public_board===board.public_board);
      Object.assign(ctx,{chosenModel:model,chosenBoard:board,status:viewStatus,proofCache:{}, Response, DecompressionStream, crypto:require("node:crypto").webcrypto});
      vm.runInContext(proof,ctx);
      for(const run of new Set([board.source_run_id, ...board.nl2_locked_variants.map(v=>v.run_id)])) {
        const code=run===board.source_run_id ? pin.viewer_archive_code : pin.locked_viewer_archive_code;
        const url='data/solver_evidence/NL2_MULTIBOARD_'+code+'.json.gz';
        const bytes=fs.readFileSync(url);
        ctx.fetch=async path=>{assert.equal(path,url);return new Response(bytes)};
        const raw=await ctx.getProof(run);
        assert.equal(raw.source_run_id,run);
        assert.equal(raw.source_run_id,JSON.parse(zlib.gunzipSync(bytes)).source_run_id);
      }
    }
  }
  const bad=structuredClone(manifest);
  bad.models[0].pins[0].NL2_strict_combos=0;
  ctx.fetch=async()=>({ok:true,json:async()=>bad});
  await assert.rejects(()=>ctx.nl2ApplyVerifiedExtensions(base));
  if(manifest.board_reach_updates){
    const wrong=structuredClone(manifest);
    const audited=Object.values(wrong.board_reach_updates).flat().find(r=>r.locks.length);
    audited.locks[0].compatible_hole_card_pairs=-1;
    ctx.fetch=async()=>({ok:true,json:async()=>wrong});
    await assert.rejects(()=>ctx.nl2ApplyVerifiedExtensions(base));
  }
  for(const file of ['nl2-multiboard.js','nl2_hu_multiboard_ui.js']) {
    assert.ok(fs.readFileSync(file,'utf8').includes('.then(globalThis.nl2ApplyVerifiedExtensions)'));
  }
  console.log('PASS exact source registry, GTO/locked archives and zero-reach rejection');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
