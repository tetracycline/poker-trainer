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
const m = context.__HU_MODEL_LAST.nodes.find(n => n.id === 'ln-opfr-t_model-712wim');
assert.deepEqual([m.pre,m.source,m.key,m.action],['翻前： 你 SB 開 ，BB 跟','ln-opfr-f_vs_donk-1wk9say','你過、對手下注、你加注、對手跟|','raise']);
assert.deepEqual([m.facts.root.pot,m.facts.root.stack,m.facts.pot,m.facts.stack,m.facts.spr],[6,97,32,83,2.594]);
const section = app.innerHTML.split('id="' + m.source + '"')[1].split('<div class="sec"')[0];
assert.match(section,/你面對（例）/);
const labels = [...section.matchAll(/<a class="jmp" href="#ln-opfr-t_model-712wim-[^"]+">([^<]+)<\/a>/g)].map(match => match[1]);
assert.deepEqual(labels,['加注≈','加注']);
process.stdout.write(JSON.stringify({source_model_id:m.source,enabled_texture_handclass_cells:m.allowed,
    directly_verified_trainer_cells:[],trainer_pot_bb:32,trainer_stack_bb:83,source_pot_bb:33,source_stack_bb:83.5,
    named_line:'x b75 r c/',face_bet_bb:4.5,raise_to_bb:13.5,scope:'NAMED_ACTION_LINE_EXAMPLES_ONLY'}));
