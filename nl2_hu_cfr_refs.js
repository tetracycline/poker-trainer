/* Strictly source-linked examples for generic HU model tables.
 * This script NEVER calls a MODEL row CERT; exact game-tree equivalence
 * requires the public runout, exact sizes, SPR and combo reach.
 */
(()=>{
'use strict';
const root=document.getElementById('app');
if(!root||typeof fetch!=='function')return;
let evidence=null,queued=false;
const statusStrings={
 MATCHED_ABSTRACT_HISTORY_AND_1PCT_SPR_ONLY:'相同抽象下注歷史＋節點 SPR 接近，但 MODEL 未指定精確公牌，不能升為 CERT／EST',
 MATCHED_ABSTRACT_HISTORY_BUT_NOT_SPR:'有同抽象行動線的真實 CFR，但 SPR 不符合此 MODEL，禁止套用',
 NO_MATCHING_EXACT_BOARD_SOURCE_LINE:'現有真實 CFR 沒有這條完整行動線，仍待解算'
};
function decorate(){
 queued=false;
 if(!evidence)return;
 for(const tag of root.querySelectorAll('.hu-cfr-lineage[data-hu-model]:not([data-checked])')){
   tag.dataset.checked='1';
   const id=tag.dataset.huModel;
   const item=evidence.records?.[id];
   if(!item){tag.textContent='無可驗證原始來源，不得標 CERT';continue;}
   const summary=statusStrings[item.candidate_status]||'來源不明';
   tag.textContent=summary+'。 ';
   if(item.candidate_status==='MATCHED_ABSTRACT_HISTORY_AND_1PCT_SPR_ONLY'&&item.best_exact_board_examples?.length){
     const c=item.best_exact_board_examples[0];
     const url='nl2-cfr.html?spot='+encodeURIComponent(c.spot)+'&version=gto&sha='+encodeURIComponent(c.source_sha256);
     const a=document.createElement('a');a.href=url;
     a.textContent='查看同線、SPR 接近的精確公牌 '+c.actual_public_board+'（Run '+c.source_run_id+'）';
     tag.appendChild(a);
     const note=document.createTextNode('；此範例的 GTO 僅適用該公牌與真實逐 combo 範圍。');
     tag.appendChild(note);
   }
 }
}
function schedule(){if(!queued){queued=true;queueMicrotask(decorate)}}
const observe=new MutationObserver(schedule);
observe.observe(root,{childList:true,subtree:true});
fetch('data/nl2_hu_model_history_crosswalk.json',{cache:'no-store'})
  .then(r=>{if(!r.ok)throw Error('crosswalk HTTP '+r.status);return r.json()})
  .then(data=>{
    if(data.schema!=='NL2_MODEL_TO_CFR_LINEAGE_SCREEN_V1'||data.model_nodes!==392||
       data.generic_CERT!==0||data.generic_EST!==0)throw Error('Crosswalk verification failed');
    evidence=data;schedule();
  }).catch(err=>{console.warn('NL2 MODEL provenance crosswalk unavailable',err)});
schedule();
})();