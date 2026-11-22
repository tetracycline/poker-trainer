#!/usr/bin/env node
// B378: execute the actual V47 validator from both browser scripts, no fake source data.
const fs=require('node:fs'),assert=require('node:assert/strict');
const status=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_v47_b364_rank96.json','utf8'));
const V47='NL2_HU_392_MULTIBOARD_CERT_STATUS_V47_B364_RANK96';
const V48='NL2_HU_392_MULTIBOARD_CERT_STATUS_V48_B369_RANK27';
assert.equal(status.schema,V47);
assert.deepEqual([status.CERT_MULTIBOARD,status.APPROX,status.EST,status.TOTAL],[159,233,0,392]);
for(const filename of ['nl2_hu_multiboard_ui.js','nl2-multiboard.js']){
  const source=fs.readFileSync(filename,'utf8');
  const start=source.indexOf('const v47=d=>{');
  const stop=source.indexOf('const v46=d=>{',start);
  assert.ok(start>0&&stop>start,filename+' missing real V47 body');
  const body=source.slice(start,stop);
  assert.ok(!body.includes("schema!=="+JSON.stringify(V47)+','),filename+' stale comma operator');
  assert.ok(body.includes("d.schema!=='"+V47+"'||"),filename+' failclosed schema gate missing');
  const v47=new Function(body+'; return v47;')();
  assert.equal(v47(status),status,filename+' must accept exact SHA-gated real V47');
  const corrupt=JSON.parse(JSON.stringify(status));
  corrupt.CERT_MULTIBOARD=160;
  assert.throws(()=>v47(corrupt),/failclosed/,filename+' must fail closed wrong counts');
  const forged=JSON.parse(JSON.stringify(status));
  forged.schema=V48;
  assert.throws(()=>v47(forged),/failclosed/,filename+' V47 must reject V48 schema');
  assert.ok(source.includes("fetch('data/nl2_hu_multiboard_status_v48_b369_rank27.json'"));
  assert.ok(source.includes("fetch('data/nl2_hu_multiboard_status_v47_b364_rank96.json'"));
  assert.ok(source.includes("'"+V48+"','"+V47+"'"),filename+' missing allowed well-guarded v48 fallback');
}
for(const filename of ['nl2.html','nl2-multiboard.html']){
 const h=fs.readFileSync(filename,'utf8');
 assert.ok(h.includes('task-hybrid-b378-v47-loaderfix-20261122'),filename+' cache not invalidated');
}
console.log('PASS B378 authentic V47 159/233 actual runtime validator, corrupt/mislabeled source rejected in both loaders');
