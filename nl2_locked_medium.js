// Source identities include the model, decision, acting seat, original run and original subgame digest.
(() => {
  const indexes=new WeakMap(), handDigests=new WeakMap();
  const unresolved='UNRESOLVED_JOINT_REACH';
  let loading;
  async function request(path){
    const response=await fetch(path,{cache:'no-store'});
    if(!response.ok)throw Error('HTTP '+response.status);
    return response;
  }
  async function readReports(){
    const manifest=await (await request('data/nl2_hu_verified_extensions.json')).json();
    const files=manifest.locked_medium_reports;
    if(manifest.schema!=='NL2_EXACT_VERIFIED_EXTENSIONS_V1' || !Array.isArray(files) ||
       !files.some(f=>f.path==='data/nl2_hu_b483_locked_medium.json') ||
       new Set(files.map(f=>f.path)).size!==files.length)throw Error('缺少原始雙方可達性來源目錄');
    const paths=files.map(({path,schema,sha256})=>{
      const match=/^data\/nl2_hu_b([1-9][0-9]*)_locked_medium\.json$/.exec(path);
      if(!match||!/^[a-f0-9]{64}$/.test(sha256)||schema!=='NL2_HU_B'+match[1]+'_ORIGINAL_LOCKED_MEDIUM_V1')throw Error('原始來源路徑或版本不符');
      return {path,schema,sha256};
    });
    const reports=await Promise.all(paths.map(async ({path,schema,sha256})=>{
      const bytes=await (await request(path)).arrayBuffer();
      const hash=await crypto.subtle.digest('SHA-256',bytes);
      const actual=Array.from(new Uint8Array(hash),c=>c.toString(16).padStart(2,'0')).join('');
      if(actual!==sha256)throw Error('原始雙方可達性報告 SHA 不符');
      const report=JSON.parse(new TextDecoder().decode(bytes));
      if(report.schema!==schema)throw Error('雙方可達性來源格式不符');
      return report;
    }));
    return combine(reports);
  }
  function load(){
    loading ??= readReports().catch(error=>{loading=undefined;throw error;});
    return loading;
  }
  const sourceKey=(run,sha,version,spot)=>JSON.stringify([run,sha,version,spot]);
  const nodeKey=(board,line,seat)=>JSON.stringify([board,line,seat]);
  const scopeFields=['root_applied_rust_lock_nodes','subgame_applied_rust_lock_nodes'];
  function same(a,b){
    if(a===b)return true;
    if(!a||!b||typeof a!=='object'||typeof b!=='object'||Array.isArray(a)!==Array.isArray(b))return false;
    return Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>Object.hasOwn(b,k)&&same(a[k],b[k]));
  }
  // Different model keys can point to exactly the same original node and private-hand order.
  function combine(reports){
    const index=new Map(), result={references:Object.create(null),gto_references:Object.create(null)};
    const links=new Map(), pending=new Map();
    function register(key,row,gto){
      const [model]=JSON.parse(key), seat=row.acting_seat;
      const canonical=JSON.stringify([model,row.public_board,row.line,seat,row.source_run_id,row.source_sha256]);
      if(typeof model!=='string'||!model||canonical!==key||![0,1].includes(seat)||
         !Number.isSafeInteger(row.source_run_id)||row.source_run_id<=0||!/^[a-f0-9]{64}$/.test(row.source_sha256)||
         row.version!==(gto?'gto':(seat?'exp_ip':'exp_oop'))||
         !Number.isSafeInteger(row.strict_legal_combos)||row.strict_legal_combos<0||
         !Number.isSafeInteger(row.compatible_hole_card_pairs)||row.compatible_hole_card_pairs<row.strict_legal_combos||
         Boolean(row.strict_legal_combos)!==Boolean(row.compatible_hole_card_pairs)||
         row.status!==(row.strict_legal_combos?'POSITIVE_JOINT_REACH':'ZERO_JOINT_REACH'))
        throw Error('原始來源與模型、行動或座位不符');
      if(scopeFields.some(f=>f in row) &&
         (!scopeFields.every(f=>Number.isSafeInteger(row[f])&&row[f]>=0) ||
          (row.root_applied_rust_lock_nodes+row.subgame_applied_rust_lock_nodes>0)===gto))
        throw Error('原始套鎖節點數不符');
      const source=sourceKey(row.source_run_id,row.source_sha256,row.version,row.spot);
      if(!index.has(source))index.set(source,new Map());
      const nodes=index.get(source), node=nodeKey(row.public_board,row.line,seat);
      let verified=nodes.get(node);
      if(!verified){
        verified={...row};delete verified.gto;nodes.set(node,verified);
      }else{
        for(const f of ['family','flop','turn','status','source_hand_order_sha256','source_actions','source_hand_count',
          'compatible_action_mask_b64','strict_legal_combos','compatible_hole_card_pairs','compatible_opponent_combos',
          'b50','gto_gap_pct','locked_hero_gap_pct',...scopeFields,'root_sha256','root_gto_stage_gap_pct','root_locked_hero_gap_pct']){
          if(f in row && f in verified && !same(row[f],verified[f]))throw Error('同一來源有相衝的手牌證據');
          if(f in row)verified[f]=row[f];
        }
      }
      const target=gto?result.gto_references:result.references;
      if(target[key] && target[key]!==verified)throw Error('同一模型來源的解算範圍不符');
      target[key]=verified;
      return model;
    }
    for(const report of reports){
      if(!report.references||Array.isArray(report.references)||typeof report.references!=='object'||
         ('unresolved' in report && (!report.unresolved||Array.isArray(report.unresolved)||typeof report.unresolved!=='object'))||
         ('gto_references' in report && (!report.gto_references||Array.isArray(report.gto_references)||typeof report.gto_references!=='object')))
        throw Error('雙方可達性來源清單格式不符');
      for(const [key,row] of Object.entries(report.references)){
        const model=register(key,row,false);
        if(row.gto!=null){
          if(!['spot','family','flop','turn','public_board','line','acting_seat'].every(f=>row[f]===row.gto[f]))
            throw Error('相對應的 GTO 節點不符');
          const g=row.gto, gkey=JSON.stringify([model,g.public_board,g.line,g.acting_seat,g.source_run_id,g.source_sha256]);
          if(links.has(key)&&links.get(key)!==gkey)throw Error('鎖頻與原始 GTO 配對不符');
          links.set(key,gkey);register(gkey,g,true);
        }
      }
      for(const [key,row] of Object.entries(report.gto_references||{}))register(key,row,true);
      for(const [key,item] of Object.entries(report.unresolved||{})){
        const [mid,public_board,line,acting_seat,source_run_id,source_sha256]=JSON.parse(key);
        const exact={public_board,line,acting_seat,source_run_id,source_sha256};
        if(typeof mid!=='string'||!mid||typeof public_board!=='string'||typeof line!=='string'||
           key!==JSON.stringify([mid,public_board,line,acting_seat,source_run_id,source_sha256])||
           ![0,1].includes(acting_seat)||!Number.isSafeInteger(source_run_id)||source_run_id<=0||!/^[a-f0-9]{64}$/.test(source_sha256)||
           !['gto',acting_seat?'exp_ip':'exp_oop'].includes(item.version)||typeof item.reason!=='string'||!item.reason.trim()||
           Object.keys(exact).some(k=>k in item&&item[k]!==exact[k])||
           ['strict_legal_combos','compatible_action_mask_b64','b50'].some(f=>f in item)||
           (pending.has(key)&&pending.get(key).version!==item.version))throw Error('待核對原始來源格式不符');
        pending.set(key,{...item,...exact,status:unresolved});
      }
    }
    for(const [key,row] of pending){
      const target=row.version==='gto'?result.gto_references:result.references;
      if(target[key])continue;
      const source=sourceKey(row.source_run_id,row.source_sha256,row.version,row.spot??null);
      if(!index.has(source))index.set(source,new Map());
      const nodes=index.get(source), node=nodeKey(row.public_board,row.line,row.acting_seat);
      if(!nodes.has(node))nodes.set(node,row);
      target[key]=nodes.get(node);
    }
    indexes.set(result,index);
    return result;
  }
  function sourceIndex(report){
    if(!indexes.has(report))indexes.set(report,indexes.get(combine([report])));
    return indexes.get(report);
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
    if(source.requires_native_joint_replay){
      const base=lookup(report,model,board,{version:'gto',source_run_id:board.source_run_id,source_sha256:board.source_sha256});
      if(row?.status!=='POSITIVE_JOINT_REACH'||base?.status!=='POSITIVE_JOINT_REACH'||
         !same(row.source_actions,board.exact_node_actions)||!same(base.source_actions,row.source_actions)||
         !row.source_actions.includes('b50')||row.strict_legal_combos!==source.strictly_reachable_combos||
         !(row.subgame_applied_rust_lock_nodes>0))throw Error('附加鎖頻缺少原始選單的雙方可達性證據');
    }
    if(!row)return null;
    if(row.status===unresolved){
      if(row.version!==source.version || row.source_run_id!==run || row.source_sha256!==sha ||
         (row.spot!=null&&row.spot!==model.solver_profile)||(row.family!=null&&row.family!==model.family)||
         (row.flop!=null&&row.flop!==board.flop)||(row.turn!=null&&row.turn!==board.turn))
        throw Error('待核對來源與模型不符');
      return row;
    }
    if(row.spot!==model.solver_profile||row.family!==model.family||row.flop!==board.flop||row.turn!==board.turn||
       row.public_board!==board.public_board||row.line!==board.actual_exact_action_line||row.acting_seat!==board.acting_seat||
       row.version!==source.version||row.source_run_id!==run||row.source_sha256!==sha||
       !['POSITIVE_JOINT_REACH','ZERO_JOINT_REACH'].includes(row.status))throw Error('原始 run、SHA、牌面或座位不符');
    return row;
  }
  async function bindCase(report,actual,run=actual.source_run_id){
    const sources=sourceIndex(report), index=sources.get(sourceKey(run,actual.source_sha256,actual.version,actual.spot));
    const unknown=sources.get(sourceKey(run,actual.source_sha256,actual.version,null));
    const verified=new Map();
    if(!index&&!unknown)return verified;
    await Promise.all(actual.nodes.map(async node=>{
      const key=nodeKey(node.public_board??node.board,node.exact_node_line??node.line,node.acting_seat);
      const row=index?.get(key)??unknown?.get(key);
      if(row){
        const mask=row.status===unresolved?null:await bindMask(row,actual,node);
        verified.set(node,{row,mask});
      }
    }));
    return verified;
  }
  function describe(row){
    if(!row) return '50% pot 的雙方可達組合尚未核對。';
    if(row.status===unresolved)return '尚缺可重算的原始子局。雙方可達手牌與 50% 下注證據仍待核對。';
    const scope=row.version!=='gto'&&scopeFields.every(f=>Number.isSafeInteger(row[f]))?
      '實際套鎖節點為翻牌父樹 '+row.root_applied_rust_lock_nodes+' 個、轉河子樹 '+row.subgame_applied_rust_lock_nodes+' 個。':'';
    if(row.status==='ZERO_JOINT_REACH')return scope+'雙方可達配牌為 0；這條行動線沒有可評估的 50% 下注。';
    const b=row.b50, counts=scope+'雙方可達 '+row.strict_legal_combos+' 組英雄手牌、'+row.compatible_hole_card_pairs+' 組雙方配牌。';
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
