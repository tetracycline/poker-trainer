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


const id='ln-ipc-r_model-va4mgd';
const turn='ln-ipc-t_stab-11hbwd9',flop='ln-ipc-f_vs_cbet-1axpfmj';
const model=nodes.get(id);
assert.equal(model.source,turn);
const flopKeys=[];
for(const [key,texture,html] of cells(flop)){
  for(const match of html.matchAll(/<a class="jmp" href="#([^"]+)">([^<]+)<.a>/g)){
    if(match[1]===turn+'-'+texture){assert.equal(match[2].replace(/≈$/,''),'跟');flopKeys.push(key);}
  }
}
const turnKeys=incoming(turn,id,'下注 1');
assert.deepEqual(turnKeys,['KQ_high:1']);
const river=cells(id).filter(([key])=>model.allowed.includes(key)).map(([key,texture,html])=>{
  const label=html.split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈/g,'').trim();
  return [key,label];
});
assert.deepEqual(river,[['KQ_high:1','過']]);
console.log(JSON.stringify({model:id,parent:turn,flop:flopKeys,turn:turnKeys,river:Object.fromEntries(river)}));
