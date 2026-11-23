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

context.__linesQA.render('ipc');
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

const model=nodes.get('ln-ipc-r_model-1h0u85n');
assert.equal(model.source,'ln-ipc-t_stab-11hbwd9');
assert.deepEqual([model.facts.root.spot,model.facts.pot,model.facts.stack],['SB_BB',20,90]);
const flop={},turn={},river={};
for(const [key,texture,html] of cells('ln-ipc-f_vs_cbet-1axpfmj')) {
 if([...html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/g)].some(m=>m[1]===model.source+'-'+texture && m[2].replace(/≈$/,'')==='跟'))flop[key]='跟';
}
for(const [key,texture,html] of cells(model.source)){
 if([...html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/g)].some(m=>m[1]===model.id+'-'+texture && m[2].replace(/≈$/,'')==='下注 ½'))turn[key]='下注 ½';
}
for(const [key,texture,html] of cells(model.id)){
 if(model.allowed.includes(key)){
  const label=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
  assert.ok(['過','下注 ½','下注 ¾'].includes(label));river[key]=label;
 }
}
assert.deepEqual(Object.keys(turn).sort(),Array.from(model.allowed).sort());
console.log(JSON.stringify({flop,turn,river}));
