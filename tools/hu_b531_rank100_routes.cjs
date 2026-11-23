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
context.__linesQA.render('iso');
const river = context.__HU_MODEL_LAST.nodes.find(n => n.id === 'ln-iso-lmp_r_model-1hgiamg');
const turn = context.__HU_MODEL_LAST.nodes.find(n => n.id === river.source);
assert.equal(turn.id, 'ln-iso-lmp_t_model-10v4wiz');
assert.equal(turn.source, 'ln-iso-lmp_f_vs_cbet-a1tpaq');
assert.equal(river.key, '你過、對手下注、你跟|你過、對手過|');
const textures = ['low','mid_high','KQ_high','A_high','mono'];
for(const [model,action] of [[turn,'跟'],[river,'過']]){
  const section=app.innerHTML.split('id="'+model.source+'"')[1].split('<div class="sec"')[0];
  const links=[];
  for(const [,id,row] of section.matchAll(/<tr data-cl="[^"]+" id="([^"]+)">([\s\S]*?)<\/tr>/g)){
    const cells=[...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)];
    for(const [col,cell] of cells.entries()) {
      for(const [,href,label] of cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)){
        if(!href.startsWith(model.id)) continue;
        const texture=id.replace(model.source+'-','');
        assert.equal(href,model.id+'-'+texture);
        assert.equal(label,action);
        links.push(texture+':'+col);
      }
    }
  }
  assert.deepEqual(links,textures.map(texture=>texture+':2'));
}
