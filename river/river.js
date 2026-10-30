/* River (single-street) heads-up CFR solver. Works in browser (window.RiverSolver) and node (module.exports).
 * DCFR (alpha 1.5, beta 0, gamma 2), vectorised over combos, O(N) showdown/fold evaluation with exact card removal.
 * Player 0 = OOP (acts first), 1 = IP. Values are chips relative to the start of the street:
 *   showdown win: pot + opp contribution, lose: -own contribution, tie: pot/2.  (constant-sum = pot)
 */
(function (root) {
  'use strict';
  var RK = '23456789TJQKA', SU = 'cdhs';
  function card(s) { return RK.indexOf(s[0]) * 4 + SU.indexOf(s[1]); }
  function cstr(c) { return RK[c >> 2] + SU[c & 3]; }
  // ---- 7-card evaluator (bigger = better) ----
  function top5(m) { var r = 0, n = 0; for (var i = 12; i >= 0 && n < 5; i--) if (m >> i & 1) { r |= 1 << i; n++; } return r; }
  function sthi(m) { var x = (m << 1) | (m >> 12 & 1); for (var hi = 13; hi >= 4; hi--) { var w = 0x1F << (hi - 4); if ((x & w) === w) return hi; } return 0; }
  function hib(k) { return 31 - Math.clz32(k); }
  function eval7(cs) {
    var sm = [0, 0, 0, 0], all = 0, cnt = new Array(13).fill(0), i;
    for (i = 0; i < cs.length; i++) { var r = cs[i] >> 2, s = cs[i] & 3; sm[s] |= 1 << r; all |= 1 << r; cnt[r]++; }
    for (var s2 = 0; s2 < 4; s2++) if (popc(sm[s2]) >= 5) { var sh = sthi(sm[s2]); if (sh) return (8 << 20) | sh; return (5 << 20) | top5(sm[s2]); }
    var quad = -1, tr = [], pr = [];
    for (var r2 = 12; r2 >= 0; r2--) { if (cnt[r2] === 4) quad = r2; else if (cnt[r2] === 3) tr.push(r2); else if (cnt[r2] === 2) pr.push(r2); }
    if (quad >= 0) return (7 << 20) | (quad << 4) | hib(all & ~(1 << quad));
    if (tr.length && (tr.length > 1 || pr.length)) { var p = tr.length > 1 ? tr[1] : pr[0]; if (tr.length > 1 && pr.length && pr[0] > p) p = pr[0]; return (6 << 20) | (tr[0] << 4) | p; }
    var st = sthi(all); if (st) return (4 << 20) | st;
    var k, a, b;
    if (tr.length) { k = all & ~(1 << tr[0]); a = hib(k); k &= ~(1 << a); b = hib(k); return (3 << 20) | (tr[0] << 8) | (a << 4) | b; }
    if (pr.length >= 2) { k = all & ~(1 << pr[0]) & ~(1 << pr[1]); return (2 << 20) | (pr[0] << 8) | (pr[1] << 4) | hib(k); }
    if (pr.length === 1) { k = all & ~(1 << pr[0]); var t = 0, sh2 = 8; for (i = 0; i < 3; i++) { a = hib(k); k &= ~(1 << a); t |= a << sh2; sh2 -= 4; } return (1 << 20) | (pr[0] << 12) | t; }
    return top5(all);
  }
  function popc(x) { x = x - ((x >> 1) & 0x55555555); x = (x & 0x33333333) + ((x >> 2) & 0x33333333); return (((x + (x >> 4)) & 0x0F0F0F0F) * 0x01010101) >> 24; }
  var CAT = ['高牌', '一對', '兩對', '三條', '順子', '同花', '葫蘆', '四條', '同花順'];

  // ---- tree ----
  // cfg: pot, stack (effective, remaining at street start), oopBets, ipBets (pot fractions), raises (fraction of pot after call), maxRaises
  function buildTree(cfg) {
    var nodes = [], P = cfg.pot, S = cfg.stack, maxR = cfg.maxRaises == null ? 1 : cfg.maxRaises;
    var allinThr = cfg.allinThreshold == null ? 0.67 : cfg.allinThreshold;  // bet >= thr*remaining -> all-in
    function sizes(fracs, potNow, toCall, c, cOpp, nRaise) {
      var out = [], seen = {}; var rem = S - c; // chips left for this player
      fracs.forEach(function (f) {
        var to = (toCall === 0) ? c + f * potNow : cOpp + f * (potNow + toCall);   // bet: f*pot ; raise: call + f*(pot after call)
        if (f === 'allin' || to - c >= allinThr * rem || to >= S) to = S;
        to = Math.round(to * 100) / 100;
        if (to <= cOpp || to - c <= 0) return;
        if (!seen[to]) { seen[to] = 1; out.push({ to: to, allin: to >= S, frac: f }); }
      });
      return out.sort(function (x, y) { return x.to - y.to; });
    }
    function dec(pl, c0, c1, hist, nRaise, facing) {
      var n = { t: 'd', pl: pl, acts: [], kids: [], c: [c0, c1], hist: hist, id: nodes.length }; nodes.push(n);
      var c = pl === 0 ? c0 : c1, co = pl === 0 ? c1 : c0, potNow = P + c0 + c1, toCall = co - c;
      if (toCall > 0) {
        n.acts.push({ k: 'F', label: 'fold' }); n.kids.push({ t: 'f', winner: 1 - pl, c: [c0, c1] });
        n.acts.push({ k: 'C', label: 'call' }); n.kids.push({ t: 's', c: [co, co] });
        if (nRaise < maxR && co < S) {
          sizes(cfg.raises || [], potNow, toCall, c, co, nRaise).forEach(function (z) {
            var nc0 = pl === 0 ? z.to : c0, nc1 = pl === 1 ? z.to : c1;
            n.acts.push({ k: 'R', label: z.allin ? 'allin' : 'raise', to: z.to });
            n.kids.push(dec(1 - pl, nc0, nc1, hist + (z.allin ? 'A' : 'R'), nRaise + 1, true));
          });
        }
      } else {
        n.acts.push({ k: 'X', label: 'check' });
        if (pl === 0) n.kids.push(dec(1, c0, c1, hist + 'x', nRaise, false)); else n.kids.push({ t: 's', c: [c0, c1] });
        sizes(pl === 0 ? cfg.oopBets : cfg.ipBets, potNow, 0, c, co, nRaise).forEach(function (z) {
          var nc0 = pl === 0 ? z.to : c0, nc1 = pl === 1 ? z.to : c1;
          n.acts.push({ k: 'B', label: z.allin ? 'allin' : 'bet', to: z.to, frac: Math.round((z.to - c) / potNow * 100) / 100 });
          n.kids.push(dec(1 - pl, nc0, nc1, hist + (z.allin ? 'A' : 'B') + Math.round((z.to - c) / potNow * 100), nRaise, true));
        });
      }
      return n;
    }
    var rootN = dec(0, 0, 0, '', 0, false);
    return { root: rootN, nodes: nodes };
  }

  // ---- game setup ----
  // ranges: arrays of {c1,c2,w} (card ints; -1 for abstract hands with explicit rank `r`)
  function setup(spec) {
    var board = (spec.board || []).map(function (x) { return typeof x === 'string' ? card(x) : x; });
    var dead = {}; board.forEach(function (c) { dead[c] = 1; });
    var H = [[], []];
    for (var p = 0; p < 2; p++) {
      spec.ranges[p].forEach(function (h) {
        if (h.w <= 0) return;
        if (h.c1 >= 0 && (dead[h.c1] || dead[h.c2])) return;
        var r = h.r != null ? h.r : eval7(board.concat([h.c1, h.c2]));
        H[p].push({ c1: h.c1, c2: h.c2, w: h.w, r: r, tag: h.tag });
      });
    }
    var g = { board: board, H: H, N: [H[0].length, H[1].length] };
    // sorted order by rank, and same-combo index in the opponent list
    g.ord = H.map(function (hs) { return hs.map(function (_, i) { return i; }).sort(function (a, b) { return hs[a].r - hs[b].r; }); });
    g.same = [0, 1].map(function (p) {
      var o = H[1 - p], m = {}; o.forEach(function (h, j) { if (h.c1 >= 0) m[Math.min(h.c1, h.c2) * 64 + Math.max(h.c1, h.c2)] = j; });
      return H[p].map(function (h) { if (h.c1 < 0) return -1; var k = Math.min(h.c1, h.c2) * 64 + Math.max(h.c1, h.c2); return m[k] == null ? -1 : m[k]; });
    });
    return g;
  }
  // compat sums: for each hand of player p, sum of opponent reach over non-blocking hands
  function compatTot(g, p, ro, out) {
    var o = g.H[1 - p], tot = 0, cs = new Float64Array(52), i;
    for (i = 0; i < o.length; i++) { var x = ro[i]; tot += x; if (o[i].c1 >= 0) { cs[o[i].c1] += x; cs[o[i].c2] += x; } }
    var hs = g.H[p], sm = g.same[p];
    for (i = 0; i < hs.length; i++) { var h = hs[i]; var v = tot; if (h.c1 >= 0) v -= cs[h.c1] + cs[h.c2]; if (sm[i] >= 0) v += ro[sm[i]]; out[i] = v; }
    return out;
  }
  // showdown cfv for player p: win (pot+x)W - xL + pot/2 T, with equal contribution x
  function showdown(g, p, ro, pot, x, out) {
    var hs = g.H[p], o = g.H[1 - p], op = g.ord[p], oo = g.ord[1 - p], n = hs.length, m = o.length;
    var tot = 0, ct = new Float64Array(52), i, j;
    for (j = 0; j < m; j++) { tot += ro[j]; if (o[j].c1 >= 0) { ct[o[j].c1] += ro[j]; ct[o[j].c2] += ro[j]; } }
    var lt = 0, lc = new Float64Array(52), et = 0, ec = new Float64Array(52), pl = 0, pe = 0, sm = g.same[p];
    for (var k = 0; k < n; k++) {
      i = op[k]; var h = hs[i], R = h.r;
      while (pl < m && o[oo[pl]].r < R) { j = oo[pl++]; lt += ro[j]; if (o[j].c1 >= 0) { lc[o[j].c1] += ro[j]; lc[o[j].c2] += ro[j]; } }
      while (pe < m && o[oo[pe]].r <= R) { j = oo[pe++]; et += ro[j]; if (o[j].c1 >= 0) { ec[o[j].c1] += ro[j]; ec[o[j].c2] += ro[j]; } }
      var Wn = lt, Le = et, T0 = tot;
      if (h.c1 >= 0) { Wn -= lc[h.c1] + lc[h.c2]; Le -= ec[h.c1] + ec[h.c2]; T0 -= ct[h.c1] + ct[h.c2]; }
      if (sm[i] >= 0) { var s = ro[sm[i]]; Le += s; T0 += s; }
      var L = T0 - Le, Ti = Le - Wn;
      out[i] = (pot + x) * Wn - x * L + 0.5 * pot * Ti;
    }
    return out;
  }

  function Solver(spec) {
    this.spec = spec; this.g = setup(spec);
    var t = buildTree(spec); this.root = t.root; this.nodes = t.nodes; this.it = 0;
    var g = this.g, self = this;
    this.nodes.forEach(function (n) {
      var N = g.N[n.pl], A = n.acts.length;
      n.reg = []; n.ss = []; for (var a = 0; a < A; a++) { n.reg.push(new Float64Array(N)); n.ss.push(new Float64Array(N)); }
      n.lock = null;
    });
    this.w = [0, 1].map(function (p) { return Float64Array.from(g.H[p].map(function (h) { return h.w; })); });
  }
  Solver.prototype.strat = function (n, useAvg) {
    var N = this.g.N[n.pl], A = n.acts.length, S = [], a, i;
    if (n.lock) return n.lock;
    for (a = 0; a < A; a++) S.push(new Float64Array(N));
    var src = useAvg ? n.ss : n.reg;
    for (i = 0; i < N; i++) {
      var t = 0; for (a = 0; a < A; a++) { var v = src[a][i]; if (v > 0) t += v; }
      for (a = 0; a < A; a++) S[a][i] = t > 0 ? Math.max(src[a][i], 0) / t : 1 / A;
    }
    return S;
  };
  Solver.prototype.term = function (nd, p, ro) {
    var g = this.g, N = g.N[p], out = new Float64Array(N), pot = this.spec.pot;
    if (nd.t === 'f') {
      var cf = nd.c[1 - nd.winner], pay = nd.winner === p ? pot + cf : -nd.c[p];
      compatTot(g, p, ro, out); for (var i = 0; i < N; i++) out[i] *= pay; return out;
    }
    return showdown(g, p, ro, pot, nd.c[0], out);
  };
  // CFR traversal for traverser p; rp own reach, ro opponent reach
  Solver.prototype.cfr = function (n, p, rp, ro) {
    if (n.t !== 'd') return this.term(n, p, ro);
    var A = n.acts.length, N = this.g.N[p], a, i, S = this.strat(n, false), v = new Float64Array(N);
    if (n.pl === p) {
      var vals = [];
      for (a = 0; a < A; a++) {
        var r2 = new Float64Array(N); for (i = 0; i < N; i++) r2[i] = rp[i] * S[a][i];
        vals.push(this.cfr(n.kids[a], p, r2, ro));
        for (i = 0; i < N; i++) v[i] += S[a][i] * vals[a][i];
      }
      if (!n.lock) {
        var t = this.it, pos = Math.pow(t, 1.5) / (Math.pow(t, 1.5) + 1), gw = Math.pow(t / (t + 1), 2);
        for (a = 0; a < A; a++) {
          var R = n.reg[a], SS = n.ss[a], va = vals[a], sa = S[a];
          for (i = 0; i < N; i++) { var r = R[i]; r *= r > 0 ? pos : 0.5; R[i] = r + va[i] - v[i]; SS[i] = SS[i] * gw + rp[i] * sa[i]; }
        }
      }
      return v;
    }
    var M = this.g.N[n.pl];
    for (a = 0; a < A; a++) {
      var r3 = new Float64Array(M); for (i = 0; i < M; i++) r3[i] = ro[i] * S[a][i];
      var c = this.cfr(n.kids[a], p, rp, r3); for (i = 0; i < N; i++) v[i] += c[i];
    }
    return v;
  };
  Solver.prototype.iterate = function (k) {
    for (var j = 0; j < k; j++) { this.it++; for (var p = 0; p < 2; p++) this.cfr(this.root, p, this.w[p], this.w[1 - p]); }
  };
  // value traversal: mode 'avg' (both average) or best response for p
  Solver.prototype.val = function (n, p, ro, br) {
    if (n.t !== 'd') return this.term(n, p, ro);
    var A = n.acts.length, N = this.g.N[p], a, i, v;
    if (n.pl === p) {
      var vals = []; for (a = 0; a < A; a++) vals.push(this.val(n.kids[a], p, ro, br));
      v = new Float64Array(N);
      if (br && !n.lock) { for (i = 0; i < N; i++) { var m = -1e300; for (a = 0; a < A; a++) if (vals[a][i] > m) m = vals[a][i]; v[i] = m; } }
      else { var S = this.strat(n, true); for (a = 0; a < A; a++) for (i = 0; i < N; i++) v[i] += S[a][i] * vals[a][i]; }
      n._v = n._v || []; n._v[p] = vals;   // per-action cfvs (last computed) for EV display
      return v;
    }
    var S2 = this.strat(n, true), M = this.g.N[n.pl]; v = new Float64Array(N);
    for (a = 0; a < A; a++) { var r3 = new Float64Array(M); for (i = 0; i < M; i++) r3[i] = ro[i] * S2[a][i]; var c = this.val(n.kids[a], p, r3, br); for (i = 0; i < N; i++) v[i] += c[i]; }
    return v;
  };
  Solver.prototype.norm = function () { // total compatible pair weight
    var g = this.g, out = new Float64Array(g.N[0]); compatTot(g, 0, this.w[1], out); var s = 0; for (var i = 0; i < out.length; i++) s += this.w[0][i] * out[i]; return s;
  };
  Solver.prototype.exploitability = function () {
    var Z = this.norm(), res = {}, self = this, pot = this.spec.pot;
    var ev = [0, 1].map(function (p) { var v = self.val(self.root, p, self.w[1 - p], false); var s = 0; for (var i = 0; i < v.length; i++) s += self.w[p][i] * v[i]; return s / Z; });
    var br = [0, 1].map(function (p) { var v = self.val(self.root, p, self.w[1 - p], true); var s = 0; for (var i = 0; i < v.length; i++) s += self.w[p][i] * v[i]; return s / Z; });
    res.ev = ev; res.br = br; res.exploit = (br[0] + br[1] - pot) / 2; res.exploitPct = 100 * res.exploit / pot;
    res.gain = [br[0] - ev[0], br[1] - ev[1]];
    return res;
  };
  Solver.prototype.solve = function (opt) {
    opt = opt || {}; var maxIt = opt.iters || 1000, chk = opt.check || 100, tgt = opt.target == null ? 0.2 : opt.target, hist = [];
    while (this.it < maxIt) {
      this.iterate(chk); var e = this.exploitability(); hist.push([this.it, e.exploitPct]);
      if (opt.onProgress) opt.onProgress(this.it, e.exploitPct);
      if (e.exploitPct < tgt) break;
    }
    this.hist = hist; return hist;
  };
  // per-node reach-weighted summary + per-hand strategies (average)
  Solver.prototype.report = function () {
    var self = this, g = this.g, out = [];
    function rec(n, r) {
      if (n.t !== 'd') return;
      var S = self.strat(n, true), p = n.pl, N = g.N[p], a, i, tot = 0, fr = n.acts.map(function () { return 0; });
      // reach of acting player at this node: r[p]; the opponent reach for blocker-aware frequencies is ignored here (range-level freq)
      for (i = 0; i < N; i++) { tot += r[p][i]; for (a = 0; a < n.acts.length; a++) fr[a] += r[p][i] * S[a][i]; }
      var to = 0; for (i = 0; i < r[1 - p].length; i++) to += r[1 - p][i];
      out.push({ id: n.id, hist: n.hist, pl: p, acts: n.acts, freq: fr.map(function (x) { return tot > 0 ? x / tot : 0; }), reachW: tot, reachOpp: to, reach: r[p].slice(), S: S, c: n.c });
      for (a = 0; a < n.acts.length; a++) {
        var rr = [r[0], r[1]]; var nr = new Float64Array(N); for (i = 0; i < N; i++) nr[i] = r[p][i] * S[a][i]; rr[p] = nr; rec(n.kids[a], rr);
      }
    }
    rec(this.root, [this.w[0], this.w[1]]);
    return out;
  };
  // EV of each hand at root (chips) under average strategies, normalised by compatible opponent weight
  Solver.prototype.handEV = function (p) {
    var v = this.val(this.root, p, this.w[1 - p], false), ct = new Float64Array(v.length); compatTot(this.g, p, this.w[1 - p], ct);
    return Array.from(v).map(function (x, i) { return ct[i] > 0 ? x / ct[i] : 0; });
  };
  // per-action EVs for player p at node n (requires val() run, uses n._v), normalised by compat weight of opp reach at node
  // per-node, per-action EVs (chips, relative to street start) for the acting player under average strategies,
  // normalised by the compatible opponent reach arriving at that node
  Solver.prototype.nodeEVs = function () {
    var self = this, g = this.g, out = {};
    this.val(this.root, 0, this.w[1], false); this.val(this.root, 1, this.w[0], false);
    function rec(n, r) {
      if (n.t !== 'd') return;
      var p = n.pl, N = g.N[p], ct = new Float64Array(N); compatTot(g, p, r[1 - p], ct);
      out[n.id] = n._v[p].map(function (va) { return Array.from(va).map(function (x, i) { return ct[i] > 1e-12 ? x / ct[i] : null; }); });
      var S = self.strat(n, true);
      for (var a = 0; a < n.acts.length; a++) { var rr = [r[0], r[1]], nr = new Float64Array(N); for (var i = 0; i < N; i++) nr[i] = r[p][i] * S[a][i]; rr[p] = nr; rec(n.kids[a], rr); }
    }
    rec(this.root, [this.w[0], this.w[1]]);
    return out;
  };
  Solver.prototype.lockNode = function (n, S) { n.lock = S; };

  var api = { card: card, cstr: cstr, eval7: eval7, CAT: CAT, buildTree: buildTree, setup: setup, Solver: Solver, compatTot: compatTot };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.RiverSolver = api;
})(typeof window !== 'undefined' ? window : this);
