/* 對手範圍：池子對手在某牌面＋行動線後的範圍，你各牌型勝率 vs GTO。資料 eq_data.js（window.EQD） */
(function(){
const D=window.EQD||{};
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const POTS=[
 ['SRP|OOP','單一加注','你開池・對手 BB'],
 ['SRP|IP','單一加注','你在 BB・對手開池'],
 ['3BP|OOP','3bet 底池','你跟 3bet・對手 3bet'],
 ['3BP|IP','3bet 底池','你 3bet・對手跟注']];
const TEX=[['A_high','A 高'],['KQ_high','K/Q 高'],['mid_high','J/T 高'],['low','9 以下'],['paired','對子面'],['mono','單色'],['ALL','全部牌面']];
const TEXZ=Object.fromEntries(TEX);
const CLS=[['S','兩對以上'],['OP','超對'],['TP','頂對'],['MP','中對'],['DR','聽牌']];
const CLZ=Object.fromEntries(CLS);
const ACT={x:'過牌',b:'下注',c:'跟注',r:'加注'};
const STR=['翻牌','轉牌','河牌'];
const NOTE=`<div class="note eqnote">勝率只看方向（他比 GTO 強還是弱），不是 EV。亮色＝明顯偏離，其餘照 GTO 打。</div>`;
const E={pot:null,tex:null,line:[],quiz:false,q:null,score:[0,0]};
// lines available for a pot (any texture)
function lines(pot){const s=new Set();for(const k in D){const p=k.split('|');if(p[0]+'|'+p[1]===pot)s.add(p[2])}return [...s]}
function toks(l){return l.split('/').map(s=>s.split(' '))}
function actor(oppRole,si,ti){const role=ti%2===0?'OOP':'IP';return role===oppRole?'opp':'me'}
function oppName(pot){return ({'SRP|OOP':'BB','SRP|IP':'開池者','3BP|OOP':'3bettor','3BP|IP':'跟注者'})[pot]}
function lineStr(pot,l){const opp=pot.split('|')[1];return toks(l).map((ts,si)=>STR[si]+' '+ts.map((t,ti)=>(actor(opp,si,ti)==='opp'?'他':'你')+ACT[t]).join('→')).join('・')}
// what to do vs this line for a class, given direction (d>0 = 你勝率比 GTO 高 = 他偏弱)
function ctx(pot,l){const opp=pot.split('|')[1];const st=toks(l);const si=st.length-1;const ts=st[si];const t=ts[ts.length-1];
 const closes=(t==='c')||(t==='x'&&opp==='IP'&&ts.length>=2&&ts[ts.length-2]==='x');
 if(t==='b'||t==='r')return {k:'cf',s:si};
 if(!closes)return {k:'bx',s:si};
 return {k:'next',s:si,t}}
function advice(pot,l,d){const c=ctx(pot,l);const w=d>0;
 if(c.k==='cf')return w?'多跟注（他偏弱）':'多棄牌（他偏強）';
 if(c.k==='bx')return w?STR[c.s]+'下注拿價值':STR[c.s]+'多過牌、別亂打';
 if(c.s<2)return w?STR[c.s+1]+'下注拿價值':STR[c.s+1]+'多過牌、控池';
 if(c.t==='c')return w?'他河牌跟得偏弱 → 河牌多下注拿價值':'他河牌跟注偏強 → 河牌少薄價值';
 return w?'他河牌過牌偏弱 → 河牌你多下注拿價值':'他河牌過牌不弱 → 河牌多過牌';}
function qopts(pot,l){return ctx(pot,l).k==='cf'?[['c','跟注'],['f','棄牌']]:[['b','下注'],['x','過牌']]}
function qans(pot,l,d){return ctx(pot,l).k==='cf'?(d>0?'c':'f'):(d>0?'b':'x')}
function qask(pot,l){const c=ctx(pot,l);if(c.k==='cf')return '他下注，你跟還是棄？';if(c.k==='bx')return '輪到你，下注還是過牌？';return c.s<2?STR[c.s+1]+'你先動，下注還是過牌？':'這條線，河牌你該下注還是過牌？'}
function pct(e){return e[0]===e[1]?e[0]+'%':e[0]+'–'+e[1]+'%'}
function dir(e){return e[3]?(e[0]>e[2]?1:-1):0}
function btns(arr,cur,attr){return '<div class="eqb">'+arr.map(([k,t,s])=>`<button class="eqbtn${k===cur?' on':''}" data-${attr}="${esc(k)}">${esc(t)}${s?`<small>${esc(s)}</small>`:''}</button>`).join('')+'</div>'}
function card(pot,l,tex){const c=D[`${pot}|${l}|${tex}`];if(!c)return '';
 let o=`<div class="sec eqcard"><div class="eqln">${esc(lineStr(pot,l))}・${esc(TEXZ[tex])}</div>`;
 if(c.s==='few')o+=`<div class="eqgrey">樣本不足<small>只有 ${c.sd||0} 次攤牌</small></div>`;
 else if(c.s==='nogto')o+=`<div class="eqgrey">GTO 不走這條線<small>沒得比・${c.sd||0} 次攤牌</small></div>`;
 else if(c.s==='nocmp')o+=`<div class="eqgrey">GTO 不走這條線<small>解算器這裡只有全下加注・沒得比</small></div>`;
 else{for(const [k,z] of CLS){const e=c.e[k];if(!e)continue;const d=dir(e);
   o+=`<div class="eqrow${d?' sig '+(d>0?'up':'dn'):''}"><div class="eqt">你的${z} 勝率 <b>${pct(e)}</b>（GTO ${e[2]}%）${d?'→ '+esc(advice(pot,l,d)):'<span class="muted">→ 照 GTO 打</span>'}</div></div>`}
  o+=`<div class="eqsd">${c.sd} 次攤牌</div>`}
 return o+'</div>'}
function sigList(){const r=[];for(const k in D){const c=D[k];if(c.s!=='ok')continue;const [sp,pl,l,tex]=k.split('|');for(const cl in c.e){const e=c.e[cl];if(e[3])r.push({pot:sp+'|'+pl,l,tex,cl,e})}}return r}
function quizHtml(){const L=sigList();if(!E.q)E.q=L[Math.floor(Math.random()*L.length)];const q=E.q;const pz=POTS.find(p=>p[0]===q.pot);
 let o=`<div class="sec eqcard"><div class="eqln">${esc(pz[1])}・${esc(pz[2])}・${esc(TEXZ[q.tex])}</div><div class="eqq">${esc(lineStr(q.pot,q.l))}</div><div class="eqq">你拿 <b>${CLZ[q.cl]}</b>・${esc(qask(q.pot,q.l))}</div>`;
 if(!q.a)o+='<div class="eqb">'+qopts(q.pot,q.l).map(([k,t])=>`<button class="eqbtn big" data-qa="${k}">${t}</button>`).join('')+'</div>';
 else{const d=dir(q.e);const ok=q.a===qans(q.pot,q.l,d);
  o+=`<div class="res ${ok?'ok':'bad'}"><div class="rh">${ok?'✓ 對':'✗ 錯'}：${esc(advice(q.pot,q.l,d))}</div><div class="eqt">你勝率 ${pct(q.e)}（GTO ${q.e[2]}%）→ 池子這條線${d>0?'比 GTO 弱':'比 GTO 強'}</div></div><div class="eqb"><button class="eqbtn big" data-qn="1">下一題</button></div>`}
 o+=`<div class="eqsd">${E.score[0]}/${E.score[1]} 對・題庫 ${L.length} 題（只出明顯偏離的）</div></div>`;
 return o}
function bindQuiz(m){const q=E.q;
 m.querySelectorAll('[data-qa]').forEach(b=>b.onclick=()=>{q.a=b.dataset.qa;E.score[1]++;if(q.a===qans(q.pot,q.l,dir(q.e)))E.score[0]++;window.drawEQ()});
 m.querySelectorAll('[data-qn]').forEach(b=>b.onclick=()=>{E.q=null;window.drawEQ()})}
window.drawEQ=function(){document.body.classList.add('eqpg');const m=$('#main');
 let o=`<div class="eqw">`+btns([['look','查表'],['quiz','測驗']],E.quiz?'quiz':'look','md');
 if(E.quiz){m.innerHTML=o+quizHtml()+NOTE+'</div>';bindMd(m);bindQuiz(m);return}
 o+=`<div class="eqh">1 底池</div>`+btns(POTS,E.pot,'pot');
 if(E.pot){o+=`<div class="eqh">2 牌面</div>`+btns(TEX,E.tex,'tex')}
 if(E.pot&&E.tex){const opp=E.pot.split('|')[1];const all=lines(E.pot).filter(l=>D[`${E.pot}|${l}|${E.tex}`]);
  const cur=E.line.join(' ');
  o+=`<div class="eqh">3 他的行動線</div>`;
  // render chosen steps
  const steps=[];let si=0,ti=0;for(const t of E.line){if(t==='/'){si++;ti=0;continue}steps.push(`${STR[si]}・${actor(opp,si,ti)==='opp'?'他':'你'}${ACT[t]}`);ti++}
  if(steps.length)o+=`<div class="eqpath">${steps.map(esc).join(' → ')} <button class="eqbtn sm" data-back="1">↶ 退一步</button><button class="eqbtn sm" data-clr="1">重來</button></div>`;
  // next options
  const nx=new Set();for(const l of all){const s=l.replace(/\//g,' / ');if(cur===''){nx.add(s.split(' ')[0])}else if(s.startsWith(cur+' ')){nx.add(s.slice(cur.length+1).split(' ')[0])}}
  let si2=0,ti2=0;for(const t of E.line){if(t==='/'){si2++;ti2=0}else ti2++}
  const opts=[...nx].map(t=>{if(t==='/')return ['/',`看${STR[si2+1]}`];const a=actor(opp,si2,ti2)==='opp'?'他':'你';return [t,a+ACT[t]]}).sort((a,b)=>'xbcr/'.indexOf(a[0])-'xbcr/'.indexOf(b[0]));
  const l=E.line.join(' ').replace(/ \/ /g,'/');
  if(D[`${E.pot}|${l}|${E.tex}`])o+=card(E.pot,l,E.tex);
  else if(!steps.length)o+=`<div class="muted small">從翻牌第一個動作開始點</div>`;
  if(opts.length)o+=`<div class="small muted">${steps.length?'接著 ':''}${STR[si2]}・${opts.some(x=>x[0]!=='/'&&x[1][0]==='他')?'他':'你'}：</div>`+btns(opts,null,'tk');
 }
 o+=NOTE+'</div>';
 m.innerHTML=o;bindMd(m);
 m.querySelectorAll('[data-pot]').forEach(b=>b.onclick=()=>{E.pot=b.dataset.pot;E.line=[];window.drawEQ()});
 m.querySelectorAll('[data-tex]').forEach(b=>b.onclick=()=>{E.tex=b.dataset.tex;window.drawEQ()});
 m.querySelectorAll('[data-tk]').forEach(b=>b.onclick=()=>{E.line.push(b.dataset.tk);window.drawEQ()});
 m.querySelectorAll('[data-back]').forEach(b=>b.onclick=()=>{E.line.pop();if(E.line[E.line.length-1]==='/')E.line.pop();window.drawEQ()});
 m.querySelectorAll('[data-clr]').forEach(b=>b.onclick=()=>{E.line=[];window.drawEQ()});
 };
function bindMd(m){m.querySelectorAll('[data-md]').forEach(b=>b.onclick=()=>{E.quiz=b.dataset.md==='quiz';window.drawEQ()})}
})();
