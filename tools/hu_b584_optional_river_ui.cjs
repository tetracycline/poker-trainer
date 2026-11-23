const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const vm = require('node:vm');
const registry = JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_current.json'));
const model = registry.records['ln-ipc-r_model-1a3ai9a'];
const publicBoard = '3c5d8s2h4c';
const viewer = fs.readFileSync('nl2-multiboard.js','utf8');
function element() {
  return {value:'0', children:[], appendChild(node){this.children.push(node);}, replaceChildren(){this.children=[];}};
}
async function main() {
  const elements = new Map([['board',element()],['model',element()]]);
  const context = vm.createContext({
    models:[model], chosenBoard:null, chosenModel:null, status:registry, proofCache:{},
    q:new URLSearchParams({board:publicBoard}), el:key=>elements.get(key), fmt:n=>String(n),
    opt:(box,value,textContent)=>box.children.push({value,textContent}), fillVersions(){},
    document:{createElement:element}, crypto:crypto.webcrypto, Response, DecompressionStream, TextEncoder, TextDecoder, atob,
    sourceSha:s=>s.source_sha256??s.sha256,
    fetch:async url=>new Response(fs.readFileSync(url))
  });
  vm.runInContext(viewer.slice(viewer.indexOf('function namedRiverChoices('),viewer.indexOf('function selectLeadTree(')),context);
  vm.runInContext(viewer.slice(viewer.indexOf('async function getProof(run){'),viewer.indexOf('function verifiedCase(')),context);
  vm.runInContext(viewer.slice(viewer.indexOf('function renderedPolicyComparison('),viewer.indexOf('function fillCombos()')),context);
  vm.runInContext(fs.readFileSync('nl2_locked_medium.js','utf8'),context);
  vm.runInContext('selectedModel()',context);
  const options=elements.get('board').children;
  assert.equal(model.certified_3_to_5_exact_flop_boards.length,3);
  assert.equal(new Set(model.certified_3_to_5_exact_flop_boards.map(b=>b.flop)).size,3);
  assert.equal(options.length,4);
  assert.equal(options.filter(o=>o.textContent.includes('同一翻牌的另一河牌')).length,1);
  const chosen=context.chosenBoard;
  assert.equal(chosen.public_board,publicBoard);
  const {pin,reach_report}=chosen.optionalRiver;
  for(const source of [{version:'gto',source_run_id:chosen.source_run_id,source_sha256:chosen.source_sha256},
                         chosen.nl2_locked_variants[0]]) {
    const run=source.run_id??source.source_run_id;
    const digest=source.sha256??source.source_sha256;
    const archive=await context.getProofForSource(run,source);
    const actual=archive.artifacts.flatMap(a=>a.cases).find(c=>c.version===source.version&&c.source_sha256===digest);
    assert.ok(actual);
    const node=actual.nodes.find(n=>n.public_board===publicBoard&&n.exact_node_line===chosen.actual_exact_action_line);
    assert.ok(node);
    const audit=context.nl2LockedMedium;
    const raw=audit.lookup(reach_report,model,chosen,source);
    assert.equal(raw.status,'POSITIVE_JOINT_REACH');
    const bound=await audit.bindCase(reach_report,actual,run);
    assert.equal(bound.get(node).row.source_sha256,digest);
    const table=context.renderedPolicyComparison(pin,node,digest);
    assert.ok(table && table.children[1].children.length>=pin.rendered_decision_hands.length);
    if(source.version==='exp_ip') {
      assert.equal(raw.b50.candidate,true);
      assert.equal(node.medium_50pct_eligible_combos,raw.b50.eligible);
      assert.ok(raw.b50.middle_count>=10);
    }
  }
  elements.get('board').value='0';
  vm.runInContext('selectBoard()',context);
  assert.equal(context.chosenBoard.public_board,model.certified_3_to_5_exact_flop_boards[0].public_board);
  assert.ok(!context.chosenBoard.optionalRiver);
  const bad=structuredClone(model);
  const branch=bad.certified_3_to_5_exact_flop_boards.find(b=>b.optional_named_rivers).optional_named_rivers[0];
  branch.board.source_sha256='0'.repeat(64);
  assert.throws(()=>context.namedRiverChoices(bad));
  console.log('Verified the optional native river and both policies alongside three distinct certified flops.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
