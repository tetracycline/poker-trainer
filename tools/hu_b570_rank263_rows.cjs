const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const app = { innerHTML: '', querySelectorAll: () => [], addEventListener() {} };
const context = {
  console, __LINES_QA: true, location: {hash:'#lines'}, scrollTo() {}, addEventListener() {},
  document: {querySelector: () => app, querySelectorAll: () => [], getElementById: () => null}
};
context.window = context;
vm.createContext(context);
for (const file of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js']) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, {filename:file});
}


context.__linesQA.render('3bp');
const html=app.innerHTML;
const end='ln-3bp-3b_r_model-1nr3lqx',turn='ln-3bp-3b_t_delay-1dtdkeg';
const headings=[...html.matchAll(/<div class="sec" data-node="([^"]+)" id="([^"]+)">/g)];
const sections=new Map(headings.map((m,i)=>[m[2], html.slice(m.index,headings[i+1]?.index??html.length)]));
const evidence=[];
for(const [id,section] of sections) {
  const seen=[];
  for(const row of section.matchAll(/<tr[^>]* id="([^"]+)">([\s\S]*?)<\/tr>/g)){
    for (const [column,cell] of [...row[2].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()){
      for(const link of cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)) {
        if(link[1]===turn||link[1].startsWith(turn+'-')||link[1]===end||link[1].startsWith(end+'-')) seen.push([row[1].slice(id.length+1),column,link[1],link[2]]);
      }
    }
  }
  if(seen.length) evidence.push({from:id,links:seen});
}
const flop='ln-3bp-3b_f_cbet-ke0pam';
const from=Object.fromEntries(evidence.map(r=>[r.from,r.links]));
assert.deepEqual(Object.keys(from).sort(),[flop,turn].sort());
function checkedRows(links,target) {
  for(const [row,col,href,label] of links) {
    assert.equal(col,2); assert.equal(href,target+'-'+row); assert.equal(label.replace(/≈$/,''),'過');
  }
  return links.map(x=>x[0]).sort();
}
assert.deepEqual(checkedRows(from[flop],turn),['A_high','KQ_high','mono','paired']);
assert.deepEqual(checkedRows(from[turn],end),['KQ_high','mono']);
const target=context.__HU_MODEL_LAST.nodes.find(n=>n.id===end);
assert.equal(target.pre,'翻前：BTN 開， 你 BB 3-bet ，BTN 跟');
assert.deepEqual([target.facts.root.spot,target.facts.root.pot,target.facts.root.stack,target.facts.pot,target.facts.spr],['BB3_BTN',20.5,90,20.5,4.39]);
const final=[];
for(const row of sections.get(end).matchAll(/<tr[^>]* id="([^"]+)">([\s\S]*?)<\/tr>/g)){
  for(const [column,cell] of [...row[2].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].entries()){
    const action=cell[1].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replaceAll('≈','').trim();
    if(action==='—')continue;
    assert.equal(column,2);assert.equal(action,'過'); final.push(row[1].slice(end.length+1));
  }
}
assert.deepEqual(final.sort(),['KQ_high','mono']);
console.log('Verified BB3-BTN sized geometry and all three rendered MID/check cells.');
