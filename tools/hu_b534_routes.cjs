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
function section(id) {
  const [, html] = app.innerHTML.split('id="' + id + '"');
  assert.ok(html, id);
  return html.split('<div class="sec"')[0];
}
function tableLinks(id, target){
  const linked={};
  for (const [, rowId, row] of section(id).matchAll(/<tr data-cl="[^"]+" id="([^"]+)">([\s\S]*?)<\/tr>/g)) {
    const texture=rowId.replace(id+'-','');
    const cells=[...row.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)];
    for (const [col, cell] of cells.entries()){
      for(const [,href,text] of cell[1].matchAll(/<a class="jmp" href="#([^"]+)">([^<]*)<\/a>/g)){
        if(!href.startsWith(target)) continue;
        assert.equal(href,target+'-'+texture);
        (linked[texture]||=[]).push([col,text.replace(/≈$/,'')]);
      }
    }
  }
  return linked;
}
context.__linesQA.render('ipc');
const river='ln-ipc-r_model-10r9o8q';
const rank341=context.__HU_MODEL_LAST.nodes.find(m=>m.id===river);
const turnLinks=tableLinks(rank341.source,river);
assert.deepEqual(turnLinks,{low:[0,1,2,3,4].map(col=>[col,'下注 ½'])});
const stab='ln-ipc-f_stab-m47nk0-low';
const flopRow=section(stab).split('</tr>')[0];
const flopCells=[...flopRow.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)];
assert.equal(flopCells.length,5);
for(const cell of flopCells) {
  const txt=cell[1].replace(/<[^>]*>/g,' ').trim();
  assert.match(txt,/^下注 1(?:\s|$)/);
  assert.match(txt,/若被加注/);
}
assert.equal(rank341.facts.spr,2.278);
const registry=JSON.parse(fs.readFileSync('data/nl2_hu_multiboard_status_v53_b465_rank218.json'));
const archived=registry.records[river].certified_3_to_5_exact_flop_boards;
for(const board of ['4d9hJsTsAh','2d7hKs9d5s']) {
  const b=archived.find(x=>x.public_board===board);
  assert.equal(b.actual_exact_action_line,'x b33 r c/x b50 c/x');
  assert.ok([...b.public_board.slice(0,8)].filter((_,i)=>!(i%2)).some(card=>'TJQKA'.includes(card)));
}
// 100bb SB open/BB call, 1-pot stab, x3 raise, call, and half-pot turn bet/call.
const rootPot=6, startStack=97, raiseTo=rootPot*3, turnPot=rootPot+2*raiseTo;
const actualSpr=(startStack-raiseTo-turnPot/2)/(2*turnPot);
assert.ok(Math.abs(actualSpr/rank341.facts.spr-1)>.05);
context.__linesQA.render('ipfr');
const target='ln-ipfr-t_model-snfiz2';
const model=context.__HU_MODEL_LAST.nodes.find(m=>m.id===target);
assert.equal(model.pre,'翻前： 你 CO 開 ，BB 跟');
assert.equal(model.key,'對手過、你下注、對手跟|對手過');
assert.deepEqual(tableLinks(model.source,target),{
  A_high:[0,3,4].map(col=>[col,'下注 ¾']),paired:[0,1,2,3,4].map(col=>[col,'下注 ¾'])
});
