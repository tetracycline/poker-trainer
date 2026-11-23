// Resolve the actual primary action links for each rendered HU model.
// Calls and unsized actions carry no numeric price in this contract.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const ids = JSON.parse(fs.readFileSync(0, 'utf8'));
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

const actions = {'過':'x','跟':'c','下注':'bet','加注':'raise','超池下注':'overbet'};
const positions = ['SB','BB','UTG','HJ','CO','BTN'];
const fractions = {'⅓':'b33','½':'b50','⅔':'b66','¾':'b75','1½':'b150'};
function betToken(text) {
  if (!/^下注/.test(text)) return null;
  const match = text.match(/^下注\s*(1½|⅓|½|⅔|¾|\d+(?:\.\d+)?%?)/);
  if (!match) return null;
  const size = match[1];
  return fractions[size] || 'b' + Math.round(parseFloat(size) * (size.endsWith('%') ? 1 : 100));
}

const routes = {};
for (const spot of new Set(ids.map(id => id.split('-')[1]))) {
  context.__linesQA.render(spot);
  const html = app.innerHTML;
  const headings = [...html.matchAll(/<div class="sec" data-node="([^"]+)" id="([^"]+)">/g)];
  const sections = new Map(headings.map((m,i) => [m[2], html.slice(m.index, headings[i+1]?.index ?? html.length)]));
  const incoming = new Map();
  for (const [from, section] of sections) {
    for (const match of section.matchAll(/<a class="jmp" href="#([^"]+)">([\s\S]*?)<\/a>/g)) {
      const target = match[1].replace(/-(low|mid_high|KQ_high|A_high|paired|mono)$/, '');
      if (!sections.has(target)) continue;
      const edge = {from, href:match[1], label:match[2].replace(/<[^>]*>/g, '').trim()};
      if (!incoming.has(target)) incoming.set(target, []);
      incoming.get(target).push(edge);
    }
  }
  const nodes = new Map(context.__HU_MODEL_LAST.nodes.map(node => [node.id, node]));
  for (const model of nodes.values()) {
    const hero = model.pre.match(/你\s*(SB|BB|UTG|HJ|CO|BTN)\b/)?.[1];
    const villain = model.pre.match(/\b(?:SB|BB|UTG|HJ|CO|BTN)\b/g)?.find(p => p !== hero);
    assert(hero && villain, model.id);
    const seat = Number(positions.indexOf(hero) > positions.indexOf(villain));
    const history = model.key.split('|').map(street => street.split('、').filter(Boolean));
    const streets = history.map(tokens => tokens.map((roleAction, i) => {
      assert.equal(roleAction.startsWith('你') ? seat : 1-seat, i%2, model.id);
      const token = actions[roleAction.replace(/^(你|對手)/,'')];
      assert(token, roleAction);
      return token;
    }));
    assert.equal(streets.length, model.st+1);
    assert.equal(streets.at(-1).length%2, seat, model.id);
    const links = [];
    function addSize(street, edges) {
      const labels = [...new Set(edges.map(e => e.label))].sort();
      const sizes = new Set(labels.map(betToken));
      if (sizes.size !== 1 || sizes.has(null)) return;
      const i = history[street].lastIndexOf('你下注');
      assert(i >= 0 && streets[street][i] === 'bet', model.id);
      streets[street][i] = [...sizes][0];
      links.push({street:street+1,action:i+1,labels,from:[...new Set(edges.map(e => e.from))].sort()});
    }
    for (let node=model; node; node=nodes.get(node.source)) {
      const edges = (incoming.get(node.id) || []).filter(edge => edge.from === node.source);
      assert(edges.length, node.id + ' has no primary link from ' + node.source);
      if (node.action === 'bet') addSize(node.st-1, edges);
      if (!nodes.has(node.source) && node.st === 2 && history[0].includes('你下注')) {
        // For a pre-authored turn, infer a flop price only when every direct primary ingress
        // from a flop section explicitly specifies the same bet. An example paragraph is not an action.
        const prior = (incoming.get(node.source) || []).filter(e => /^ln-.*-(?:[a-z0-9]+_)?f_[a-z0-9_]+-/.test(e.from));
        if (prior.length) addSize(0, prior);
      }
    }
    assert(!routes[model.id], model.id);
    const route = {seat,streets:streets.map(tokens => tokens.join(' ')),links};
    if(model.id==='ln-ipfr-r_model-1iypoop') {
      const edges=incoming.get(model.id).filter(e=>e.from===model.source);
      assert.equal(model.source,'ln-ipfr-t_model-dzbacd');
      assert.deepEqual([...new Set(edges.map(e=>e.href))],[model.id+'-mono']);
      assert.deepEqual([...new Set(edges.map(e=>e.label))],['過']);
      route.requires_three_suited_turn=true;
    }
    routes[model.id] = route;
  }
}
assert.equal(ids.length, 392);
assert.deepEqual(Object.keys(routes).sort(), [...ids].sort());
process.stdout.write(JSON.stringify({schema:'NL2_HU_RENDERED_ACTION_ROUTES_V1',routes}));
