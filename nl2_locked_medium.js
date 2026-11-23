// Source identities include the model, decision, acting seat, original run and original subgame digest.
(() => {
  const sources=[
    ['data/nl2_hu_b483_locked_medium.json','NL2_HU_B483_ORIGINAL_LOCKED_MEDIUM_V1'],
    ['data/nl2_hu_b485_locked_medium.json','NL2_HU_B485_ORIGINAL_LOCKED_MEDIUM_V1']
  ];
  const indexes=new WeakMap(), handDigests=new WeakMap();
  let loading;
  function load(){
    loading ??= Promise.all(sources.map(async ([path,schema])=>{
      const response=await fetch(path,{cache:'no-store'});
      if(!response.ok)throw Error('HTTP '+response.status);
      const report=await response.json();
      if(report.schema!==schema||!report.references)throw Error('雙方可達性來源格式不符');
      return report;
    })).then(reports=>{
      const result={references:{},gto_references:{}};
      for(const report of reports){
        Object.assign(result.references,report.references);
        Object.assign(result.gto_references,report.gto_references);
      }
      return result;
    }).catch(error=>{loading=undefined;throw error;});
    return loading;
  }
  function sourceKey(run,sha,version,spot){
    return JSON.stringify([run,sha,version,spot]);
  }
  const nodeKey=(board,line,seat)=>JSON.stringify([board,line,seat]);
  function sourceIndex(report){
    if(indexes.has(report))return indexes.get(report);
    const result=new Map();
    function add(row){
      if(!row)return;
      const source=sourceKey(row.source_run_id,row.source_sha256,row.version,row.spot);
      if(!result.has(source))result.set(source,new Map());
      const index=result.get(source), key=nodeKey(row.public_board,row.line,row.acting_seat);
      const before=index.get(key);
      if(before&&(before.source_hand_order_sha256!==row.source_hand_order_sha256||
         before.compatible_action_mask_b64!==row.compatible_action_mask_b64||
         before.compatible_hole_card_pairs!==row.compatible_hole_card_pairs||
         JSON.stringify(before.b50)!==JSON.stringify(row.b50)))throw Error('同一來源有相衝的手牌證據');
      index.set(key,row);
    }
    for(const row of Object.values(report.references)){add(row);add(row.gto);}
    for(const row of Object.values(report.gto_references||{}))add(row);
    indexes.set(report,result);return result;
  }
  function lookup(report,model,board,source){
    if(!source)return null;
    const run=source.source_run_id??source.run_id,sha=source.source_sha256??source.sha256;
    const prefix=[model.model_id,board.public_board,board.actual_exact_action_line,board.acting_seat];
    const key=(r,h)=>JSON.stringify([...prefix,r,h]);
    let row;
    if(source.version==='gto'){
      if(run!==board.source_run_id||sha!==board.source_sha256)return null;
      row=report.gto_references?.[key(run,sha)];
      if(!row){
        const lock=board.nl2_locked_variants.find(v=>report.references[key(v.run_id,v.sha256)]?.gto?.source_sha256===sha);
        if(lock)row=report.references[key(lock.run_id,lock.sha256)].gto;
      }
    }else if(board.nl2_locked_variants.some(v=>v.run_id===run&&v.sha256===sha&&v.version===source.version)){
      row=report.references[key(run,sha)];
    }
    if(!row)return null;
    if(row.spot!==model.solver_profile||row.family!==model.family||row.flop!==board.flop||row.turn!==board.turn||
       row.public_board!==board.public_board||row.line!==board.actual_exact_action_line||row.acting_seat!==board.acting_seat||
       row.version!==source.version||row.source_run_id!==run||row.source_sha256!==sha||
       !['POSITIVE_JOINT_REACH','ZERO_JOINT_REACH'].includes(row.status))throw Error('原始 run、SHA、牌面或座位不符');
    return row;
  }
  async function bindCase(report,actual,run=actual.source_run_id){
    const index=sourceIndex(report).get(sourceKey(run,actual.source_sha256,actual.version,actual.spot));
    const verified=new Map();
    if(!index)return verified;
    await Promise.all(actual.nodes.map(async node=>{
      const key=nodeKey(node.public_board??node.board,node.exact_node_line??node.line,node.acting_seat);
      const row=index.get(key);
      if(row){
        const mask=await bindMask(row,actual,node);
        verified.set(node,{row,mask});
      }
    }));
    return verified;
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
    const actions=node.source_actions??node.actions;
    if(!row || row.public_board!==(node.public_board??node.board) || row.line!==(node.exact_node_line??node.line) || row.acting_seat!==node.acting_seat)
      throw Error('無此決策的雙方可達手牌來源');
    const hands=actual.hands_by_seat?.[node.acting_seat];
    if(row.source_sha256!==actual.source_sha256||row.version!==actual.version||row.spot!==actual.spot||
       row.family!==actual.pot_family||row.flop!==actual.flop||row.turn!==actual.turn||
       (actual.source_run_id!=null&&row.source_run_id!==actual.source_run_id)||!Array.isArray(hands)||typeof row.compatible_action_mask_b64!=='string'||
       JSON.stringify(row.source_actions)!==JSON.stringify(actions))
      throw Error('缺少可核對的手牌或動作順序');
    if(!handDigests.has(hands))handDigests.set(hands,crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(hands)))
      .then(bytes=>Array.from(new Uint8Array(bytes),v=>v.toString(16).padStart(2,'0')).join('')));
    const hex=await handDigests.get(hands);
    if(hex!==row.source_hand_order_sha256)throw Error('原始牌序 SHA 不符');
    const mask=atob(row.compatible_action_mask_b64);
    const limit=2**actions.length;
    if(mask.length!==hands.length||Array.from(mask,c=>c.charCodeAt(0)).some(b=>b>=limit)||
       Array.from(mask).filter(c=>c.charCodeAt(0)>0).length!==row.strict_legal_combos)
      throw Error('雙方可達手牌遮罩不符');
    const original=node.eligible_action_masks_b64??node.strictly_reachable_masks_b64;
    if(typeof original==='string'){
      const earlier=atob(original);
      if(earlier.length!==mask.length||Array.from(mask).some((c,i)=>c.charCodeAt(0)&~earlier.charCodeAt(i)))
        throw Error('相容手牌的動作與原始節點不符');
    }
    return mask;
  }
  globalThis.nl2LockedMedium={load,lookup,describe,showBoard,bindMask,bindCase};
})();
