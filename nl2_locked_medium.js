// Source identities include the model, decision, acting seat, original run and original subgame digest.
(() => {
  const path='data/nl2_hu_b483_locked_medium.json';
  let loading;
  function load(){
    loading ??= fetch(path,{cache:'no-store'}).then(async response=>{
      if(!response.ok) throw Error('HTTP '+response.status);
      const report=await response.json();
      if(report.schema!=='NL2_HU_B483_ORIGINAL_LOCKED_MEDIUM_V1'||!report.references)
        throw Error('雙方可達性來源格式不符');
      return report;
    }).catch(error=>{loading=undefined;throw error;});
    return loading;
  }
  function lookup(report, model, board, source){
    if(!source) return null;
    const gto=source.version==='gto';
    const run=source.source_run_id??source.run_id, sha=source.source_sha256??source.sha256;
    const variants=gto?board.nl2_locked_variants:board.nl2_locked_variants.filter(v=>
      v.run_id===run&&v.sha256===sha&&v.version===source.version);
    for(const v of variants){
      const key=JSON.stringify([model.model_id,board.public_board,board.actual_exact_action_line,board.acting_seat,v.run_id,v.sha256]);
      const ref=report.references[key], row=gto?ref?.gto:ref;
      if(!row)continue;
      if(ref.spot!==model.solver_profile || ref.family!==model.family || ref.flop!==board.flop || ref.turn!==board.turn ||
         ref.public_board!==board.public_board || ref.line!==board.actual_exact_action_line || ref.acting_seat!==board.acting_seat ||
         ref.version!==v.version || ref.source_run_id!==v.run_id || ref.source_sha256!==v.sha256 ||
         row.source_run_id!==run || row.source_sha256!==sha || row.version!==source.version ||
         !['POSITIVE_JOINT_REACH','ZERO_JOINT_REACH'].includes(row.status))
        throw Error('原始 run、SHA、牌面或座位不符');
      return row;
    }
    return null;
  }
  function describe(row){
    if(!row) return '50% pot 的雙方可達組合尚未核對。';
    if(row.status==='ZERO_JOINT_REACH')return '雙方可達配牌為 0；這條行動線沒有可評估的 50% 下注。';
    const b=row.b50, counts='雙方可達 '+row.strict_legal_combos+' 組英雄手牌、'+row.compatible_hole_card_pairs+' 組雙方配牌。';
    if(!b)return counts+'50% pot 尚無可核對的行動證據。';
    if(b.status==='NO_50PCT_ACTION')return counts+'此節點的解算選單沒有 50% 下注。';
    if(!b.eligible)return counts+'有 50% 下注選項，可走此行動的手牌為 0 組。';
    return counts+'可下 50% pot 的手牌有 '+b.eligible+' 組，其中 '+b.preferred+' 組以 50% 下注的 EV 最高。'+
      '中段 equity '+b.middle_count+' 組。'+(b.candidate?'符合非極化下注研究候選條件。':'未達非極化下注研究門檻。');
  }
  function showBoard(parent,model,board){
    const mount=document.createElement('div');parent.appendChild(mount);
    load().then(report=>{
      const gto=lookup(report,model,board,{version:'gto',source_run_id:board.source_run_id,source_sha256:board.source_sha256});
      if(gto){
        const line=document.createElement('div');line.textContent='GTO｜'+describe(gto);mount.appendChild(line);
      }
      for(const [i,v] of board.nl2_locked_variants.entries()){
        const row=lookup(report,model,board,v), line=document.createElement('div');
        if(row){
          const link=document.createElement('a');
          const query=new URLSearchParams({model:model.model_id,board:board.public_board,version:v.version+'@'+i,sha:v.sha256});
          link.href='nl2-multiboard.html?'+query;link.textContent='NL2 鎖 '+v.run_id;
          line.appendChild(link);line.appendChild(document.createTextNode('｜'+describe(row)));
        }else line.textContent='NL2 鎖 '+v.run_id+'｜'+describe(null);
        mount.appendChild(line);
      }
    }).catch(()=>{mount.textContent='雙方可達性與 50% 下注稽核暫時無法載入。';});
  }
  async function bindMask(row,actual,node){
    if(!row || row.public_board!==node.public_board || row.line!==node.exact_node_line || row.acting_seat!==node.acting_seat)
      throw Error('無此決策的雙方可達手牌來源');
    const hands=actual.hands_by_seat?.[node.acting_seat];
    if(row.source_sha256!==actual.source_sha256||row.version!==actual.version||row.spot!==actual.spot||
       row.family!==actual.pot_family||!Array.isArray(hands)||typeof row.compatible_action_mask_b64!=='string'||
       JSON.stringify(row.source_actions)!==JSON.stringify(node.source_actions))
      throw Error('缺少可核對的手牌或動作順序');
    const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(hands)));
    const hex=Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,'0')).join('');
    if(hex!==row.source_hand_order_sha256)throw Error('原始牌序 SHA 不符');
    const mask=atob(row.compatible_action_mask_b64);
    const limit=2**node.source_actions.length;
    if(mask.length!==hands.length||Array.from(mask,c=>c.charCodeAt(0)).some(b=>b>=limit)||
       Array.from(mask).filter(c=>c.charCodeAt(0)>0).length!==row.strict_legal_combos)
      throw Error('雙方可達手牌遮罩不符');
    return mask;
  }
  globalThis.nl2LockedMedium={load,lookup,describe,showBoard,bindMask};
})();
