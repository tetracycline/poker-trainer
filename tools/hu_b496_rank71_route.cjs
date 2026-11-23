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
context.__linesQA.render('iso');
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(node => [node.id, node]));

const rank71 = nodes.get('ln-iso-lmp_r_model-vlgh2t');
assert.deepEqual([rank71.source, rank71.pre, rank71.action, rank71.key, rank71.facts.root.family, rank71.facts.spr],
  ['ln-iso-lmp_t_vs_probe-eejqdl', '翻前：CO 溜入， 你 BB 過', 'call', '你下注、對手跟|你過、對手下注、你跟|', 'LMP', 9.916]);
const start = app.innerHTML.indexOf('id="' + rank71.source + '"');
assert.ok(start >= 0);
const template = app.innerHTML.slice(start, app.innerHTML.indexOf('<div class="sec"', start));
assert.match(template, /你面對（例）/);
const calls = [...template.matchAll(/<a\b[^>]*href="#ln-iso-lmp_r_model-vlgh2t-[^"]+"[^>]*>[\s\S]*?<\/a>/g)];
assert.ok(calls.length && calls.every(a => /^跟/.test(a[0].replace(/<[^>]+>/g, ''))));
process.stdout.write(JSON.stringify({ source_model_id: rank71.source, enabled_texture_handclass_cells: Array.from(rank71.allowed),
  generic_trainer_cells_certified: [], claim: 'NAMED_ACTION_LINE_EXAMPLES_ONLY' }));
