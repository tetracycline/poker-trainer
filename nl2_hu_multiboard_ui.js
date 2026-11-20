/* 392 NL2 HU training groups: genuine 3-5-board CERT evidence, otherwise
 * prominently APPROX. A GTO citation is scoped to explicit public cards,
 * exact betting history, actor, 100bb range and corresponding SPR only.
 */
(()=>{
'use strict';
const app=document.getElementById('app');
if(!app)return;
let registry=null,pending=false;
const safe=(x)=>String(x??'');
const approxReasons={
 LOW_FREQUENCY_BELOW_PREREGISTERED_TOP24_CUTOFF:'低於依 NL2 池頻率估算的前 24／392 高頻截斷點；保留近似策略',
 NOT_ENOUGH_DISTINCT_AUTHENTIC_FLOPS_WITH_HERO_LOCKED_SOURCE:'尚無三個以上不同代表翻牌，同時符合完整行動歷史、實際 SPR、合法 combo 與英雄節點鎖來源',
 NO_TRUSTED_ACTING_SEAT_IN_PREFLOP:'翻前角色來源不足，不能驗證 OOP／IP 真實動作順序',
 INCOMPLETE_OR_EXTRA_STREET_HISTORY:'翻／轉／河的完整行動歷史不一致',
 UNPARSABLE_ACTION_SEQUENCE:'部分行動或下注尺寸仍是訓練近似，沒有精確 solver 來源',
 REPRESENTATIVE_BOARD_COVERAGE_LACKS_SECOND_TEXTURE:'代表牌面種類不足，不能假裝整類牌面都經驗證'
};
function make(tag,cls,value){
 const x=document.createElement(tag);if(cls)x.className=cls;
 if(value!==undefined)x.textContent=value;
 return x;
}
function render(){
 pending=false;
 if(!registry)return;
 const statuses=app.querySelectorAll('.hu-board-cert-status[data-hu-model]');
 for(const tag of statuses){
   const id=tag.dataset.huModel,item=registry.records[id];
   if(!item){tag.textContent='APPROX 近似（無對應來源）';continue;}
   const sec=tag.closest('.sec');
   const note=sec?.querySelector('.hu-board-proof[data-hu-model]');
   if(item.label==='CERT-MULTIBOARD'){
     const cases=item.certified_3_to_5_exact_flop_boards;
     if(cases.length<3||cases.length>5||new Set(cases.map(z=>z.flop)).size!==cases.length){
       tag.textContent='APPROX 來源驗證失敗';continue;
     }
     tag.textContent='CERT-MULTIBOARD — 限 '+cases.length+' 組具名公牌的真實 GTO';
     tag.style.background='#1b5f41';
     tag.style.color='#d6ffe4';
     tag.style.padding='4px 7px';
     tag.style.borderRadius='5px';
     if(note){
       note.replaceChildren(document.createTextNode(
         'NL2 高頻排名 #'+item.frequency_rank+'；通用六牌面／五手牌格仍為 APPROX。'
         +' 本證據只涵蓋以下實際發牌、行動線與 SPR：'));
       const ul=make('ul','hu-exact-gto-proof');
       for(const b of cases){
         const li=make('li','');
         const flavor=b.flop_texture;
         li.append(document.createTextNode(
           b.public_board+'（'+flavor+'）｜歷史 '+b.actual_exact_action_line
           +'｜SPR '+b.actual_spr+'｜可達 combo '+b.strict_full_street_combo_reachable
           +'｜GTO exploitability '+b.genuine_gto_exploitability_pct.toFixed(3)+'%｜'));
         const link=make('a','', '真實 CFR Run '+b.source_run_id);
         if(b.source_kind.includes('OFFICIAL')){
           link.href='nl2-cfr.html?spot='+encodeURIComponent(item.solver_profile)
              +'&version=gto&sha='+encodeURIComponent(b.source_sha256)
              +'&board='+encodeURIComponent(b.public_board)
              +'&line='+encodeURIComponent(b.actual_exact_action_line);
         }else{
           link.href='https://github.com/tetracycline/poker-trainer/actions/runs/'+b.source_run_id;
           link.target='_blank';link.rel='noopener';
         }
         li.appendChild(link);
         li.append(document.createTextNode(
          '｜NL2 英雄鎖頻 '+b.nl2_locked_variants.length+' 版'
          +(b.nl2_locked_variants.some(x=>x.unknown_history_frequency_filled_with_default)
             ? '（缺的精細頻率以公開標示預設補齊）':'（可觀測粗分桶頻率，未必覆蓋全節點）')
          +'｜50% pot '+(b.b50_nonpolarized_relative_equity_research_candidate
             ? '有非極化研究候選':'無足夠證據，不標為推薦')));
         ul.appendChild(li);
       }
       note.append(ul);
       const disclosure=make('strong','hu-multiboard-limits',
         '注意：CERT 僅限以上真實公牌。下方一般牌面分類的行動仍顯示 APPROX，不得認為整格已是 GTO。');
       note.append(disclosure);
     }
   }else{
     tag.textContent='APPROX 近似解';
     tag.style.background='#664814';tag.style.color='#ffe0a2';
     tag.style.padding='4px 7px';tag.style.borderRadius='5px';
     if(note)note.textContent='NL2 頻率排名 #'+item.frequency_rank+
       '（前24視為優先研究）；'+(approxReasons[item.blocked_reason]||'需要先取得完整公牌／範圍／SPR 的原始解算')+
       '。此表的下注與牌型行動屬估計值，不能視為 GTO。';
   }
 }
}
function schedule(){if(!pending){pending=true;queueMicrotask(render)}}
new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
fetch('data/nl2_hu_multiboard_status.json',{cache:'no-store'})
 .then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()})
 .then(d=>{
   if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V1'||d.TOTAL!==392||
      d.CERT_MULTIBOARD+d.APPROX!==392||Object.keys(d.records).length!==392){
        throw Error('Certification source register failed independent count check');
   }
   registry=d;
   schedule();
 }).catch(e=>{
   console.warn('Independent model certification ledger unavailable. All unverified rows remain APPROX.',e);
 });
schedule();
})();