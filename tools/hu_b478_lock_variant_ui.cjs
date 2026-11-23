const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const zlib=require('node:zlib');
const read=p=>JSON.parse(fs.readFileSync(p));
const current=read(process.argv[2]);
const base=read('data/'+current.base_registry);
const manifest=read('data/nl2_hu_verified_extensions.json');
const viewer=fs.readFileSync('nl2-multiboard.js','utf8');
const row=read('data/solver_evidence/lock_variants/rank1_b472.json');
const key=row.model_id;
const ctx=vm.createContext({Response,DecompressionStream,crypto:require('node:crypto').webcrypto,
  fetch:async()=>({ok:true,json:async()=>manifest})});
vm.runInContext(fs.readFileSync('nl2_cert_registry.js','utf8'),ctx);
async function main(){
  const withVariant=await ctx.nl2ApplyVerifiedExtensions(base);
  const noVariant={...manifest,lock_variants:manifest.lock_variants.filter(x=>x.lock.sha256!==row.lock.sha256)};
  ctx.fetch=async()=>({ok:true,json:async()=>noVariant});
  const old=await ctx.nl2ApplyVerifiedExtensions(base);
  const models=JSON.parse(JSON.stringify(withVariant.records));
  const board=models[key].certified_3_to_5_exact_flop_boards.find(b=>b.public_board===row.public_board);
  const supplemental=board.nl2_locked_variants.pop();
  assert.equal(supplemental.sha256,row.lock.sha256);
  assert.deepEqual(models,JSON.parse(JSON.stringify(old.records)));
  assert.equal(withVariant.CERT_MULTIBOARD,old.CERT_MULTIBOARD);
  const total=Object.values(withVariant.records).flatMap(m=>m.certified_3_to_5_exact_flop_boards||[])
    .reduce((n,b)=>n+b.nl2_locked_variants.length,0);
  assert.equal(total,current.all_cert_lock_medium.paired_hero_locked_source_variants);
  for(const mutate of [r=>{r.gto_sha256='0'.repeat(64)},r=>{r.parent_lock_sha256='0'.repeat(64)},
    r=>{r.lock.version='exp_ip'},r=>{r.lock.strictly_reachable_combos=0}]){
    const broken=structuredClone(manifest);mutate(broken.lock_variants.find(x=>x.lock.sha256===row.lock.sha256));
    ctx.fetch=async()=>({ok:true,json:async()=>broken});
    await assert.rejects(()=>ctx.nl2ApplyVerifiedExtensions(base));
  }
  const model=withVariant.records[key], boards=model.certified_3_to_5_exact_flop_boards;
  const index=boards.findIndex(b=>b.public_board===row.public_board), exact=boards[index];
  const version={options:[],replaceChildren(){this.options=[]}};
  Object.assign(ctx,{status:withVariant,chosenModel:model,chosenBoard:exact,proofCache:{},
    q:new URLSearchParams({version:'exp_oop@1'}), el:id=>id==='board'?{value:index}:version,
    opt:(box,value,label)=>box.options.push({value,label}), selectVersion(){}});
  vm.runInContext(viewer.slice(viewer.indexOf('function nodeCount('), viewer.indexOf('function buildLinks(')), ctx);
  vm.runInContext(viewer.slice(viewer.indexOf('function selectBoard(){'),viewer.indexOf('async function getProof(run){')),ctx);
  ctx.selectBoard();assert.equal(version.value,'exp_oop@1');
  assert.equal(ctx.sourceCase('exp_oop@0').sha256,row.parent_lock_sha256);
  assert.equal(ctx.sourceCase(version.value).sha256,row.lock.sha256);
  assert.ok(version.options.find(x=>x.value===version.value).label.includes(row.lock.variant_label));
  ctx.sourceRun=s=>s.source_run_id??s.run_id;
  ctx.sourceSha=s=>s.source_sha256??s.sha256;
  vm.runInContext(viewer.slice(viewer.indexOf('async function getProof(run){'),viewer.indexOf('let versionRequest=')),ctx);
  const bytes=fs.readFileSync('data/solver_evidence/NL2_MULTIBOARD_'+row.lock.viewer_archive_code+'.json.gz');
  ctx.fetch=async path=>{assert.equal(path,'data/solver_evidence/NL2_MULTIBOARD_'+row.lock.viewer_archive_code+'.json.gz');return new Response(bytes)};
  const source=ctx.sourceCase(version.value);
  const actual=ctx.verifiedCase(source,await ctx.getProofForSource(source.run_id,source));
  const node=actual.nodes[0];
  assert.equal(node.strictly_reachable_combos,689);assert.equal(node.medium_50pct_eligible_combos,371);
  assert.equal(Buffer.from(node.strictly_reachable_masks_b64,'base64').filter(b=>b!==0).length,689);
  assert.equal(actual.villain_lock_scope.observed_marginal_source_nodes,source.observed_marginal_source_nodes);
  assert.equal(source.reach_comparison.common_legal_hero_combos,116);
  assert.equal(zlib.gunzipSync(bytes).length>0,true);
  assert.ok(fs.readFileSync('nl2_hu_multiboard_ui.js','utf8').includes("version:v.version+'@'+i"));
  ctx.proofCache={};ctx.fetch=async()=>new Response(Buffer.from('invalid source'));
  await assert.rejects(()=>ctx.getProofForSource(source.run_id,source));
  console.log('PASS original and corrected locks selectable, 689 exact hands, 116 shared with GTO, 371 b50 eligible');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
