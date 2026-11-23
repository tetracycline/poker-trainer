// Audit disclosures are keyed to the original Rust run and subgame SHA.
(() => {
  const path='data/nl2_hu_b475_verified_lock_scope.json';
  const streets=['翻牌','轉牌','河牌'];
  let loaded;
  function select(report,model,board,lock) {
    if(report.schema!=='NL2_VERIFIED_ORIGINAL_POOL_SOURCE_SCOPE_V1' ||
       report.pool_sha256!=='c2d7c8a6b0dd044a5e546256207a6e46f626b083ecb598b1e6d98bb928611c4a') {
      throw Error('pool source scope mismatch');
    }
    const row=report.sources[lock.run_id+'/'+lock.sha256];
    if(!row || row.spot!==model.solver_profile || row.flop!==board.flop ||
       row.turn!==board.turn || row.version!==lock.version) return null;
    return row;
  }
  function element(tag,content) {
    const el=document.createElement(tag);
    if(content!==undefined) el.textContent=String(content);
    return el;
  }
  function render(parent,report,model,board,lock) {
    const row=select(report,model,board,lock);
    const details=element('details');
    if(lock.measurement_policy==='STREET_SPECIFIC_POOL_MARGINALS' && lock.viewer_sha256 &&
       lock.pool_sha256===report.pool_sha256 && Array.isArray(lock.applied_street_rates)){
      details.appendChild(element('summary','NL2 鎖 '+lock.run_id+'｜已核實逐街池頻率'));
      for(const r of lock.applied_street_rates){
        const rate=report.pool_by_action_and_street[r.token]?.[r.street-1];
        if(rate) details.appendChild(element('p',streets[r.street-1]+' '+r.token.slice(1)+'% pot：'+
          rate.n.toLocaleString('zh-TW')+' 次池決策，Rust 鎖後棄／加 '+r.fold_pct+'%／'+r.raise_pct+'%。'));
      }
      parent.appendChild(details);return;
    }

    const prefix='NL2 鎖 '+lock.run_id+'｜';
    const title=row?.scope==='CONFIRMED' ? '已核實跨街沿用翻牌頻率' :
      row ? '已檢查封存，本輪未確認跨街沿用' : '本輪未核對此來源';
    details.appendChild(element('summary',prefix+title));
    if(row?.scope==='CONFIRMED'){
      details.appendChild(element('p','這份局部鎖的原始規則依順序比對。本輪在封存的可達對手決策中發現以下跨街套用。每個樣本數都是全池該街與尺寸的決策次數。'));
      for(const proof of row.evidence) {
        const actual=proof.action.slice(1)+'% pot：原始 Rust 對此規則回報的全樹加權棄／加為 '+proof.applied_fold_pct+'%／'+proof.applied_raise_pct+
          '%。先匹配的翻牌來源有 '+proof.first_matching_source_n.toLocaleString('zh-TW')+' 次決策。';
        details.appendChild(element('p',actual));
        const table=element('table'),thead=element('thead'),head=element('tr');
        for(const label of ['原始池來源','樣本數','棄／跟／加 %','此封存確認沿用的後街節點數']) head.appendChild(element('th',label));
        thead.appendChild(head);table.appendChild(thead);
        const body=element('tbody');
        report.pool_by_action_and_street[proof.action].forEach((rate,index)=>{
          const tr=element('tr');
          for(const v of [streets[index],rate.n.toLocaleString('zh-TW'),rate.fold+' / '+rate.call+' / '+rate.raise,
            index===0?'—':(proof.observed_later_street_node_counts[String(index+1)]||0)]) tr.appendChild(element('td',v));
          body.appendChild(tr);
        });
        table.appendChild(body);details.appendChild(table);
      }
      details.appendChild(element('p','節點數依本次匯出的公牌與行動線計算。歷史鎖仍採其原始輸入。'));
    } else {
      details.appendChild(element('p',row ? '已比對固定玩家池與求解來源。這份封存沒有足夠證據確認同一個翻牌尺寸規則套用至可達的後街決策。':
        '本輪可核對的歷史封存沒有這組 run、SHA 與牌面；跨街頻率適用情形仍待驗證。'));
    }
    if(row && /^NL2_MULTIBOARD_[A-Za-z0-9_]+\.json\.gz$/.test(row.archive)){
      const link=element('a','查閱這個原始求解來源的封存檔');
      link.href='data/solver_evidence/'+encodeURIComponent(row.archive);
      details.appendChild(link);
    }
    parent.appendChild(details);
  }
  function show(parent,model,board,locks) {
    if(!parent || !locks.length) return;
    // Each selection gets its own mount so a delayed response cannot populate a later board.
    const mount=element('div');
    parent.appendChild(mount);
    loaded ??=fetch(path,{cache:'no-store'}).then(r=>{
      if(!r.ok) throw Error('pool scope HTTP '+r.status);
      return r.json();
    }).catch(e=>{loaded=undefined;throw e;});
    return loaded.then(report=>{
      for(const lock of locks) render(mount,report,model,board,lock);
    }).catch(()=>{mount.textContent='歷史 NL2 鎖頻來源比較暫時無法載入。';});
  }
  globalThis.nl2PoolRateScope={select,show};
})();
