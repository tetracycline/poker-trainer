(function(){
const R = window.NL2, H = window.HWR, $ = s => document.querySelector(s), app = $('#app');
const RK = '23456789TJQKA', SU = {s: '♠', h: '♥', d: '♦', c: '♣'};
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const cd = c => `<span class="cd ${c[1] === 'h' ? 'r' : c[1] === 'd' ? 'd' : c[1] === 'c' ? 'c' : ''}">${c[0] === 'T' ? '10' : c[0]}${SU[c[1]]}</span>`;
const pretty = cs => cs.map(c => (c[0] === 'T' ? '10' : c[0]) + SU[c[1]]).join('');
// ---------- 規則卡 ----------
function card() {
  window.__Q = null;
  app.innerHTML = `<div class="sec"><b class="h">NL2 規則卡（${esc(R.ver)}）</b><p class="small muted">${esc(R.scope)}<br>${esc(R.bias)}<br>每條規則：觀察＝你的手牌；數據＝玩家池（括號是 n 和誤差）；規則＝要做什麼；最後是練習的地方。翻前的規則跟網站翻前表一致，翻後的規則跟「行動線」題一致；這頁只有「河牌一對依尺寸」是新的題目。</p></div>` +
   R.rules.map((r, i) => `<div class="sec"><b class="h">${i + 1}. ${esc(r.t)}</b><span class="ev">${esc(r.ev)}</span>
   <p><span class="lab">觀察</span>　${esc(r.obs)}</p><div><span class="lab">數據</span><ul>${r.data.map(d => `<li class="small">${esc(d)}</li>`).join('')}</ul></div>
   <p><span class="lab">規則</span>　<b>${esc(r.rule)}</b></p><div>${r.go.map(([h, t]) => `<a class="btn" href="${h}">${esc(t)}</a>`).join('')}</div></div>`).join('') +
   `<div class="sec small muted">覆盤：<a href="review/2026-11-04.html">11/4 覆盤＋11/5 大數據診斷</a></div>`;
}
// ---------- 牌力 ----------
function cat7(cs) { // 'str'|'flush'|'quads'|'boat'|'trips'|'two'|'pair'|'high'
  const rc = {}, sc = {}; cs.forEach(c => { rc[c[0]] = (rc[c[0]] || 0) + 1; sc[c[1]] = (sc[c[1]] || 0) + 1; });
  if (Object.values(sc).some(v => v >= 5)) return 'flush';
  const rs = new Set(cs.map(c => RK.indexOf(c[0]))); if (rs.has(12)) rs.add(-1);
  for (let lo = -1; lo <= 8; lo++) { let ok = true; for (let k = 0; k < 5; k++) if (!rs.has(lo + k)) { ok = false; break; } if (ok) return 'str'; }
  const v = Object.values(rc).sort((a, b) => b - a);
  if (v[0] >= 3) return 'trips+'; if (v[0] === 2 && v[1] === 2) return 'two'; if (v[0] === 2) return 'pair'; return 'high';
}
function deck() { const d = []; for (const r of RK) for (const s of 'shdc') d.push(r + s); return d; }
function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function combos(lab) { const a = lab[0], b = lab[1], out = []; const S = 'shdc';
  if (a === b) { for (let i = 0; i < 4; i++) for (let j = i + 1; j < 4; j++) out.push([a + S[i], b + S[j]]); }
  else if (lab[2] === 's') { for (const s of S) out.push([a + s, b + s]); }
  else { for (const s of S) for (const t of S) if (s !== t) out.push([a + s, b + t]); } return out; }
// ---------- 河牌一對題 ----------
const OPN = ['CO', 'BTN'];
let Q = null, n = 0;
function classify(hero, board) {
  if (cat7(hero.concat(board)) !== 'pair' || cat7(board) !== 'high') return null;
  const hr = hero.map(c => RK.indexOf(c[0])), br = board.map(c => RK.indexOf(c[0])), top = Math.max(...br);
  if (hr[0] === hr[1]) return null; // 口袋對子另算（超對/低對），這題只出頂對、中小對
  const p = hr.find(h => br.includes(h)); if (p == null) return null;
  return p === top ? 'top' : 'mid';
}
function verdict(c, sk) { const [w, nn] = R.river[c][sk], need = R.river.sizes.find(s => s[0] === sk)[3], ci = 1.96 * Math.sqrt(w / 100 * (1 - w / 100) / nn) * 100;
  return {w, n: nn, need, ci: Math.round(ci * 10) / 10, ok: w - need > ci ? ['c'] : need - w > ci ? ['f'] : ['c', 'f']}; }
function newQ() {
  const op = OPN[Math.floor(Math.random() * OPN.length)], node = op + 'open>BB', rng = (H.call[node] || []).filter(h => h[0] !== h[1]);
  const want = Math.random() < 0.55 ? 'top' : 'mid';
  for (let t = 0; t < 400; t++) {
    const lab = rng[Math.floor(Math.random() * rng.length)], cs = combos(lab), hero = cs[Math.floor(Math.random() * cs.length)];
    const d = shuffle(deck().filter(c => !hero.includes(c))), board = d.slice(0, 5);
    const c = classify(hero, board); if (c !== want) continue;
    const sz = R.river.sizes[Math.floor(Math.random() * R.river.sizes.length)], pot = 5.5, bet = Math.round(pot * sz[2] * 10) / 10;
    return {id: 'nl2r' + (++n), drill: 'nl2river', hero: hero.join(' '), board: board.join(' '), role: ['call', node], op, lab, c, sk: sz[0], szl: sz[1], bet, pot, v: verdict(c, sz[0])};
  }
  return newQ();
}
function grid(node, me) { const L = H.call[node] || [], T = (H.tb || {})[node] || []; let h = '';
  for (let i = 12; i >= 0; i--) for (let j = 12; j >= 0; j--) { const a = RK[Math.max(i, j)], b = RK[Math.min(i, j)], lab = i === j ? a + a : (j < i ? a + b + 's' : a + b + 'o');
    h += `<i class="${L.includes(lab) || T.includes(lab) ? 'in' : ''}${lab === me ? ' me' : ''}">${lab}</i>`; }
  return `<div class="grid">${h}</div>`; }
function table(q) { const S = R.river.sizes;
  const row = (c, name) => `<tr><th>${name}</th>${S.map(s => { const v = verdict(c, s[0]), k = v.ok.length > 1 ? 'b' : v.ok[0]; return `<td class="${k}${c === q.c && s[0] === q.sk ? ' me' : ''}">${k === 'c' ? '跟' : k === 'f' ? '棄' : '都可'}<br><span class="small">${v.w}%/${v.need}%</span></td>`; }).join('')}</tr>`;
  return `<table class="rt"><tr><th></th>${S.map(s => `<th>${s[1]}</th>`).join('')}</tr>${row('top', '頂對')}${row('mid', '中小對')}</table><p class="small muted">格子＝玩家池跟注者勝率／需要勝率。差距小於誤差（約 ±4%）就算「都可」。</p>`; }
function river() {
  const q = Q = newQ(), h = q.hero.split(' '), b = q.board.split(' ');
  app.innerHTML = `<div id="qbox" class="sec"><p class="qs">你在 BB，單挑。你的牌 ${pretty(h)}，河牌對手下注，你要跟還是棄？</p>
  <div class="cards">${h.map(cd).join('')}　${b.map(cd).join('')}</div>
  <p class="line">翻前：${q.op} 開池 2.5bb，SB 棄，BB 跟（底池 5.5bb）</p>
  <p class="line">翻牌 ${pretty(b.slice(0, 3))}：BB 過牌，${q.op} 過牌</p>
  <p class="line">轉牌 ${pretty(b.slice(3, 4))}：BB 過牌，${q.op} 過牌</p>
  <p class="line">河牌 ${pretty(b.slice(4))}：BB 過牌，${q.op} 下注 ${q.bet}bb（${q.szl}）</p>
  <div class="abar"><button class="ab" data-a="f">棄牌</button><button class="ab" data-a="c">跟注 ${q.bet}bb</button></div></div><div id="ans"></div>`;
  window.__Q = q;
  app.querySelectorAll('.ab').forEach(e => e.onclick = () => answer(e.dataset.a, e));
}
function answer(a, el) {
  const q = Q; if (q.done) return; q.done = 1; const v = q.v, ok = v.ok.includes(a);
  app.querySelectorAll('.ab').forEach(e => { if (v.ok.includes(e.dataset.a)) e.classList.add('good'); });
  el.classList.add('pick');
  const name = q.c === 'top' ? '頂對' : '中小對', act = v.ok.length > 1 ? '跟或棄都可以（打平）' : v.ok[0] === 'c' ? '跟注' : '棄牌';
  const sig = v.ok.length > 1 ? '差距在誤差內，不明顯' : '差距大於誤差，顯著';
  $('#ans').innerHTML = `<div class="sec"><p class="res ${ok ? 'ok' : 'no'}">${ok ? '✓ 正確' : '✗ 不對'}：${act}</p><button class="nx" data-next>下一題 →</button>
  <p class="small">你是<b>${name}</b>，對手下 ${q.szl}。玩家池（BB 面對 BTN/CO 等所有位置的河牌單挑第一注）跟注者攤牌勝率 ${v.w}%（n=${v.n}，±${v.ci}%），需要 ${v.need}% → ${sig}。</p>
  <p class="small muted">你自己：11/2 之後河牌面對 >½ 池跟注 20 次，平均 −19.4±15bb；面對 ≤½ 池跟 17 次，−0.1±9.7bb。</p>
  ${table(q)}<p class="small muted">BB 對 ${q.op} 開池的跟注範圍（框起來的是這手 ${q.lab}）：</p>${grid(q.role[1], q.lab)}</div>`;
}
// ---------- 路由 ----------
function route() { const t = (location.hash || '#card').slice(1) === 'river' ? 'river' : 'card';
  document.querySelectorAll('.topb').forEach(e => e.classList.toggle('on', e.dataset.t === t));
  t === 'river' ? river() : card(); }
window.__QNEXT = () => river();
app.addEventListener('click', e => { if (e.target.closest('[data-next]')) river(); });
window.addEventListener('hashchange', route); route();
})();
