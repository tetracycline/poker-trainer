/* 全站快捷鍵（同一套規則）。由 nav.js 載入。
   1–9 這頁的主要選項（答案按鈕；首頁大按鈕；對手範圍的下一步）＋ 助記字母 F 棄牌、C 跟注/過牌、R 加注/下注、A 全下
   空白/Enter 下一題・Backspace/Esc 退一步（上一題）・← → 換分頁・⇧1–6 主選單
   V 版本（穩健剝削/GTO）・M 模式・G GTO 對照・D 練習項目選單・其他字母＝換這一排的選項（⇧＋字母 反向）或按那個按鈕
   H 或 ? 顯示全部快捷鍵 */
(function(){
if(window.self!==window.top||window.PKKEYS)return;
var POOL='QWETYUIOPSJKLZXBN'.split('');
var CTRL='button,a[href],summary,select,input:not([type=hidden]),textarea,[role=button]';
var SKIP='#kkhint,#kkhelp,.kk';
function vis(e){if(!e.isConnected||e.disabled)return false;if(e.closest(SKIP))return false;var r=e.getBoundingClientRect();if(!r.width||!r.height)return false;var dd=e.parentElement&&e.parentElement.closest('details:not([open])');if(dd&&!(e.tagName==='SUMMARY'&&e.parentElement===dd))return false;var cs=getComputedStyle(e);return cs.visibility!=='hidden'&&cs.display!=='none'}
function isOn(e){return e.classList.contains('on')||e.classList.contains('sel')||e.getAttribute('aria-pressed')==='true'||e.getAttribute('aria-selected')==='true'}
function txt(e){var t='';e.childNodes.forEach(function(n){if(!(n.nodeType===1&&n.tagName==='KBD'))t+=n.textContent});return t.replace(/\s+/g,' ').trim()}
function sig(e){return e.tagName+'.'+((e.className&&typeof e.className==='string'?e.className:'').split(' ').filter(function(c){return c&&c!=='on'&&c!=='kkh'&&!/^k-/.test(c)})[0]||'')+'['+Object.keys(e.dataset).filter(function(k){return k!=='kk'}).sort().join(',')+']'}
function isNext(e){return e.matches('.nx,[data-next],[data-qn],[data-a=next],[data-nav="1"]')||/^下一(題|手)/.test(txt(e))}
function isBack(e){return e.matches('[data-back],[data-nav="-1"]')||/^(← 上一題|↶)/.test(txt(e))}
function isAns(e){return e.matches('.ab,[data-qa],.hb,[data-tk],.abar button')&&!isNext(e)}
function mnem(e){var t=txt(e);if(/棄/.test(t))return 'F';if(/全下/.test(t))return 'A';if(/^(跟|過牌)/.test(t))return 'C';if(/(加注|下注|3-bet|4-bet|5-bet|Iso|隔離)/i.test(t))return 'R';return null}
function fixedOf(e){if(e.matches('[data-ver],[data-v]'))return 'V';if(e.matches('[data-md],[data-m],[data-rm],[data-tab]'))return 'M';if(e.id==='gt')return 'G';if(e.tagName==='SUMMARY'&&e.closest('.dpick'))return 'D';return null}
// -------- assignment (deterministic from DOM) --------
function assign(){
 var all=Array.prototype.filter.call(document.querySelectorAll(CTRL),vis);
 var K={},list=[],used={},rows=[],singles=[],ans=[],tabs=[],curTab=null;
 function put(k,act,els,badgeEl,label){if(K[k])return false;K[k]={act:act,els:els};used[k]=1;list.push({k:k,els:els,badge:badgeEl,label:label});return true}
 var gn=all.filter(function(e){return e.closest('#gnav')});
 gn.forEach(function(e,i){put('S'+(i+1),cl(e),[e],e,'⇧'+(i+1))});
 var rest=all.filter(function(e){return !e.closest('#gnav')});
 // sub-nav tabs
 rest.forEach(function(e){if(e.closest('nav.top')&&e.classList.contains('topb')&&e.id!=='gt')tabs.push(e)});
 if(tabs.length>1){var cur=tabs.findIndex(isOn),tn=tabs[(cur+1)%tabs.length],tp=tabs[(cur-1+tabs.length)%tabs.length];
  put('ArrowRight',cl(tn),tabs,tn,tn===tp?'← →':'→');put('ArrowLeft',cl(tp),tabs,tn===tp?null:tp,'←');if(cur>=0)curTab=tabs[cur]}
 if(tabs.length<2)tabs=[];rest=rest.filter(function(e){return tabs.indexOf(e)<0});
 // next / back
 var nx=rest.filter(isNext),bk=rest.filter(isBack);
 if(nx[0]){put('Space',cl(nx[0]),[nx[0]],nx[0],'空白');K.Enter=K.Space}
 if(bk[0]){put('Backspace',cl(bk[0]),[bk[0]],bk[0],'⌫')}
 rest=rest.filter(function(e){return e!==nx[0]&&e!==bk[0]});
 // answers 1–9 (+ mnemonic)
 ans=rest.filter(isAns).slice(0,9);
 ans.forEach(function(e,i){var m=e.matches('.hb,[data-tk]')?null:mnem(e),lab=String(i+1);if(m&&!K[m])lab+=' '+m;put(String(i+1),cl(e),[e],e,lab);if(lab.length>1)put(m,cl(e),[e],null,null)});
 rest=rest.filter(function(e){return ans.indexOf(e)<0});
 // groups
 var onSig={};rest.forEach(function(e){if(isOn(e))onSig[sig(e)]=1});
 var groups=[],gmap=new Map();
 rest.forEach(function(e){var key=sig(e),p=e.parentElement,g=null;
  if(e.tagName!=='SELECT'&&e.tagName!=='INPUT'&&e.tagName!=='TEXTAREA'){var arr=gmap.get(p)||{};gmap.set(p,arr);g=arr[key];if(!g){g=arr[key]={sig:key,els:[]};groups.push(g)}g.els.push(e)}
  else groups.push({sig:key,els:[e],solo:1})});
 if(curTab)singles.push(curTab);
 groups.forEach(function(g){var row=!g.solo&&g.els.length>=2&&(onSig[g.sig]||g.els[0].tagName==='BUTTON');
  if(row)rows.push(g);else g.els.forEach(function(e){singles.push(e)})});
 // fixed letters first
 rows.slice().forEach(function(g){var f=fixedOf(g.els[0]);if(f&&!K[f]){putRow(f,g);rows.splice(rows.indexOf(g),1)}});
 singles.slice().forEach(function(e){var f=fixedOf(e);if(f&&!K[f]){put(f,cl(e),[e],e,f);singles.splice(singles.indexOf(e),1)}});
 var pi=0;function nextL(){while(pi<POOL.length&&K[POOL[pi]])pi++;return pi<POOL.length?POOL[pi++]:null}
 function putRow(L,g){var els=g.els,mk=rowKey(g);function step(d){return function(){var c=els.findIndex(isOn);if(c<0&&MEM[mk]!=null&&MEM[mk]<els.length)c=MEM[mk];var j=c<0?(d>0?0:els.length-1):(c+d+els.length)%els.length;MEM[mk]=j;cl(els[j])()}}
  put(L,step(1),els,els[0],L);put('S'+L,step(-1),els,null);K[L].row=mk}
 rows.forEach(function(g){var L=nextL();if(L)putRow(L,g)});
 var over=[];singles.forEach(function(e){var L=nextL();if(L)put(L,act(e),[e],e,L);else over.push(e)});
 POOL.forEach(function(L){if(!over.length)return;if(!K['S'+L]){var e=over.shift();put('S'+L,act(e),[e],e,'⇧'+L)}});
 return {K:K,list:list,tabs:tabs.length>1,ans:ans.length,next:!!nx[0],back:!!bk[0]};
}
var MEM={};function rowKey(g){return location.pathname+location.hash+'|'+g.sig+'|'+g.els.length}
function cl(e){return function(){e.click()}}
function act(e){return /^(SELECT|INPUT|TEXTAREA)$/.test(e.tagName)?function(){e.focus()}:cl(e)}
// -------- badges --------
var CSS='.kk{display:inline-block;min-width:1.25em;padding:0 .3em;margin:0 .35em 0 0;border:1px solid #6b8f7b;border-radius:5px;background:#0b130e;color:#dcefe3;font:700 14px/1.45 ui-monospace,Menlo,Consolas,monospace;vertical-align:.12em;text-align:center;white-space:nowrap;letter-spacing:0;text-shadow:none;pointer-events:none}'+
 '.kk.sib{margin:0 .3em 0 0;align-self:center}.kkh kbd:not(.kk){display:none!important}'+
 '#kkhint{font-size:15px;color:#9fb6a9;padding:4px 12px;border-bottom:1px solid #22382b;background:#0f1a14}#kkhint b{color:#dcefe3}'+
 '#kkhelp{position:fixed;inset:0;z-index:999;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center}#kkhelp>div{background:#16261d;border:1px solid #3ecf7a;border-radius:16px;padding:18px 22px;max-width:640px;font-size:19px;line-height:1.7;color:#e8f1ea}#kkhelp h3{margin:0 0 6px;color:#3ecf7a}'+
 '@media (hover:none) and (pointer:coarse),(max-width:700px){.kk,#kkhint{display:none!important}.kkh kbd:not(.kk){display:inline-block!important}}';
var st=document.createElement('style');st.textContent=CSS;document.head.appendChild(st);
var mo,pending=false,LAST=null;
function render(){pending=false;if(mo)mo.disconnect();
 document.querySelectorAll('.kk').forEach(function(b){b.remove()});document.querySelectorAll('.kkh').forEach(function(e){e.classList.remove('kkh')});
 var A=assign();LAST=A;
 A.list.forEach(function(x){var e=x.badge;if(!e||!x.label)return;var k=document.createElement('kbd');k.className='kk';k.textContent=x.label;
  if(/^(SELECT|INPUT|TEXTAREA)$/.test(e.tagName)||(x.els.length>1&&e.parentElement&&/grid/.test(getComputedStyle(e.parentElement).display))){k.classList.add('sib');var host=x.els.length>1&&/grid/.test(getComputedStyle(e.parentElement).display)?e.parentElement:e;host.parentElement.insertBefore(k,host)}
  else if(x.els.length>1&&x.k.indexOf('Arrow')<0){k.classList.add('sib');e.parentElement.insertBefore(k,e)}
  else{e.classList.add('kkh');e.insertBefore(k,e.firstChild)}});
 hint(A);
 if(mo)mo.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class','open','style','disabled','hidden']});
}
function hint(A){var h=document.getElementById('kkhint');if(!h){h=document.createElement('div');h.id='kkhint'}
 var anchor=Array.prototype.filter.call(document.querySelectorAll('nav.top'),function(n){return getComputedStyle(n).display!=='none'})[0]||document.getElementById('gnav');
 if(anchor&&h.previousElementSibling!==anchor)anchor.parentElement.insertBefore(h,anchor.nextSibling);
 var p=['⌨'];if(A.ans)p.push('<b>1–'+A.ans+'</b> 選');if(A.next)p.push('<b>空白</b> 下一題');if(A.back)p.push('<b>⌫</b> 退一步');if(A.tabs)p.push('<b>← →</b> 分頁');p.push('<b>字母</b> 換選項（⇧ 反向）');p.push('<b>⇧1–6</b> 主選單');p.push('<b>H</b> 全部');
 var s=p.join('・');if(h.innerHTML!==s)h.innerHTML=s}
function schedule(){if(pending)return;pending=true;requestAnimationFrame(render)}
function help(show){var o=document.getElementById('kkhelp');if(o){o.remove();return}if(show===false)return;o=document.createElement('div');o.id='kkhelp';
 o.innerHTML='<div><h3>快捷鍵（全站一樣）</h3><b>1–9</b> 答案（畫面順序）・<b>F</b> 棄牌・<b>C</b> 跟注/過牌・<b>R</b> 加注/下注・<b>A</b> 全下<br><b>空白 / Enter</b> 下一題・<b>⌫ / Esc</b> 退一步、上一題<br><b>← →</b> 上/下一個分頁・<b>⇧1–6</b> 主選單<br><b>V</b> 穩健剝削/GTO・<b>M</b> 模式・<b>G</b> GTO 對照・<b>D</b> 練習項目<br>其他字母：換那一排的選項（<b>⇧</b>＋字母 反向），或按那個按鈕<br>輸入框裡打字時不會觸發；<b>Esc</b> 離開輸入框<br><span style="color:#8fa69a">按 H、? 或 Esc 關閉</span></div>';
 o.onclick=function(){o.remove()};document.body.appendChild(o)}
function keyId(e){var c=e.code||'';if(/^Digit[1-9]$/.test(c))return (e.shiftKey?'S':'')+c.slice(5);if(/^Numpad[1-9]$/.test(c)&&!e.shiftKey)return c.slice(6);if(/^Key[A-Z]$/.test(c))return (e.shiftKey?'S':'')+c.slice(3);
 if(c==='Space'||e.key===' ')return 'Space';if(e.key==='Enter')return 'Enter';if(e.key==='Backspace')return 'Backspace';if(e.key==='Escape')return 'Escape';if(e.key==='ArrowLeft')return 'ArrowLeft';if(e.key==='ArrowRight')return 'ArrowRight';if(e.key==='?'||(c==='Slash'&&e.shiftKey))return '?';return null}
addEventListener('keydown',function(e){
 if(e.ctrlKey||e.metaKey||e.altKey||e.isComposing)return;
 var t=e.target,typing=t&&(/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)||t.isContentEditable);
 var id=keyId(e);if(!id)return;
 if(typing){if(id==='Escape'){t.blur();e.preventDefault();e.stopImmediatePropagation()}return}
 if(document.getElementById('kkhelp')){if(id==='Escape'||id==='H'||id==='?'){help(false);e.preventDefault();e.stopImmediatePropagation()}return}
 if(id==='H'||id==='?'){help(true);e.preventDefault();e.stopImmediatePropagation();return}
 var A=assign(),k=id==='Escape'?'Backspace':id,x=A.K[k];
 if(!x)return;
 e.preventDefault();e.stopImmediatePropagation();
 if(document.activeElement&&document.activeElement!==document.body&&document.activeElement.blur)document.activeElement.blur();
 x.act();
},true);
// remember which item of an un-highlighted row was clicked, so the row letter continues from there
addEventListener('click',function(e){if(!e.isTrusted||!LAST)return;var t=e.target;for(var k in LAST.K){var x=LAST.K[k];if(!x.row)continue;for(var i=0;i<x.els.length;i++)if(x.els[i]===t||x.els[i].contains(t)){MEM[x.row]=i;return}}},true);
// Space on a mouse-focused button must not re-click it
addEventListener('keyup',function(e){if((e.code==='Space'||e.key===' ')&&e.target&&/^(BUTTON|A|SUMMARY)$/.test(e.target.tagName))e.preventDefault()},true);
function start(){mo=new MutationObserver(function(ms){for(var i=0;i<ms.length;i++){var n=ms[i].target;if(n.id==='kkhint'||(n.closest&&n.closest('#kkhint,#kkhelp')))continue;return schedule()}});render();addEventListener('resize',schedule);addEventListener('hashchange',schedule)}
window.PKKEYS={assign:assign,render:render,last:function(){return LAST}};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
