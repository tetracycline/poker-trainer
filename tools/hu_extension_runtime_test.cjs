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
  assert.equal(result.trainer_route_contract_schema, registry.trainer_route_contract_schema);
  assert.deepEqual(JSON.parse(JSON.stringify(result.exact_source_extensions)), registry.exact_source_extensions);
  for(const id of Object.keys(registry.records)){
    const browserRecord=JSON.parse(JSON.stringify(result.records[id]));
    assert.deepEqual(browserRecord,registry.records[id],id);
    if(browserRecord.label==='APPROX' && browserRecord.remaining_exact_board_evidence){
      assert.ok(browserRecord.remaining_exact_board_evidence.length<3);
      assert.equal(browserRecord.certified_3_to_5_exact_flop_boards.length,0);
    }
  }
  const viewer=fs.readFileSync('nl2-multiboard.js','utf8');
  const proof=viewer.slice(viewer.indexOf('async function getProof(run){'),viewer.indexOf('function verifiedCase('));
  const route118=Object.values(registry.records).find(m=>m.frequency_rank===118);
  assert.ok(manifest.trainer_route_contract.routes[route118.model_id].streets.includes('x b66 c'));
  const missingContract=structuredClone(manifest);
  delete missingContract.trainer_route_contract;
  ctx.fetch=async()=>({ok:true,json:async()=>missingContract});
  await assert.rejects(()=>ctx.nl2ApplyVerifiedExtensions(base));
  const falsePrice=structuredClone(manifest);
  const sample=falsePrice.trainer_route_exclusions.find(r=>r.model_id===route118.model_id);
  if(sample) {
    const route=falsePrice.trainer_route_contract.routes[sample.model_id];
    route.streets=sample.actual_line.split('/');
    ctx.fetch=async()=>({ok:true,json:async()=>falsePrice});
    await assert.rejects(()=>ctx.nl2ApplyVerifiedExtensions(base));
  }
  ctx.fetch=async()=>({ok:true,json:async()=>manifest});
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
  for(const item of manifest.lock_variants.filter(e=>e.lock.requires_native_joint_replay)){
    const model=result.records[item.model_id], source=item.lock;
    const board=model.certified_3_to_5_exact_flop_boards.find(b=>b.public_board===item.public_board);
    if (!board) {
      const excluded=manifest.trainer_route_exclusions.some(row=>row.model_id===item.model_id && row.public_board===item.public_board);
      const partial=model.remaining_exact_board_evidence?.some(b=>b.public_board===item.public_board);
      const replacement = manifest.reverified_models.find(group => group.model_id === item.model_id);
      const retired = replacement?.superseded_native_variants?.find(row =>
        row.public_board === item.public_board && row.gto_run === item.gto_run && row.gto_sha256 === item.gto_sha256 &&
        row.lock_run === source.run_id && row.lock_sha256 === source.sha256 &&
        row.original_package_sha256 === item.original_package_sha256);
      if (retired) {
        assert.equal(model.label, 'CERT-MULTIBOARD');
        assert.ok(replacement.boards.length >= 3 && replacement.boards.every(b =>
          model.certified_3_to_5_exact_flop_boards.some(active => active.public_board === b.public_board)));
        assert.equal(retired.common_rendered_hands, 0);
        assert.ok(['NO_RENDERED_ORIGINAL_GTO_HAND', 'NO_PRICED_FLOP_LINK_ON_ACTUAL_TEXTURE'].includes(retired.reason));
        const historical = fs.readFileSync('data/solver_evidence/' + item.original_package);
        assert.equal(require('node:crypto').createHash('sha256').update(historical).digest('hex'), retired.original_package_sha256);
      }
      assert.ok(excluded || (model.label==='APPROX' && partial) || retired,
        'Missing native lock lacks a matching route exclusion, retained partial proof, or source-verified supersession');
      continue;
    }
    assert.ok(board.nl2_locked_variants.some(v=>v.sha256===source.sha256));
    Object.assign(ctx,{chosenModel:model,chosenBoard:board,status:result,proofCache:{},Response,DecompressionStream,
      crypto:require('node:crypto').webcrypto,TextEncoder,TextDecoder,atob,fetch:async path=>new Response(fs.readFileSync(path))});
    vm.runInContext(fs.readFileSync('nl2_locked_medium.js','utf8'),ctx);
    const medium=ctx.nl2LockedMedium, report=await medium.load(), observed=medium.lookup(report,model,board,source);
    assert.equal(observed.status,'POSITIVE_JOINT_REACH');
    assert.deepEqual([...observed.source_actions],board.exact_node_actions);
    assert.throws(()=>medium.lookup({...report,references:{}},model,board,source));
    ctx.jointReach={row:observed};
    vm.runInContext(viewer.slice(viewer.indexOf('async function getProof(run){'),viewer.indexOf('let versionRequest=')),ctx);
    ctx.sourceSha=s=>s.source_sha256??s.sha256;ctx.sourceRun=s=>s.source_run_id??s.run_id;
    const original=await ctx.getProofForSource(source.run_id,source), actual=ctx.verifiedCase(source,original);
    const node=actual.nodes.find(n=>n.public_board===board.public_board && n.exact_node_line===item.line && n.acting_seat===item.acting_seat);
    const bound=await medium.bindCase(report,actual,source.run_id);
    assert.equal(bound.get(node).mask,Buffer.from(observed.compatible_action_mask_b64,'base64').toString('latin1'));
    ctx.jointReach={row:{...observed,compatible_action_mask_b64:''}};
    assert.throws(()=>ctx.verifiedCase(source,original));
    const missing=structuredClone(manifest);
    const phase=item.after_reverification ? missing.reverified_board_reach_updates : missing.board_reach_updates;
    const updates=phase[item.model_id].find(r=>r.public_board===item.public_board&&r.line===item.line&&r.seat===item.acting_seat);
    updates.locks=updates.locks.filter(r=>r.sha256!==source.sha256);
    ctx.fetch=async()=>({ok:true,json:async()=>missing});
    await assert.rejects(()=>ctx.nl2ApplyVerifiedExtensions(base));
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
    const script = fs.readFileSync(file, 'utf8');
    const start = script.indexOf('function applyCurrentTrainerRoutes(');
    const end = script.indexOf('\nfetchCertifiedRegistry()', start);
    assert.ok(start >= 0 && end > start && script.slice(end).includes('.then(applyCurrentTrainerRoutes)'));
    const loader = vm.createContext({});
    vm.runInContext(script.slice(start, end), loader);
    await assert.rejects(async () => loader.applyCurrentTrainerRoutes(base));
    loader.nl2ApplyVerifiedExtensions = async () => base;
    await assert.rejects(() => loader.applyCurrentTrainerRoutes(base));
    loader.nl2ApplyVerifiedExtensions = async () => result;
    assert.equal(await loader.applyCurrentTrainerRoutes(base), result);
  }
  console.log('PASS exact source registry, GTO/locked archives and zero-reach rejection');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
