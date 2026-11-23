const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const context = {
  console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null}
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js']) {
  vm.runInContext(fs.readFileSync(file,'utf8'), context, {filename: file});
}
context.__linesQA.render('ipfr');
const target = 'ln-ipfr-r_model-1iypoop';
const model = context.__HU_MODEL_LAST.nodes.find(node => node.id === target);
assert.equal(model.source, 'ln-ipfr-t_model-dzbacd');
assert.equal(model.key, '對手過、你下注、對手跟|對手過、你過|對手過');
const section = app.innerHTML.split('id="' + model.source + '"')[1].split('<div class="sec"')[0];
const rows = [...section.matchAll(/<tr data-cl="[^"]+" id="([^"]+)">([\s\S]*?)<\/tr>/g)];
const checks = [];
for (const [, id, row] of rows) {
  const cells = [...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)];
  for (const [col, cell] of cells.entries()) {
    const anchors = [...cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)];
    for (const [, href, action] of anchors) {
      if (!href.startsWith(target)) continue;
      assert.equal(href, target + '-mono');
      assert.equal(action, '過');
      checks.push([id.replace(model.source + '-', ''), col]);
    }
  }
}
assert.deepEqual(checks, [['mono',1], ['mono',2], ['mono',4]]);
assert.deepEqual(Array.from(model.allowed).sort(), checks.map(([row,col]) => row + ':' + col));
