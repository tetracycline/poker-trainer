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
const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(node => [node.id, node]));

const turn=nodes.get('ln-ipc-t_model-btptzw'),river=nodes.get('ln-ipc-r_model-1at1re2');
const opponent='ln-ipc-f_vs_cbet-1axpfmj';
const start=app.innerHTML.indexOf('id="'+opponent+'"');
assert.ok(start>=0);
const section=app.innerHTML.slice(start,app.innerHTML.indexOf('<div class="sec"',start));
assert.match(section,/你面對（例）/);
const anchors=[...section.matchAll(/<a\b[^>]*href="#ln-ipc-t_model-btptzw-[^"]+"[^>]*>[\s\S]*?<\/a>/g)];
assert.ok(anchors.length && anchors.every(a=>!/[0-9]/.test(a[0].replace(/<[^>]+>/g,''))));
assert.deepEqual([turn.pre,turn.source,turn.action,turn.key],['翻前：SB 開， 你 BB 跟',opponent,'call','對手下注、你跟|對手過']);
assert.deepEqual([river.pre,river.source,river.action,river.key],[turn.pre,turn.id,'check','對手下注、你跟|對手過、你過|對手過']);
for(const m of [turn,river]){
 assert.deepEqual([m.facts.root.family,m.facts.root.spot,m.facts.root.pot,m.facts.root.stack,m.facts.pot,m.facts.stack,m.facts.spr],
   ['SRP','SB_BB',6,97,12,91,7.583]);
}
process.stdout.write(JSON.stringify(Object.fromEntries([turn,river].map(m=>[m.id,{
  source_model_id:m.source,enabled_texture_handclass_cells:Array.from(m.allowed),generic_trainer_cells_certified:[],
  abstract_trainer_line:m.key,trainer_pot_bb:m.facts.pot,trainer_remaining_bb:m.facts.stack,model_spr:m.facts.spr,
  named_flop_lead_fraction:.5,source_flop_pot_bb:6,original_called_amount_bb:3,original_turn_remaining_bb:94,
  claim:'NAMED_ACTION_LINE_EXAMPLES_ONLY'}]))));
