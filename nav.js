/* 全站主選單（5 區＋首頁）與共用大字設定。每頁 <body> 開頭： <script src="(相對路徑)nav.js" data-sec="pre"></script> */
(function(){
var s=document.currentScript,base=s.src.replace(/nav\.js(\?.*)?$/,''),sec=s.getAttribute('data-sec')||'';
if(window.self!==window.top)return; // 被嵌入時不顯示
var S=[['home','⌂ 首頁','index.html#home'],['pre','翻前','index.html#prac'],['post','翻後','postflop/index.html#prac'],['exp','剝削','learn.html#tb'],['eq','對手範圍','learn.html#eq'],['rv','覆盤','review/index.html']];
var css=document.createElement('style');css.id='gnav-css';
css.textContent=
'.gnav{display:flex;gap:8px;padding:10px 10px 8px;padding-top:calc(10px + env(safe-area-inset-top));background:#0b140f;border-bottom:1px solid #2c4637}'+
'.gnav a{flex:1 1 0;text-align:center;white-space:nowrap;padding:11px 8px;border-radius:12px;font:700 21px/1.2 -apple-system,BlinkMacSystemFont,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;color:#e8f1ea!important;background:#16261d;border:1px solid #2c4637;text-decoration:none}'+
'.gnav a.on{background:#3ecf7a;border-color:#3ecf7a;color:#06281a!important}'+
'html.has-gnav nav.top{padding-top:8px!important;background:#0f1a14}'+
'html.has-gnav nav.top .topb{font-size:18px}'+
'html.sec-home nav.top,html.sec-home .foot{display:none!important}'+
'@media (max-width:600px){html{zoom:1.1}.gc b{font-size:clamp(8px,2.6vw,15px)!important}.gnav{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;padding:8px 6px 6px}.gnav a{font-size:19px;padding:10px 4px}}'+
'@media (min-width:1024px){html{zoom:.9!important}main,.wrap{max-width:1180px!important;margin-left:auto!important;margin-right:auto!important}main{padding:0 14px}.gnav{gap:6px;padding:6px 10px 5px}.gnav a{font-size:17px;padding:6px 8px;border-radius:9px}html.has-gnav nav.top{padding-top:4px!important;padding-bottom:4px!important}html.has-gnav nav.top .topb{font-size:16px;padding:4px 10px}.pg:has(>#qbox),#drill:has(>#qbox),.pg:has(>.qcard){display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:14px;align-items:start}.pg:has(>#qbox)>*,.pg:has(>.qcard)>*{grid-column:1/-1}.pg>#qbox,#drill>#qbox{grid-column:1}.pg>#ans,#drill>#ans{grid-column:2}#qbox>.qcard,#qbox.sec,#ans>.sec:first-child{margin-top:0}.pg:has(>#qbox)>.dpick:not([open]){grid-column:1}.pg:has(>#qbox)>.dpick:not([open])+.row.ctl{grid-column:2;justify-self:end}main>.qcard:has(>.res),#qc:has(>.qR){display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:14px;align-items:start}main>.qcard:has(>.res)>*{grid-column:1}main>.qcard>.res{grid-column:2;grid-row:1/span 40;margin-top:0}#qc>.qR>.res:first-child{margin-top:0}#qbox .cd,.qcard .cd{width:50px;height:68px;font-size:25px}#qbox .cd i,.qcard .cd i{font-size:20px}.pg>:has(+.qcard){grid-column:1}.pg>.qcard{grid-column:2}.pg>.qcard,.pg>:has(+.qcard){margin-top:8px}.flt{flex-wrap:nowrap!important;overflow-x:auto;scrollbar-width:thin;padding-bottom:3px}.flt>*{flex:none}}';
document.head.appendChild(css);
var n=document.createElement('nav');n.className='gnav';n.id='gnav';n.setAttribute('aria-label','主選單');
n.innerHTML=S.map(function(x){return '<a href="'+base+x[2]+'" data-s="'+x[0]+'">'+x[1]+'</a>'}).join('');
document.body.insertBefore(n,document.body.firstChild);
document.documentElement.classList.add('has-gnav');
function set(v){sec=v;var c=document.documentElement.classList;S.forEach(function(x){c.remove('sec-'+x[0])});c.add('sec-'+v);
 Array.prototype.forEach.call(n.querySelectorAll('a'),function(a){a.classList.toggle('on',a.getAttribute('data-s')===v)})}
set(sec);
window.PKNAV={set:set,base:base};
var ks=document.createElement('script');ks.src=base+'keys.js?v=5';document.head.appendChild(ks);
})();
