// 同一題（含同一步）只發一次 __Q；作答後重畫不算新題
let QN=0;function setQ(q,o){if(q&&!q.__n)q.__n=++QN;const k=(q&&q.__n)+'|'+JSON.stringify(o);if(window.__Q&&window.__Qk===k)return;window.__Qk=k;window.__Q=o}
(function(){
const D=window.LD,$=s=>document.querySelector(s),R='AKQJT98765432';
const st={tab:(location.hash.slice(1)||'tb'),gto:false,tb:'CO>BTN',iso:'UTG>BTN',two:false,grp:'SRP_IP',cat:'all',mode:'drill',tx:'A_high',q:null};
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const pick=a=>a[Math.floor(Math.random()*a.length)];
const SUIT={s:'♠',h:'♥',d:'♦',c:'♣'};
function card(c,sm){return `<span class="cd ${c[1]}${sm?' sm':''}">${c[0]==='T'?'10':c[0]}<i>${SUIT[c[1]]}</i></span>`}
function cards(s,sm){let o='';for(let i=0;i<s.length;i+=2)o+=card(s.substr(i,2),sm);return o}
function combo(h){const S='shdc';let a,b;if(h.length===2){const x=Math.floor(Math.random()*4);let y=(x+1+Math.floor(Math.random()*3))%4;return h[0]+S[x]+h[1]+S[y]}
 if(h[2]==='s'){const x=S[Math.floor(Math.random()*4)];return h[0]+x+h[1]+x}a=Math.floor(Math.random()*4);b=(a+1+Math.floor(Math.random()*3))%4;return h[0]+S[a]+h[1]+S[b]}
// compress hand list: QQ+, JJ-66, AJs+, A9s-A6s
function comp(list){const set=new Set(list),out=[];let run=[];
 const flush=(top)=>{if(!run.length)return;const a=run[0],b=run[run.length-1];out.push(run.length===1?a:(a===top?b+'+':a+'-'+b));run=[]};
 for(const r of R){const h=r+r;if(set.has(h))run.push(h);else flush('AA')}flush('AA');
 for(const t of 'so')for(let i=0;i<13;i++){const hi=R[i];run=[];const top=hi+R[i+1]+t;
  for(let j=i+1;j<13;j++){const h=hi+R[j]+t;if(set.has(h))run.push(h);else flush(top)}flush(top)}
 return out.join(' ')||'—'}
function nav(){const T=st.tab==='eq'?[]:[['tb','3-bet'],['iso','Iso 跛入'],['ln','行動線'],['rd','讀牌']];
 $('#topnav').innerHTML=T.map(([k,l])=>`<button class="topb${st.tab===k?' on':''}" data-t="${k}">${l}</button>`).join('')+`<button class="topb${st.gto?' on':''}" id="gt" style="flex:0 0 auto">GTO 對照</button>`;
 $('#topnav').querySelectorAll('[data-t]').forEach(b=>b.onclick=()=>{st.tab=b.dataset.t;st.q=null;location.hash=st.tab;draw()});
 $('#gt').onclick=()=>{st.gto=!st.gto;draw()}}
const chips=(arr,cur,attr)=>arr.map(([k,l])=>`<button class="chip${k===cur?' on':''}" data-${attr}="${k}">${l}</button>`).join(' ');
function bind(attr,fn){document.querySelectorAll(`[data-${attr}]`).forEach(b=>b.onclick=()=>{fn(b.dataset[attr]);st.q=null;draw()})}
const AB=(k,l,c)=>`<button class="ab ${c}" data-a="${k}">${l}</button>`;
/* ---------- 3-bet ---------- */
function tbWhyHand(t,h,a){const v=t.val.includes(h),s=t.semi.includes(h);
 if(a==='3bet'){return v?`對他跟注範圍勝率 ${t.eqc[h]}% → 3-bet 讓差牌付錢`:`他面對 3-bet 棄 ${t.pf3}%，被跟也有補牌 → 小對子 3-bet 偷`}
 if(a==='call')return t.h==='BB'?'BB 已經放了 1bb，賠率好 → 跟注看翻牌':'3-bet 時他只用更好的牌繼續 → 平跟、有位置打翻後';
 return '跟了翻後常被壓制、很難贏 → 棄'}
function vs4Why(t,h,a){if(a==='jam')return `NL2 的 4-bet 幾乎都是 QQ+/AK，你仍領先（勝率 ${t.eq4[h]}%）→ 全下`;
 if(a==='call')return `勝率約 ${t.eq4[h]}%，夠跟、但全下會被 AA/KK 吃 → 跟`;
 return `NL2 4-bet 只有 ${t.p4}%，AA/KK 占 29% → 你勝率只有 ${t.eq4[h]}%，棄`}
function tbAns(t,h){return t.val.includes(h)||t.semi.includes(h)?'3bet':t.call.includes(h)?'call':'fold'}
function drawTB(){const t=D.tb[st.tb],O=['UTG','HJ','CO','BTN','SB'];const heroes=Object.keys(D.tb).filter(k=>k.startsWith(t.o+'>')).map(k=>[k,k.split('>')[1]]);
 let h=`<div class="pg"><div class="dg"><span class="dgl">誰開池</span>${chips(O.map(o=>[o,o]),t.o,'op')}</div><div class="dg"><span class="dgl">你在</span>${chips(heroes,st.tb,'sp')}</div>`;
 const v4=Object.entries(t.vs4);const jam=v4.filter(x=>x[1]==='jam').map(x=>x[0]),cal=v4.filter(x=>x[1]==='call').map(x=>x[0]);
 h+=`<div class="sec"><div class="big">${t.o} 開 ${t.open}bb → 你 ${t.h} 3-bet 到 ${t.to}bb（${t.ip?'有位置 3 倍':'沒位置 4 倍'}）</div>
 <div class="ln"><span class="lab">3-bet 價值</span><b>${comp(t.val)}</b></div>
 ${t.semi.length?`<div class="ln"><span class="lab">3-bet 偷</span><b>${comp(t.semi)}</b></div>`:''}
 <div class="ln"><span class="lab">被 4-bet</span>${comp(jam)} 全下${cal.length?'・'+comp(cal)+' 跟':''}・其他棄</div>
 <div class="why">${t.o} 被 3-bet 棄 ${t.pf3}%、4-bet 只 ${t.p4}% → ${t.gv==='small'?'差很小，範圍照 GTO':'3-bet 收價值，不用純詐唬'}</div>${t.sc?`<div class="rsc">${esc(t.sc)}</div>`:''}${t.gl?`<div class="gl">${esc(t.gl)}</div>`:''}
 <details><summary>跟注範圍（${t.pct.call}%）</summary><div class="small">${comp(t.call)}</div></details>`;
 if(st.gto){const g=Object.entries(t.gto).filter(([k,s])=>s[2]>=50).map(x=>x[0]);h+=`<div class="gto">GTO 3-bet（≥50% 頻率）：${comp(g)}</div>`}
 h+=`</div>`+tbDrill(t)+`</div>`;$('#main').innerHTML=h;
 bind('op',o=>{st.tb=Object.keys(D.tb).find(k=>k.startsWith(o+'>')&&k.endsWith('>BB'))||Object.keys(D.tb).find(k=>k.startsWith(o+'>'))});bind('sp',k=>st.tb=k);bindDrill()}
function tbDrill(t){if(!st.q||st.q.k!=='tb'){const pool=[...t.val,...t.semi,...t.call,...t.call,...D.tb[st.tb].call.map(x=>x)];
  const near=Object.keys(t.gto).filter(k=>!pool.includes(k)&&/^(A|K|Q|J|T)|s$|^(\d)\1$/.test(k));
  const all=[...t.val,...t.val,...t.semi,...t.semi,...t.call,...near.slice(0,40)];const hh=pick(all);st.q={k:'tb',h:hh,c:combo(hh),step:1,pick:null}}
 const q=st.q,h=q.h;setQ(st.q,{drill:'tb',id:st.tb,hero:q.c,board:'',role:['pre',''],step:q.step,sc:t.sc,gl:t.gl,gv:t.gv});let o=`<div class="qcard"><div class="qs">練習：${t.o} 開 ${t.open}bb，你在 ${t.h}，拿到</div><div class="cards">${cards(q.c)}</div>`;
 if(q.step===1){o+=`<div class="acts">${AB('fold','棄牌','k-fold')}${AB('call','跟注','k-call')}${AB('3bet','3-bet','k-3bet')}</div>`}
 else{const a=tbAns(t,h),ok=q.pick===a;o+=res(ok,`${h}：${{fold:'棄牌',call:'跟注','3bet':'3-bet 到 '+t.to+'bb'}[a]}`,tbWhyHand(t,h,a),st.gto&&t.gto[h]?`GTO：棄 ${t.gto[h][0]}%・跟 ${t.gto[h][1]}%・3-bet ${t.gto[h][2]}%`:'');
  if(a==='3bet'){if(q.step===2)o+=`<div class="qs" style="margin-top:10px">${t.o} 4-bet 回來！</div><div class="acts">${AB('fold','棄牌','k-fold')}${AB('call','跟注','k-call')}${AB('jam','全下','k-jam')}</div>`;
   else{const b=t.vs4[h]||'fold',both=(h==='AA'||h==='KK')&&q.p2!=='fold';o+=res(q.p2===b||both,`面對 4-bet：${{fold:'棄牌',call:'跟注',jam:'全下'}[b]}`,vs4Why(t,h,b),'')}}
  if(a!=='3bet'||q.step===3)o+=`<div class="acts"><button class="ab nx" data-a="next">下一手</button></div>`}
 return o+`</div>`}
function res(ok,head,why,gto){return `<div class="sec res ${ok?'ok':'bad'}"><div class="rh">${ok?'✓ ':'✗ '}${esc(head)}</div><div class="why">${esc(why)}</div>${gto?`<div class="gto">${esc(gto)}</div>`:''}</div>`}
function bindDrill(){document.querySelectorAll('[data-a]').forEach(b=>b.onclick=()=>{const a=b.dataset.a,q=st.q;if(a==='next'){st.q=null;draw();return}
 if(q.k==='tb'){if(q.step===1){q.pick=a;q.step=2;if(tbAns(D.tb[st.tb],q.h)!=='3bet')q.step=2}else if(q.step===2){q.p2=a;q.step=3}}
 else if(q.k==='iso'||q.k==='ln'||q.k==='rd'){if(q.pick)return;q.pick=a}
 draw()})}
/* ---------- iso ---------- */
function isoKey(){return st.iso+(st.two?'_2limp':'')}
function drawISO(){const L=['UTG','HJ','CO','BTN','SB'];let key=isoKey();if(!D.iso[key]){st.two=false;key=st.iso}const t=D.iso[key];
 const heroes=Object.keys(D.iso).filter(k=>!k.endsWith('_2limp')&&k.startsWith(t.l+'>')).map(k=>[k,k.split('>')[1]]);
 const oth={fold:'其他全部棄（有位置也不要跟著跛入）',limp:`其他：約 ${t.limp_pct}% 的牌補 0.5bb，剩下棄`,check:'其他全部過牌（免費看翻牌）'}[t.other];
 let h=`<div class="pg"><div class="dg"><span class="dgl">誰跛入</span>${chips(L.map(o=>[o,o]),t.l,'il')}</div><div class="dg"><span class="dgl">你在</span>${chips(heroes,st.iso,'ih')}</div>
 <div class="dg"><span class="dgl">跛入人數</span>${chips([['1','1 人'],['2','2 人']],st.two?'2':'1','in')}</div>
 <div class="sec"><div class="big">${t.two?'2 人':t.l}跛入 → 你 ${t.h} 加注到 ${t.size}bb</div>
 <div class="ln"><span class="lab">加注（${t.pct}%）</span><b>${comp(t.core)}</b></div><div class="ln small">${oth}</div>
 <div class="why">跛入者被加注還跟 ${t.lc}%、只再加注 ${t.lr}% → 用好牌加注，翻後打他的弱範圍</div>${t.sc?`<div class="rsc">${esc(t.sc)}</div>`:''}${t.gl?`<div class="gl">${esc(t.gl)}</div>`:''}
 ${t.other==='limp'?`<details><summary>補 0.5bb 的牌</summary><div class="small">${comp(t.limp)}</div></details>`:''}${t.adv.length?`<details><summary>進階也賺（EV 小於 1bb）</summary><div class="small">${comp(t.adv)}</div></details>`:''}
 ${st.gto?'<div class="gto">GTO 對照：解算器沒有跛入節點（GTO 不跛入），這裡只有剝削版</div>':''}</div>`;
 h+=isoDrill(t,key);
 h+=`<details class="sec"><summary class="big">加注後怎麼打（${D.iso_post.length} 條）</summary>${D.iso_post.map(r=>`<div class="rrow"><div>${esc(r.sit)}</div><div class="a">→ ${esc(r.ans)}</div><div class="w">${esc(r.why)}</div>${r.sc?`<div class="rsc">${esc(r.sc)}</div>`:''}</div>`).join('')}</details></div>`;
 $('#main').innerHTML=h;bind('il',l=>{st.iso=Object.keys(D.iso).find(k=>k.startsWith(l+'>')&&k.endsWith('>BTN'))||Object.keys(D.iso).find(k=>k.startsWith(l+'>'))});bind('ih',k=>st.iso=k);bind('in',n=>st.two=n==='2');bindDrill()}
function isoDrill(t,key){if(!st.q||st.q.k!=='iso'||st.q.key!==key){const near=['K9o','QTo','JTo','Q9s','J9s','T8s','97s','86s','A9o','A8o','K8s','55','44','33','22','K5s','Q8s','A5o','KTo'];
  const hh=pick([...t.core,...t.adv,...near.filter(x=>!t.core.includes(x))]);st.q={k:'iso',key,h:hh,c:combo(hh),pick:null}}
 setQ(st.q,{drill:'iso',id:key,hero:st.q.c,board:'',role:['pre',''],sc:t.sc,gl:t.gl,gv:t.gv});const q=st.q,h=q.h,oth=t.other,olab={fold:'棄牌',limp:'補 0.5bb',check:'過牌'}[oth];
 let o=`<div class="qcard"><div class="qs">練習：${t.two?'2 人':t.l}跛入，你在 ${t.h}，拿到</div><div class="cards">${cards(q.c)}</div>`;
 if(!q.pick)o+=`<div class="acts">${AB(oth,olab,'k-fold')}${AB('iso','加注 '+t.size+'bb','k-3bet')}</div>`;
 else{const a=t.core.includes(h)?'iso':(oth==='limp'&&!t.limp.includes(h)?'fold':oth),adv=t.adv.includes(h);const ok=q.pick===a||(adv&&q.pick==='iso');
  const lab=a==='iso'?'加注 '+t.size+'bb':{fold:'棄牌',limp:'補 0.5bb',check:'過牌'}[a];
  const why=a==='iso'?`比跛入範圍強很多，翻後好打 → 加注拿主動`:adv?'有一點 EV，但新手翻後難打 → 先不加注（加也行）':a==='limp'?'只要再補 0.5bb，賠率好 → 補':a==='check'?'免費看翻牌，不用花錢 → 過牌':'牌太弱，有位置也不要跟著跛 → 棄';
  o+=res(ok,`${h}：${lab}`,why,'')+`<div class="acts"><button class="ab nx" data-a="next">下一手</button></div>`}
 return o+`</div>`}
/* ---------- lines ---------- */
const G=[['SRP_IP','你開池（有位置）'],['SRP_BB','你 BB 防守'],['3BP_3bettor','你 3-bet（沒位置）'],['3BP_caller','你跟 3-bet（有位置）']];
const CAT={f_cbet:'翻牌 c-bet',barrel:'轉牌再開火',delay:'翻牌過→轉牌',r_barrel:'河牌第三槍',r_stab:'河牌（轉牌過）',vs_probe:'對手轉牌先下',vs_raise:'被加注',r_vs_bet:'河牌被下注',f_vs_cbet:'翻牌被 c-bet',vs_barrel:'轉牌被下注',probe:'轉牌你先下'};
const STZ={flop:'翻牌',turn:'轉牌',river:'河牌'};
function alab(a,s){if(a==='x')return '過牌';if(a==='f')return '棄牌';if(a==='c')return '跟注';if(a==='r')return '加注';
 if(s==='flop')return a==='small'?'下注 33%':'下注 75%';return a==='small'?'下注 半池':'下注 1 池+'}
function spotTxt(g,sp){const [a,b]=sp.split('_');if(g==='SRP_IP')return `你 ${a} 開池、BB 跟`;if(g==='SRP_BB')return `${a} 開池、你 BB 跟`;
 const x=a.replace('3','');if(g==='3BP_3bettor')return `BTN 開、你 ${x} 3-bet、BTN 跟`;return `你 BTN 開、${x} 3-bet、你跟`}
function drawLN(){const rs=D.rules.filter(r=>r.group===st.grp);const cats=[...new Set(rs.map(r=>r.cat))];if(st.cat!=='all'&&!cats.includes(st.cat))st.cat='all';
 if(st.mode==='sheet'&&st.cat==='all')st.cat=cats[0];
 let h=`<div class="pg"><div class="dg">${chips(G,st.grp,'g')}</div>
 <div class="row ctl"><span class="seg"><button class="segb${st.mode==='drill'?' on':''}" data-m="drill">練習</button><button class="segb${st.mode==='sheet'?' on':''}" data-m="sheet">速查</button></span></div>
 ${st.mode==='sheet'?`<div class="dg">${chips(cats.map(c=>[c,CAT[c]||c]),st.cat,'c')}</div>`:''}`;
 h+=st.mode==='drill'?lnDrill(rs):lnSheet(rs);$('#main').innerHTML=h+`</div>`;
 bind('g',g=>{st.grp=g;st.cat='all'});bind('c',c=>st.cat=c);bind('m',m=>{st.mode=m;st.cat='all'});bind('x',x=>st.tx=x);bindDrill()}
const SPM={BTN_BB:['BB','BTN',1,'SRP',5.5,97.5],CO_BB:['BB','CO',1,'SRP',5.5,97.5],HJ_BB:['BB','HJ',1,'SRP',5.5,97.5],UTG_BB:['BB','UTG',1,'SRP',5.5,97.5],SB_BB:['SB','BB',0,'SRP',6,97],SB3_BTN:['SB','BTN',0,'3BP',21,90],BB3_BTN:['BB','BTN',0,'3BP',20.5,90]};
const f1=x=>(Math.round(x*10)/10).toString();
function spRole(sp,p){const [oop,ip,pfr,kind]=SPM[sp],me=p?ip:oop,op=p?oop:ip;if(kind==='SRP')return pfr===p?['open',me]:['call',op+'open>'+me];return pfr===p?['tb',op+'open>'+me]:['c3',me+'open>'+op+'3b']}
// 完整行動線：翻前（尺寸）＋每條街（尺寸）；回傳 [rows, 底池, 你剩]
function lnRows(sp,l,p,b){const [oop,ip,pfr,kind,P0,stk]=SPM[sp],nm=[oop,ip].map((x,i)=>i===p?'你':x),pn=[oop,ip];
 const o=kind==='SRP'?(pfr?ip:oop):(pfr?oop:ip),c=kind==='SRP'?(pfr?oop:ip):(pfr?ip:oop),me=x=>x===pn[p]?'你':x;
 const pf=kind==='SRP'?`${me(o)} 開 ${o==='SB'?3:2.5}bb → ${me(c)} 跟`:`${me(o)} 開 2.5bb → ${me(c)} 3-bet 到 ${100-stk}bb → ${me(o)} 跟`;
 const rows=[['翻前',pf]];let pot=P0*100,ct=0;const S=l.split('/').map(x=>x?x.split(' '):[]),nst=b.length/2-3;
 for(let si=0;si<=nst;si++){const tk=S[si]||[],bt=[0,0],d=[];tk.forEach((t,k)=>{const q=k%2,mx=Math.max(bt[0],bt[1]);
  if(t==='x')d.push(nm[q]+' 過牌');else if(t==='c'){bt[q]=mx;d.push(nm[q]+' 跟')}else if(t==='f')d.push(nm[q]+' 棄');
  else if(t[0]==='b'){const pc=+t.slice(1);bt[q]=Math.round(pc/100*pot);d.push(`${nm[q]} 下注 ${pc}%（${f1(bt[q]/100)}bb）`)}
  else if(t==='r'){bt[q]=3*mx;d.push(`${nm[q]} 加注到 ${f1(bt[q]/100)}bb`)}else if(t==='a'){bt[q]=stk*100-ct;d.push(`${nm[q]} 全下`)}});
  const cs=si===0?b.slice(0,6):b.slice(4+2*si,6+2*si);
  if(si<nst){pot+=bt[0]+bt[1];ct+=bt[p];rows.push([['翻牌','轉牌','河牌'][si],d.join(' → ')||'—',cs])}
  else{rows.push([['翻牌','轉牌','河牌'][si],(d.length?d.join(' → ')+' → ':'')+'輪到你',cs]);ct+=0;var cur=pot+bt[0]+bt[1],left=stk*100-ct-bt[p]}}
 return [rows,cur/100,left/100]}
function actHTML(rows){return `<div class="ral">${rows.map(r=>`<div><b>${r[0]}</b>${r[2]?`<span class="rc">${cards(r[2],1)}</span>`:''}${esc(r[1])}</div>`).join('')}</div>`}
function lnDrill(rs){if(!st.q||st.q.k!=='ln'||st.q.g!==st.grp||(st.cat!=='all'&&st.q.r.cat!==st.cat)){let pool=rs.filter(r=>(st.cat==='all'||r.cat===st.cat)&&r.ex.length);
  const r=pick(pool),e=pick(r.ex);st.q={k:'ln',g:st.grp,r,e,pick:null}}
 const {r,e}=st.q,b=e[1],[rows,pot,left]=lnRows(e[2],e[4]||'',e[5],b);
 setQ(st.q,{drill:'ln',id:r.id,hero:e[0],board:b,role:spRole(e[2],e[5]),line:e[4],spot:e[2],rows:rows.map(x=>x[0]),sc:r.sc,gl:r.gl||'',psc:r.psc||'',dev:r.dev,gv:r.gv});
 let o=`<div class="qcard"><div class="rsc">統計範圍：${esc(r.sc)}</div>${actHTML(rows)}<div class="small muted">底池 <b>${f1(pot)}bb</b>・你剩 ${f1(left)}bb</div>
 <div class="cards" style="margin-top:6px"><span class="lb">你</span>${cards(e[0])}</div>`;
 if(!st.q.pick)o+=`<div class="acts">${r.choices.map(a=>AB(a,alab(a,r.street),a==='x'||a==='f'?'k-fold':a==='c'?'k-call':a==='small'?'k-open':'k-3bet')).join('')}</div>`;
 else{const ok=st.q.pick===r.ans,alt=!ok&&r.ok.includes(st.q.pick);
  o+=`<div class="sec res ${ok?'ok':alt?'mix':'bad'}"><div class="rh">${ok?'✓ ':alt?'△ ':'✗ '}${alab(r.ans,r.street)}${r.dev?'<span class="dev">剝削</span>':'<span class="dev g">GTO</span>'}</div>
  <div class="small muted">你的牌：${esc(r.hc_zh)}${r.tx_zh?'・'+esc(r.tx_zh):''}${alt?'・你的選擇也可以，但不是首選':''}</div>
  <div class="why">${esc(r.why)}</div>${r.gl?`${r.psc?`<div class="rsc">${esc(r.psc)}</div>`:''}<div class="gl">${esc(r.gl)}</div>`:''}${r.dev?`<div class="gto">GTO 是：${alab(r.gto,r.street)}</div>`:''}${st.gto?`<div class="gto">GTO 頻率：${Object.entries(r.gf).map(([k,v])=>alab(k,r.street)+' '+Math.round(v*100)+'%').join('・')}</div>`:''}</div>
  <div class="acts"><button class="ab nx" data-a="next">下一題</button></div>`}
 return o+`</div>`}
function lnSheet(rs){const cat=st.cat==='all'?rs[0].cat:st.cat;let sub=rs.filter(r=>r.cat===cat);const txs=[...new Set(sub.map(r=>r.tx).filter(Boolean))];
 let h='';if(txs.length){if(!txs.includes(st.tx))st.tx=txs[0];h+=`<div class="dg"><span class="dgl">牌面</span>${chips(txs.map(x=>[x,sub.find(r=>r.tx===x).tx_zh]),st.tx,'x')}</div>`;sub=sub.filter(r=>r.tx===st.tx)}
 const keyf=r=>r.street+(r.tx||'');const parts={};sub.forEach(r=>(parts[keyf(r)]=parts[keyf(r)]||[]).push(r));
 for(const k in parts){const p=parts[k];h+=`<div class="sec"><div class="big">${esc(p[0].sit)}${p.length&&!p[0].tx?'（'+STZ[p[0].street]+'）':''}</div>`+p.map(r=>`<div class="rrow"><div>${esc(r.hc_zh)} <span class="a">→ ${alab(r.ans,r.street)}</span>${r.dev?'<span class="dev">剝削</span>':''}</div><div class="w">${esc(r.why)}</div>${r.gl?`${r.psc?`<div class="rsc">${esc(r.psc)}</div>`:''}<div class="gl">${esc(r.gl)}</div>`:''}${st.gto?`<div class="gto">GTO：${alab(r.gto,r.street)}</div>`:''}</div>`).join('')+`</div>`}
 return h}
/* ---------- 讀牌 ---------- */
const BZ={S:'兩對以上',M:'頂對/超對',W:'弱對',D:'聽牌',A:'空氣',G:'之後棄牌'},STN={1:'翻牌',2:'轉牌',3:'河牌'};
const RC={S:'#e05a5a',M:'#e8a23a',W:'#d9cf6b',D:'#5aa9ff',A:'#8a968f',G:'#33463b'};
function rbar(p){const ks='SMWDAG'.split('').filter(k=>p[k]>0);return `<div class="rb">${ks.map(k=>`<span class="${k}" style="flex:${p[k]} 0 0">${p[k]>=8?p[k]+'%':''}</span>`).join('')}</div><div class="lg">${ks.map(k=>`<span><i style="background:${RC[k]}"></i>${BZ[k]} ${p[k]}%</span>`).join('')}</div>`}
function rlg(){return `<div class="lg">${'SMWDAG'.split('').map(k=>`<span><i class="rb-${k}" style="background:${{S:'#e05a5a',M:'#e8a23a',W:'#d9cf6b',D:'#5aa9ff',A:'#8a968f',G:'#33463b'}[k]}"></i>${BZ[k]}</span>`).join('')}</div>`}
function bcards(b){return cards(b.slice(0,6),1)+(b.length>6?'<span style="width:6px"></span>'+cards(b.slice(6),1):'')}
function rdNorm(a){return a.startsWith('下注')?'bet':a==='過牌'?'x':a==='棄牌'?'f':a==='跟注'?'c':a==='加注'?'r':'cf'}
function drawRD(){st.rg=st.rg||'all';st.rm=st.rm||'drill';const G=[['all','全部'],...Object.entries(D.readGrp)];
 let h=`<div class="sec"><div class="dg">${chips(G,st.rg,'rg')}</div><div class="dg">${chips([['drill','練習'],['sheet','總表']],st.rm,'rm')}</div></div>`;
 const rs=D.reads.filter(r=>st.rg==='all'||r.grp===st.rg);
 h+=st.rm==='drill'?rdDrill(rs):rdSheet(rs);$('#main').innerHTML=h;
 bind('rg',g=>st.rg=g);bind('rm',m=>st.rm=m);bindDrill()}
function rdHead(r,p){return `<div class="small muted">${STN[r.street]}・讀牌</div><div class="qs">${esc(r.line)}</div>${r.sc?`<div class="rsc">統計範圍：${esc(r.sc)}</div>`:''}
 <div class="cards"><span class="lb">牌面</span>${bcards(r.board)}${r.tx?`<span class="txz">${esc(r.tx.zh)}</span>`:''}</div>`}
function rdN(r){const t=r.tx;return `<div class="nn">樣本：全部牌面 ${r.n.toLocaleString()} 手・攤牌 ${r.nsd.toLocaleString()}${t&&t.on?`｜${esc(t.zh)} ${t.n.toLocaleString()} 手・攤牌 ${t.nsd.toLocaleString()}`:''}${r.small?'<span class="few">・樣本偏少</span>':''}</div>`}
function rdHIP(r,p){if(!p)return null;const O=['SB','BB','UTG','HJ','CO','BTN'],a=p.split('>'),x=t=>O.indexOf(t.replace('open','').replace('3b',''));
 if(r.grp==='ip')return true;if(r.grp==='bb')return false;if(a.length<2)return null;
 if(r.id.indexOf('3b_')===0)return x(a[1])>x(a[0]);if(r.grp==='3b')return x(a[0])>x(a[1]);return x(a[1])>x(a[0])}
function rdLine(r,p){const L=r.lines||[];if(!L.length)return -1;const ip=rdHIP(r,p);let c=L.map((l,i)=>i).filter(i=>ip==null||L[i].ip===ip);if(!c.length)c=L.map((l,i)=>i);
 let t=0;c.forEach(i=>t+=L[i].w);let x=Math.random()*t;for(const i of c){x-=L[i].w;if(x<=0)return i}return c[c.length-1]}
function rdAct(r,p,li){const l=(r.lines||[])[li];if(!l)return '';const pf=(p&&D.rdSpot?D.rdSpot(r,p):r.spot)+'（翻前尺寸不分）';
 return `<div class="ral"><div><b>翻前</b>${esc(pf)}</div>${l.st.map(x=>{const k=x.indexOf('：');return `<div><b>${esc(x.slice(0,k))}</b>${esc(x.slice(k+1))}</div>`}).join('')}</div>`}
function rdLS(r,li){const L=r.lines||[],l=L[li];if(!l||L.length<2)return '';
 return `<div class="nn">本題這條線（占 ${l.sh}%）：${l.nsd>=60?`攤牌 ${l.nsd}・兩對+ ${l.bar.S}%・空氣 ${l.bar.A}%`:`攤牌僅 ${l.nsd} 手 → 用 ${L.length} 條線合併`}</div>`}
function rdRange(r){const t=r.tx;if(!t)return `<div class="small muted">他的範圍：</div>${rbar(r.bar)}`;
 return `<div class="small muted">他的範圍：${t.on?`<b class="txz" style="margin:0">${esc(t.zh)}</b>（本題牌面）`:`<b>全部牌面合併</b>（${esc(t.zh)}攤牌僅 ${t.nsd} 手，不足 60）`}</div>${rbar(t.on?t.bar:r.bar)}`}
function rdGL(r){const t=r.tx;let o='';if(t&&t.on&&t.gl)o+=`<div class="gl">${esc(t.zh)}：${esc(t.gl)}</div>`;
 if(r.gp)o+=`<div class="gl">全部牌面：${esc(r.gp)}</div>`;else if(r.gl)o+=`<div class="gl">${esc(r.gl)}</div>`;
 if(r.ct&&r.ct.length)o+=`<div class="nn">${r.ct.map(esc).join('；')}</div>`;return o}
function rdRole(r,p){if(r.grp==='ip')return ['open',p];if(r.grp==='bb')return ['call',p];if(r.grp==='iso')return ['iso',p];if(r.id.indexOf('3b_')===0)return ['tb',p.replace(/3b$/,'')];return ['c3',p]}
// 只發 HW 會玩的牌：每個組合依它的位置檢查核心範圍
function rdDealHW(r){const ok=c=>!window.HWR||HWR.ok(...rdRole(r,D.rdPos[c[1]]),hcls(c[0]));const H=r.hands.map(h=>({h,cs:h.cs.filter(ok)})).filter(x=>x.cs.length);
 if(!H.length)return null;let t=0;const ws=H.map(x=>{const w=Math.max(x.h.sh,0.12);t+=w;return w});let z=Math.random()*t,k=H.length-1;for(let i=0;i<H.length;i++){z-=ws[i];if(z<=0){k=i;break}}
 const cs=H[k].cs;let s2=0;cs.forEach(c=>s2+=c[2]);z=Math.random()*s2;let c=cs[cs.length-1];for(const x of cs){z-=x[2];if(z<=0){c=x;break}}return {hd:H[k].h,c:c[0],pos:D.rdPos[c[1]]}}
function hcls(c){const a=c.slice(0,2),b=c.slice(2,4);let x=R.indexOf(a[0]),y=R.indexOf(b[0]);if(x>y)[x,y]=[y,x];return x===y?R[x]+R[x]:R[x]+R[y]+(a[1]===b[1]?'s':'o')}
function rdDrill(rs){if(!st.q||st.q.k!=='rd'||!rs.includes(st.q.r)){let r,dl;for(let k=0;k<30;k++){r=pick(rs);dl=rdDealHW(r);if(dl)break}st.q={k:'rd',r,hd:dl.hd,c:dl.c,pos:dl.pos,pick:null}}
 if(st.q.li==null)st.q.li=rdLine(st.q.r,st.q.pos);
 {const q=st.q,l=(q.r.lines||[])[q.li];setQ(st.q,{drill:'rd',id:q.r.id,hero:q.c||q.hd.c,board:q.r.board,role:rdRole(q.r,q.pos),pos:q.pos,rows:['翻前',...(l?l.st.map(x=>x.slice(0,x.indexOf('：'))):[])],street:q.r.street,sc:q.r.sc,line:l&&l.st,act:q.hd.act,gv:q.hd.gv})}
 const {r,hd}=st.q;let o=`<div class="qcard">${rdHead(r,st.q.pos)}${rdAct(r,st.q.pos,st.q.li)}<div class="cards" style="margin-top:6px"><span class="lb">你</span>${cards(st.q.c||hd.c)}</div>
 <div class="qs" style="margin-top:8px">他拿什麼？你怎麼做？</div>`;
 const ch=r.kind==='dec'?[['x','過牌','k-fold'],['bet','下注','k-3bet']]:[['f','棄牌','k-fold'],['c','跟注','k-call'],['r','加注','k-3bet']];
 if(!st.q.pick)o+=`<div class="acts">${ch.map(([a,l,c])=>AB(a,l,c)).join('')}</div>`;
 else{const ans=rdNorm(hd.act),p=st.q.pick,ok=p===ans||ans==='cf';
  o+=`<div class="sec res ${ok?'ok':'bad'}"><div class="rh">${ok?'✓ ':'✗ '}你：${esc(hd.zh)} → ${esc(hd.act==='邊緣'?(r.kind==='dec'?'下注或過牌都行（邊緣）':'跟或棄都行（邊緣）'):hd.act)}</div>
  ${rdRange(r)}
  <div class="why">${esc(r.why)}</div>${rdGL(r)}${rdLS(r,st.q.li)}${hd.gn?`<div class="gl">${esc(hd.gn)}</div>`:''}${hd.tn?`<div class="gl">${esc(hd.tn)}</div>`:''}
  <div class="nn eqx">你這類手 vs 他這條線範圍（${esc(hd.eqr||'全部牌面')}）：勝率 ${hd.eq}%${r.need?`・跟注要 ${r.need}%`:''}${r.fold!=null?`・你下注他棄 ${r.tx&&r.tx.on&&r.tx.fold!=null?r.tx.fold:r.fold}%`:''}</div>${rdN(r)}</div>
  <div class="acts"><button class="ab nx" data-a="next">下一題</button></div>`}
 return o+`</div>`}
function rdSheet(rs){return rs.map(r=>`<div class="sec"><div class="small muted">${esc(r.spot)}・${STN[r.street]}</div><div class="big">${esc(r.line)}</div>${r.sc?`<div class="rsc">統計範圍：${esc(r.sc)}</div>`:''}<div class="small muted">全部牌面合併：</div>${rbar(r.bar)}<div class="why">${esc(r.why0||r.why)}</div>${r.gp?`<div class="gl">${esc(r.gp)}</div>`:r.gl?`<div class="gl">${esc(r.gl)}</div>`:''}
 ${r.txs&&r.txs.length?`<div class="txt"><div class="small muted">分牌面（攤牌 ≥60）：</div>${r.txs.map(t=>`<div class="txr"><span>${esc(t.zh)}<i>攤 ${t.nsd}</i></span>${mbar(t.bar)}</div>`).join('')}${r.txlow&&r.txlow.length?`<div class="nn">不足 60，看合併：${r.txlow.map(esc).join('、')}</div>`:''}</div>`:''}${rdN0(r)}</div>`).join('')}
function rdN0(r){return `<div class="nn">樣本：全部牌面 ${r.n.toLocaleString()} 手・攤牌 ${r.nsd.toLocaleString()}</div>`}
function mbar(p){return `<div class="rb mb">${'SMWDAG'.split('').filter(k=>p[k]>0).map(k=>`<span class="${k}" style="flex:${p[k]} 0 0" title="${BZ[k]} ${p[k]}%">${p[k]>=10?p[k]:''}</span>`).join('')}</div>`}
function draw(){nav();if(window.PKNAV)PKNAV.set(st.tab==='eq'?'eq':'exp');$('#topnav').style.display=st.tab==='eq'?'none':'';document.body.classList.toggle('eqpg',st.tab==='eq');if(st.tab==='eq'&&window.drawEQ)window.drawEQ();else if(st.tab==='tb')drawTB();else if(st.tab==='iso')drawISO();else if(st.tab==='rd')drawRD();else drawLN()}
addEventListener('hashchange',()=>{const t=location.hash.slice(1);if(t&&t!==st.tab&&['tb','iso','ln','rd','eq'].includes(t)){st.tab=t;st.q=null;draw();scrollTo(0,0)}});
draw();window.LQ={st:st,draw:draw};
})();
