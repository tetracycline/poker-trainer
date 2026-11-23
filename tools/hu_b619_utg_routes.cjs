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
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(n=>[n.id,n]));
const textures=['low','mid_high','KQ_high','A_high','paired','mono'];
function cells(id) {
  const section=app.innerHTML.split('id="'+id+'"')[1].split('<div class="sec"')[0];
  return textures.flatMap(texture=>{
    const row=section.match(new RegExp('<tr[^>]+id="'+id+'-'+texture+'">([\\s\\S]*?)</tr>'));
    assert.ok(row,id);
    return [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map((cell,i)=>[texture+':'+i,texture,cell[1]]);
  });
}
function incoming(source, target, label) {
  const keys = [];
  for (const [key, texture, html] of cells(source)) {
    for (const m of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)) {
      if (m[1] === target + '-' + texture) {
        assert.equal(m[2].replace(/≈$/, ''), label);
        keys.push(key);
      }
    }
  }
  assert.ok(keys.length, source + ' -> ' + target);
  return keys;
}
const root = 'ln-opfr-f_cbet-1ihx52e';
const parent = 'ln-opfr-t_model-1ocorr7';
const targets = {
  109: ['ln-opfr-r_model-1txz51y', '下注 ¾', 0.75],
  110: ['ln-opfr-r_model-bt63wt', '下注 ½', 0.50],
  111: ['ln-opfr-r_model-psu0y9', '下注 ⅓', 1 / 3]
};
const output = {};
for (const [rank, [id, label, fraction]] of Object.entries(targets)) {
  const model = nodes.get(id);
  assert.equal(model.source, parent);
  assert.deepEqual([model.facts.root.spot, model.facts.pot, model.facts.stack], ['UTG_CO', Number((6.5 * (1 + 2 * fraction)).toFixed(3)), Number((97.5 - 6.5 * fraction).toFixed(3))]);
  const flop = incoming(root, parent, '過');
  const turn = incoming(parent, id, label);
  assert.deepEqual([...new Set(turn)].sort(), Array.from(model.allowed).sort());
  const river = {};
  for (const [key, texture, html] of cells(id)) {
    if (!model.allowed.includes(key)) continue;
    const action = html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g, '').replaceAll('≈','').trim();
    assert.ok(action && action !== '—');
    river[key] = action;
  }
  output[rank] = {id, flop, turn, river};
}
console.log(JSON.stringify(output));
