// Read amounts from the same generated nodes the training interface uses.
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const context = {
  console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null},
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, {filename: file});
}
context.__linesQA.render('iso');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(node => [node.id, node]));
const first = 'ln-iso-iso_f_first-zd1by2';
const generated = 'ln-iso-iso_t_model-1x553s3';
const probe = 'ln-iso-iso_t_probe-1vfhv3';
const seatHistory = '翻前： 你 CO 溜入 ，BTN 加注隔離， 你 CO 跟';
const flopLine = '你過、對手過';
const turn = nodes.get(generated);
assert.deepEqual([turn.source, turn.pre, turn.key, turn.action], [first, seatHistory, flopLine + '|', 'check']);
// The pre-authored probe is the other route to the same unbet 9.5bb turn.
const marker = 'id="' + probe + '"';
const start = app.innerHTML.indexOf(marker);
assert.ok(start > 0);
const section = app.innerHTML.slice(start, app.innerHTML.indexOf('<div class="sec"', start));
const title = section.match(/<b class="ttl">([\s\S]*?)<\/b>/)[1].replace(/<[^>]+>/g, '');
assert.equal(title, '翻前：你 CO 溜入，BTN 加注隔離，你 CO 跟' + ' → 翻牌：你過、對手過 → 轉牌：你先行動，下注或過牌？');
assert.ok(section.includes('href="#' + first + '">↑ 上一步'));
assert.ok(section.includes('BTN 加注到 4bb') && section.includes('底池 9.5bb'));
const targets = [
  [140, 'ln-iso-iso_r_model-1gds1ky', generated, 'bet', '你下注、對手跟', 19, 91.25],
  [160, 'ln-iso-iso_r_model-17k9x0l', generated, 'check', flopLine, 9.5, 96],
  [161, 'ln-iso-iso_r_model-19fbxqk', probe, 'check', flopLine, 9.5, 96],
];
const scope = {};
for (const [rank, id, parent, action, turnLine, pot, stack] of targets) {
  const river = nodes.get(id);
  assert.deepEqual([river.pre, river.source, river.action, river.key, river.facts.pot, river.facts.stack],
    [seatHistory, parent, action, flopLine + '|' + turnLine + '|', pot, stack]);
  if (action === 'bet') assert.equal(river.size, 0.5);
  scope[rank] = {source_model_id:parent, enabled_texture_handclass_cells:Array.from(river.allowed)};
}
process.stdout.write(JSON.stringify(scope));
