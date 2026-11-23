const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ctx = vm.createContext({});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js','utf8'),ctx);
const {match,matchFrozenRiver} = ctx.nl2HalfPotLeads;
const read = p => JSON.parse(fs.readFileSync(p));
const row = read('data/nl2_hu_b561_frozen_river.json');
const m = read('data/nl2_hu_multiboard_status_current.json').records[row.model_id];
const board = m.certified_3_to_5_exact_flop_boards.find(b=>b.public_board===row.public_board);
const prior = match(read('data/nl2_hu_b500_half_pot_leads.json').records,m,board);
assert.equal(matchFrozenRiver(row,m,board,prior),row);
assert.equal(matchFrozenRiver(row,m,{...board,source_sha256:'0'.repeat(64)},prior),null);
assert.equal(matchFrozenRiver(row,m,{...board,nl2_locked_variants:[]},prior),null);
assert.throws(()=>matchFrozenRiver(row,m,board,{...prior,status:'BOTH_POSITIVE'}));
const invalid=structuredClone(row);
invalid.policies.exp_oop.half_pot_pairs=0;
assert.throws(()=>matchFrozenRiver(invalid,m,board,prior));
console.log('B561 conditional river and original zero full-turn alternative verified.');
class Element {
  constructor(){this.textContent='';this.children=[];}
  appendChild(el){this.children.push(el);return el;}
}
ctx.document={createElement:()=>new Element()};
ctx.fetch=async path=>({ok:true,status:200,json:async()=>read(path)});
const parent=new Element();
ctx.nl2HalfPotLeads.showBoard(parent,m,board);
setImmediate(()=>{
  const texts=el=>[el.textContent,...el.children.flatMap(texts)];
  const displayed=texts(parent);
  assert.ok(displayed.some(x=>x.includes('從轉牌重新求解')));
  assert.ok(displayed.some(x=>x.includes('固定原轉牌策略後')));
  assert.ok(displayed.some(x=>x.startsWith('GTO 逐手半池頻率')));
  assert.ok(displayed.some(x=>x.startsWith('NL2 逐手半池頻率')));
  assert.ok(displayed.some(x=>x.includes('64,272')));
});
