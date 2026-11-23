const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = { innerHTML: '', querySelectorAll: () => [], addEventListener() {} };
const context = {
  console, __LINES_QA: true, location: { hash: '#lines' }, scrollTo() {}, addEventListener() {},
  document: { querySelector: () => app, querySelectorAll: () => [], getElementById: () => null }
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, { filename: file });
}
context.__linesQA.render('opfr');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(node => [node.id, node]));

const root = JSON.parse(fs.readFileSync("data/nl2_hu_multiboard_status_v51_b453_rank32.json", "utf8"));
const byRank = new Map(Object.values(root.records).map(entry => [entry.frequency_rank,entry]));
for (const [rank, parentRank, bet, targetPot, targetStack] of [
  [99,30,.50,26,87.75], [109,33,.75,16.25,92.625],
  [110,33,.50,13,94.25], [111,33,.333,10.833,95.333]
]) {
  const child = nodes.get(byRank.get(rank).model_id);
  const parent = nodes.get(byRank.get(parentRank).model_id);
  assert.equal(child.source, parent.id);
  assert.equal(child.st, 2);
  assert.equal(child.action, "bet");
  assert.equal(child.size, bet);
  assert.equal(parent.action, parentRank === 30 ? "bet" : "check");
  if (parentRank === 30) assert.equal(parent.size, .5);
  assert.equal(parent.key, parentRank === 30 ? "你下注、對手跟|" : "你過、對手過|");
  assert.match(child.pre, /你\s*UTG\s*開/);
  assert.equal(child.facts.pot,targetPot);
  assert.equal(child.facts.stack,targetStack);
  assert.equal(child.facts.spr,byRank.get(rank).assumed_model_node_spr);
}
console.log("PASS four exact UTG parent and child decisions, including native turn bet fractions");
