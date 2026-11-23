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
function checkLinks(target, source, action, allowedColumns) {
  const section = app.innerHTML.split('id="' + source + '"')[1].split('<div class="sec"')[0];
  const mono = section.match(new RegExp('<tr data-cl="單色面" id="' + source + '-mono">([\\s\\S]*?)</tr>'));
  assert.ok(mono, source);
  const cells = [...mono[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)];
  const present = cells.flatMap((cell, col) => {
    const links = [...cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)];
    return links.filter(([, href]) => href === target + '-mono').map(([, , text]) => {
      assert.equal(text.replace(/≈$/, ''), action);
      return col;
    });
  });
  assert.deepEqual(present, allowedColumns);
}
const turn = context.__HU_MODEL_LAST.nodes.find(node => node.id === model.source);
checkLinks(turn.id, turn.source, '下注 ½', [1,2,3,4]);
checkLinks(model.id, model.source, '過', [1,2,4]);
