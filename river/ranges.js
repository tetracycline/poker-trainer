// Range construction for river spots: preflop solver ranges -> line filters on flop/turn (documented heuristics).
(function (root) {
const RS = (typeof module !== 'undefined' && module.exports) ? require('./river.js') : root.RiverSolver;
const RK = '23456789TJQKA';
function classCombos(n) {
  const out = [];
  if (n.length === 2) { const r = RK.indexOf(n[0]); for (let a = 0; a < 4; a++) for (let b = a + 1; b < 4; b++) out.push([r * 4 + a, r * 4 + b]); }
  else { const h = RK.indexOf(n[0]), l = RK.indexOf(n[1]);
    if (n[2] === 's') for (let s = 0; s < 4; s++) out.push([h * 4 + s, l * 4 + s]);
    else for (let a = 0; a < 4; a++) for (let b = 0; b < 4; b++) if (a !== b) out.push([h * 4 + a, l * 4 + b]); }
  return out;
}
function classOf(c1, c2) {
  let a = c1 >> 2, b = c2 >> 2; if (a < b) [a, b] = [b, a];
  return a === b ? RK[a] + RK[a] : RK[a] + RK[b] + ((c1 & 3) === (c2 & 3) ? 's' : 'o');
}
// range from preflop solution: node name + action index (or product of several)
function fromPreflop(pf, parts) {
  const N = pf.names; const w = new Array(169).fill(1);
  parts.forEach(([node, act]) => { const nd = pf.nodes[node]; const k = nd.acts.indexOf(act); if (k < 0) throw new Error(node + ' ' + act); for (let i = 0; i < 169; i++) w[i] *= nd.strat[i][k]; });
  const combos = [];
  N.forEach((n, i) => { if (w[i] > 0.005) classCombos(n).forEach(([c1, c2]) => combos.push({ c1, c2, w: w[i] })); });
  return combos;
}
function removeDead(r, board) { const d = new Set(board); return r.filter(h => !d.has(h.c1) && !d.has(h.c2)); }
// strength on a partial board: made-hand value + draws -> percentile within range (combo-weighted)
function draws(c1, c2, board) {
  const cs = [c1, c2, ...board]; const suit = [0, 0, 0, 0]; cs.forEach(c => suit[c & 3]++);
  let fd = false; for (let s = 0; s < 4; s++) if (suit[s] === 4 && ((c1 & 3) === s || (c2 & 3) === s)) fd = true;
  let m = 0; cs.forEach(c => m |= 1 << (c >> 2)); const x = (m << 1) | (m >> 12 & 1);
  let oe = false; for (let lo = 0; lo <= 9; lo++) { const w = 0xF << lo; if ((x & w) === w) { const hm = ((1 << ((c1 >> 2) + 1)) | (1 << ((c2 >> 2) + 1))); if (hm & w) oe = true; } }
  return { fd, oe };
}
function percentiles(r, board) {
  const vals = r.map(h => RS.eval7([h.c1, h.c2, ...board]));
  const idx = r.map((_, i) => i).sort((a, b) => vals[a] - vals[b]);
  const tot = r.reduce((s, h) => s + h.w, 0); let acc = 0; const pct = new Array(r.length);
  idx.forEach(i => { acc += r[i].w; pct[i] = (acc - r[i].w / 2) / tot; });
  return r.map((h, i) => { const d = draws(h.c1, h.c2, board); let p = pct[i];
    const madeCat = vals[i] >> 20;
    if (madeCat <= 1 && (d.fd || d.oe)) p = Math.max(p, d.fd && d.oe ? 0.8 : 0.6);
    return { p, d, cat: madeCat }; });
}
// select a fraction of the range by score with smooth boundary (keeps weights fractional)
function keepTop(r, board, frac) {
  const P = percentiles(r, board);
  return r.map((h, i) => ({ ...h, w: h.w * clamp((P[i].p - (1 - frac)) / 0.06 + 0.5) })).filter(h => h.w > 1e-4);
}
function clamp(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
// bettor barrel range: value top `v`, all draws, plus bottom `b` as bluffs. Returns [betRange, checkRange]
function splitBarrel(r, board, v, b) {
  const P = percentiles(r, board); const bet = [], chk = [];
  r.forEach((h, i) => { const p = P[i].p; let f = clamp((p - (1 - v)) / 0.06 + 0.5);
    if (P[i].cat <= 1 && (P[i].d.fd || P[i].d.oe)) f = Math.max(f, 0.85);
    f = Math.max(f, clamp((b - p) / 0.04 + 0.5));
    if (f > 1e-4) bet.push({ ...h, w: h.w * f }); if (f < 1 - 1e-4) chk.push({ ...h, w: h.w * (1 - f) }); });
  return [bet, chk];
}
const api = { classCombos, classOf, fromPreflop, removeDead, percentiles, keepTop, splitBarrel, draws };
if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.RiverRanges = api;
})(this);
