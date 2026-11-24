const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const app = {innerHTML: '', querySelectorAll: () => [], addEventListener() {}};
const c = {console, __LINES_QA: true, location: {hash: '#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null}};
c.window = c;
vm.createContext(c);
for (const file of ['lines_data.js', 'nl2_rules.js', 'hwrange.js', 'nl2_reach.js', 'nl2_titles.js', 'nl2_hu_model.js', 'nl2.js'])
  vm.runInContext(fs.readFileSync(file, 'utf8'), c, {filename: file});
c.__linesQA.render('iso');
const id = 'ln-iso-lmp_r_model-asilzt';
const start = 'ln-iso-lmp_f_lead-aqcv9i';
const probe = 'ln-iso-lmp_t_probe-1uf0tkn';
const facing = 'ln-iso-lmp_t_vs_probe-1ld6jxn';
const model = c.__HU_MODEL_LAST.nodes.find(n => n.id === id);
assert.equal(model.source, facing);
assert.equal(model.pre, '翻前：CO 溜入， 你 BB 過');
assert.equal(model.key, '你過、對手過|你過、對手下注、你跟|');
assert.deepEqual([model.facts.root.spot, model.facts.root.pot, model.facts.root.stack], ['ASSUMED_LMP', 2.5, 99]);
assert.equal(model.facts.spr, 17.044);
const section = id => app.innerHTML.split('id="' + id + '">')[1].split('<div class="sec"')[0];
assert(section(facing).split('<table')[0].includes('CO 下注 66%（1.7bb），你要跟 1.7bb（底池 4.2bb）'));
const cells = (id, tx) => [...section(id).split('id="' + id + '-' + tx + '">')[1].split('</tr>')[0]
  .matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m => m[1]);
const first = html => html.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);
const routes = {flop: {}, turn: {}, river: {}};
for (const tx of ['low','mid_high','KQ_high','A_high','paired','mono']) {
  const [root, turn, call, river] = [start, probe, facing, id].map(node => cells(node, tx));
  for (let i = 0; i < 5; i++) {
    const key = tx + ':' + i, link = 'class="jmp sub" href="#' + facing + '-' + tx + '"';
    if (first(root[i])?.[1] === probe + '-' + tx && first(root[i])?.[2] === '過' && root[i].includes(link))
      routes.flop[key] = '過';
    if (first(turn[i])?.[2] === '過' && turn[i].includes(link) && first(call[i])?.[1] === id + '-' + tx && first(call[i])?.[2] === '跟')
      routes.turn[key] = '跟';
    if (model.allowed.includes(key)) {
      const label = river[i].split('<small')[0].replace(/<[^>]*>/g, '').trim();
      assert.equal(label, '過');
      routes.river[key] = label;
    }
  }
}
assert.deepEqual(Object.keys(routes.flop).sort(), ['A_high:2','mid_high:2','paired:2']);
assert.deepEqual(Object.keys(routes.turn).sort(), ['mid_high:2','paired:2']);
assert.deepEqual(Object.keys(routes.river).sort(), Object.keys(routes.turn).sort());
console.log(JSON.stringify({id, start, probe, facing, model_spr: model.facts.spr, turn_pct: 66, routes}));
