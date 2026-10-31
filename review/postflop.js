/* 翻後覆盤（全部場次）：報告＋錯題測驗。資料 window.PR（data/postflop.js，由 TexasSolver 逐街解算產生）。 */
(function () {
'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const fbb = x => String(Math.round(x * 10) / 10);
const sg = x => (x > 0 ? '+' : '') + x;
const SU = {h: '♥', d: '♦', c: '♣', s: '♠'};
const cardHTML = c => `<span class="cd ${c[1]}">${c[0] === 'T' ? '10' : c[0]}<i>${SU[c[1]]}</i></span>`;
const LS = {get(k, d) { try { const v = localStorage.getItem('pk8.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('pk8.' + k, JSON.stringify(v)); } catch (e) {} }};
const P = window.PR;
$('#topnav').innerHTML = '<a class="topb" href="index.html" style="text-decoration:none;text-align:center">← 覆盤列表</a><a class="topb" data-view="rep" href="#rep" style="text-decoration:none;text-align:center">報告</a><a class="topb" data-view="quiz" href="#quiz" style="text-decoration:none;text-align:center">測驗</a>';
const st = document.createElement('style');
st.textContent = '.dn-d{display:none}@media (min-width:1024px){#qc .dn-d{display:inline-block}#qc .dn-m{display:none}.qcard#qc{display:grid;grid-template-columns:1fr 1fr;gap:12px}#qc>.opts,#qc>.qhd{grid-column:1/-1}}html.rv-quiz #rep{display:none}html.rv-rep #quizsec{display:none}html.rv-quiz #quizsec{border:0;padding:0;background:none;margin:0}.qL .opts{margin:6px 0}table.t td.r,table.t th.r{text-align:right}';
document.head.appendChild(st);
function view() { const q = location.hash === '#quiz'; const c = document.documentElement.classList; c.toggle('rv-quiz', q); c.toggle('rv-rep', !q);
  document.querySelectorAll('#topnav [data-view]').forEach(a => a.classList.toggle('on', a.dataset.view === (q ? 'quiz' : 'rep'))); }
view(); window.addEventListener('hashchange', () => { view(); window.scrollTo(0, 0); });

// ---- replay ----
const STZ = {pre: '翻牌前', flop: '翻牌', turn: '轉牌', river: '河牌'}, BN = {pre: 0, flop: 3, turn: 4, river: 5};
const who = p => p === 'Hero' ? '你' : p;
function aTxt(a) { const k = a[2], x = a[3], ai = a[4];
  if (k === 'fold') return '棄牌'; if (k === 'check') return a[0] === 'pre' && a[1] !== 'BB' ? '補盲 1（過牌）' : '過牌';
  if (ai) return k === 'call' ? `跟注 ${fbb(x)}（全下）` : `全下 ${fbb(x)}`;
  return k === 'call' ? `跟注 ${fbb(x)}` : k === 'bet' ? `下注 ${fbb(x)}` : `加注到 ${fbb(x)}`; }
function logHTML(h, upto, reveal) {
  const end = reveal ? h.acts.length : upto; let html = '', s0 = null;
  const sm = 'style="width:30px;height:40px;font-size:16px" class="cd';
  for (let i = 0; i < end; i++) { const a = h.acts[i];
    if (a[2] === 'fold' && a[0] === 'pre' && a[1] !== 'Hero') continue;
    if (a[0] !== s0) { s0 = a[0]; html += `<div class="st">${STZ[s0]}${BN[s0] ? '　' + h.board.slice(0, BN[s0]).map(cardHTML).join('').replace(/class="cd/g, sm) : ''}　<span class="muted">底池 ${fbb(h.pots[i])}bb</span></div>`; }
    html += `<span class="a ${a[1] === 'Hero' ? 'me' : ''}">${esc(who(a[1]))} ${aTxt(a)}</span>`; }
  if (!reveal) { const a = h.acts[upto];
    if (a[0] !== s0) html += `<div class="st">${STZ[a[0]]}　<span class="muted">底池 ${fbb(h.pots[upto])}bb</span></div>`;
    html += '<span class="a q">你 ？</span>'; }
  return `<div class="alog">${html}</div>`; }

// ---- report ----
function report() {
  const S = P.sum;
  return `<div id="rep"><div class="rvh">翻後覆盤・全部場次</div>
  <div class="muted small">${esc(P.title)}</div>
  <div class="sec"><div class="kpi">
    <div><span class="muted">翻後 solver 可量化損失</span><b>−${S.post_loss}bb</b><span class="muted">${S.n_hands} 手單挑大底池・${S.n_dec} 個決定</span></div>
    <div><span class="muted">翻前損失（同 ${S.hands} 手）</span><b>−${S.pre_loss}bb</b><span class="muted">${S.pre_dec} 個翻前決定</span></div>
    <div><span class="muted">攤牌 / 沒攤牌贏</span><b>${sg(S.sd)} / ${sg(S.nsd)}bb</b><span class="muted">沒攤牌＝翻前 ${S.nsd_pre}・翻後 ${sg(S.nsd_post)}</span></div></div>
    <ul>${P.concl.map(x => `<li class="small">${x}</li>`).join('')}</ul></div>
  <div class="sec"><b>損失分類（solver）</b><div class="tw"><table class="t st" style="margin-top:6px"><tr><th>類別</th><th class="r">決定</th><th class="r">錯</th><th class="r">損失 bb</th><th>例子</th></tr>
    ${P.cats.map(c => `<tr><td>${esc(c[0])}</td><td class="r">${c[1]}</td><td class="r">${c[2]}</td><td class="r">${c[3]}</td><td class="small">${esc(c[4])}</td></tr>`).join('')}</table></div></div>
  <div class="sec"><b>最常見的漏洞</b>${P.leaks.map(l => `<div class="lrow"><b>${esc(l.t)}</b><div class="small">${l.p}</div><div class="note" style="margin-top:4px">修正：${esc(l.fix)}</div></div>`).join('')}</div>
  <div class="sec"><b>多人／limp 底池（依原則，非 solver）</b><div class="tw"><table class="t st" style="margin-top:6px"><tr><th>手</th><th>牌</th><th>問題</th></tr>
    ${P.mw.map(m => `<tr><td class="small">${esc(m.day)}<br>${esc(m.id)}</td><td>${esc(m.cards)}<br><span class="muted small">${esc(m.board)}</span></td><td class="small">${esc(m.note)}</td></tr>`).join('')}</table></div></div>
  <div class="sec"><b>方法</b><ul>${P.method.map(x => `<li class="small">${x}</li>`).join('')}</ul></div>
  <div class="sec"><a class="btn" href="#quiz">去測驗（${P.drill.length} 題）→</a></div></div>`;
}

// ---- quiz ----
const KEY = 'rv.postflop.v1';
const S = Object.assign({q: null, right: 0, wrong: 0}, LS.get(KEY, {}));
if (!Array.isArray(S.q) || S.q.some(k => k >= P.drill.length)) S.q = P.drill.map((_, i) => i);
const save = () => LS.set(KEY, S);
let CUR = null;
const kcls = k => /^(CHECK|CALL)/.test(k) ? 'k-call' : k === 'FOLD' ? 'k-fold' : /ALLIN|全下/.test(k) ? 'k-jam' : 'k-bet';
function head(it) { const h = it.hand, b = h.board.slice(0, BN[h.acts[it.at][0]]);
  return `<div class="qL"><div class="tags">${it.sv ? '<span class="tag v-exp">solver（TexasSolver）</span>' : '<span class="tag np">依原則（多人底池，非 solver）</span>'}<span class="tag">${esc(it.cat)}</span><span class="tag">${esc(it.day)}・${esc(h.id)}</span></div>
    <div class="hand">${h.cards.map(cardHTML).join('')}<span class="muted">你在 <b>${h.pos}</b>・${esc(it.ctx)}</span></div>
    ${b.length ? `<div class="bd">${b.map(cardHTML).join('')}</div>` : ''}${logHTML(h, it.at, false)}
    <div class="small">輪到你：底池 <b>${fbb(h.pots[it.at])}bb</b>${h.tocall[it.at] > 0 ? `，要跟 <b>${fbb(h.tocall[it.at])}bb</b>` : ''}・有效籌碼 ${fbb(it.eff)}bb</div>`; }
function opts(it) { return `<div class="opts">${it.opts.map(o => `<button class="ab ${kcls(o[0])}" data-a="${esc(o[0])}">${esc(o[1])}</button>`).join('')}</div>`; }
function grade(it, a) { return it.ok.includes(a) ? 'ok' : 'bad'; }
function reveal(it, a) {
  const r = grade(it, a), lbl = k => (it.opts.find(o => o[0] === k) || [k, k])[1];
  let tbl = '';
  if (it.sv) { const best = Math.max(...it.opts.map(o => it.ev[o[0]]));
    tbl = `<table class="evt"><tr><th>動作</th><th>頻率</th><th>EV 差</th></tr>${it.opts.map(o => { const k = o[0], d = it.ev[k] - best, f = Math.round(it.fq[k] * 100);
      return `<tr class="${k === a ? 'me' : ''} ${it.ok.includes(k) ? 'okr' : ''}"><td>${esc(o[1])}${k === a ? ' ← 你選' : ''}${k === it.you ? '・實戰' : ''}</td><td><span class="fb"><span style="width:${f}%;background:#3ecf7a"></span></span>${f}%</td><td>${d > -0.05 ? '最佳' : d.toFixed(1) + 'bb'}</td></tr>`; }).join('')}</table>`; }
  const sd = Object.entries(it.hand.shows || {}).filter(([p]) => p !== 'Hero').map(([p, c]) => `${esc(p)} 亮 ${c.map(cardHTML).join('')}`).join('　');
  return `<div class="qR"><div class="res ${r}"><div class="rh">${r === 'bad' ? '✗ 不對' : '✓ 對'}</div>
    <div class="small">你選：${esc(lbl(a))}　｜　實戰：<b>${esc(lbl(it.you))}</b>${it.loss ? `（少約 ${it.loss}bb）` : ''}</div>
    <div class="small">建議：<b>${it.ok.map(lbl).map(esc).join(' 或 ')}</b></div><div class="small" style="margin-top:4px">${it.why}</div></div>${tbl}
    <details style="margin-top:6px"><summary>後來怎麼了</summary>${it.hand.board.length ? `<div class="bd">${it.hand.board.map(cardHTML).join('')}</div>` : ''}${logHTML(it.hand, 0, true)}${sd ? `<div class="small">攤牌：${sd}</div>` : ''}<div class="small">你這手：<b>${sg(it.hand.net)}bb</b></div></details>
    <button class="btn dn-m" data-dnext="1" style="margin-top:8px">下一題 →</button></div>`; }
function render() {
  const n = P.drill.length; let body;
  if (!S.q.length) { body = `<div class="qcard"><div class="rh big">全部答對 🎉</div><p>答對 ${S.right}、答錯 ${S.wrong}。</p><button class="btn" data-reset="1">重新開始</button></div>`; CUR = null; }
  else { const k = S.q[0], it = P.drill[k];
    if (!(CUR && CUR.k === k)) CUR = {k, it};
    body = `<div class="row sp"><span class="prog">剩 ${S.q.length} / ${n} 題・對 ${S.right}・錯 ${S.wrong}</span><button class="btn sm" data-reset="1">重來</button></div>
      <div class="qcard" id="qc">${CUR.a ? head(it) + '<button class="btn dn-d" data-dnext="1" style="margin-top:8px">下一題 →</button></div>' + reveal(it, CUR.a) : head(it) + '</div>' + opts(it)}</div>`; }
  if (CUR) { const h = CUR.it.hand, up = CUR.it.at; window.__Q = {drill: 'rvpost', id: h.id + '|' + up, hero: h.cards.join(''), board: h.board.slice(0, BN[h.acts[up][0]]).join(''), full: h.board.join(''), real: true, role: ['real', ''], st: h.acts[up][0], seen: [...new Set(h.acts.slice(0, up).filter(a => !(a[2] === 'fold' && a[0] === 'pre' && a[1] !== 'Hero')).map(a => a[0]))]}; }
  $('#quiz').innerHTML = body;
}
function answer(a) { if (!CUR || CUR.a) return; CUR.a = a; CUR.r = grade(CUR.it, a); if (CUR.r === 'bad') S.wrong++; else S.right++; save(); render(); }
function dnext() { if (!CUR || !CUR.a) return; const k = S.q.shift(); if (CUR.r === 'bad') S.q.splice(Math.min(3, S.q.length), 0, k); CUR = null; save(); render(); }
$('#app').innerHTML = report() + `<div class="sec" id="quizsec"><div id="quiz"></div></div>`;
render();
document.addEventListener('click', e => { const t = e.target.closest('button'); if (!t) return;
  if (t.dataset.a) answer(t.dataset.a); else if (t.dataset.dnext) dnext();
  else if (t.dataset.reset) { S.q = P.drill.map((_, i) => i); S.right = S.wrong = 0; CUR = null; save(); render(); } });
})();
