const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const read = path => JSON.parse(fs.readFileSync(path));
const element = () => ({children: [], appendChild(node) { this.children.push(node); }});
const models = read('data/nl2_hu_multiboard_status_current.json').records;
const ctx = vm.createContext({document: {createElement: element},
  fetch: async path => ({ok: true, json: async () => read(path)})});
vm.runInContext(fs.readFileSync('nl2_half_pot_leads.js', 'utf8'), ctx);

async function verify(rank) {
  const report = read('data/nl2_hu_b663_rank'+rank+'_river.json');
  for (const row of report.records) {
    const model = models[row.model_id];
    const board = model.certified_3_to_5_exact_flop_boards.find(b => b.public_board === row.public_board);
    const render = async (b, source) => {
      const parent = element();
      await ctx.nl2HalfPotLeads.showRiverReply(parent, model, b, source);
      return parent.children;
    };
    assert.deepEqual(await render({...board, source_run_id: 0}), []);
    assert.deepEqual(await render(board, 'unmatched-sha'), []);
    const nodes = await render(board);
    const hands = Object.entries(row.locked.eligible_hand_frequencies);
    assert.equal(nodes.length, Number(hands.length > 0 && row.response_pairs > 0));
    if (!nodes.length) continue;
    const copy = nodes[0].children.map(child => child.textContent).join('\n');
    assert.ok(copy.includes(row.seat ? '大盲 河牌半池下注與小盲回應鎖' : '小盲 河牌半池下注與大盲回應鎖'));
    assert.ok(copy.includes('64,272') && copy.includes('跟注 37.6%'));
    assert.ok(copy.includes(row.locked.half_pot.candidate ? '符合非極化研究門檻' : '未達非極化研究門檻'));
    for (const [hand, freq] of hands) assert.ok(copy.includes(hand+' '+(freq*100).toFixed(1)+'%'));
  }
}
Promise.all([verify(43),verify(102)]).catch(error => {console.error(error); process.exitCode=1;});
