#!/usr/bin/env python3
"""B355: failclosed V46 158/234 rank79 3 actual original GTO+real NL2 CO-IP
100bb board sources as UI primary, with immutable V45 and V44 fallbacks.
"""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
NEW=R/'data/nl2_hu_multiboard_status_v46_b354_rank79.json'
PARENT=R/'data/nl2_hu_multiboard_status_v45_b345_rank71.json'
MID='ln-ipc-t_model-1cla93g'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=json.loads(NEW.read_text())
 assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79'
 assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(158,234,0,392)
 assert s['parent_v45_sha256']==sha(PARENT)
 q=s['B354_rank79_three_true_original_GTO_NL2_CO_IP_flops']
 assert q['rank']==79 and q['model_id']==MID and q['actor']=='CO_IP'
 assert q['exact_line']=='b50 c/x' and q['SPR']==7
 assert q['flops']==['Ks7h2d','8s8h3d','Js9h4d']
 assert len(q['textures'])>=2 and len(q['source_run_shas'])==3
 assert q['genuine_source_GTO_3_and_actor_NL2_3']
 assert q['historic_source_original_run']==44654973894
 assert q['no_observed_private_card_conditional_NL2_villain_rates']
 for item in q['source_run_shas']:
  assert item['run']>0 and len(item['GTO_SHA'])==len(item['NL2_SHA'])==64
 rec=s['records'][MID]
 assert rec['label']=='CERT-MULTIBOARD' and rec['proven_exact_board_count']==3
 assert all(x['acting_seat']==1 and x['actual_exact_action_line']=='b50 c/x' and
     x['relative_spr_error_pct']<=5 and
     x['nl2_locked_variants'][0]['version']=='exp_ip' for x in rec['certified_3_to_5_exact_flop_boards'])
 assert s['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='CERT-MULTIBOARD'
 assert s['no_generic_texture_GTO'] and s['no_observed_private_card_NL2_rates']
 assert s['PR2_remains_draft_never_merge']
 validator="""const v46=d=>{
 const q=d.B354_rank79_three_true_original_GTO_NL2_CO_IP_flops;
 const r=d.records?.['ln-ipc-t_model-1cla93g'];
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V46_B354_RANK79'||
    d.CERT_MULTIBOARD!==158||d.APPROX!==234||d.EST!==0||d.TOTAL!==392||
    d.parent_v45_sha256?.length!==64||
    q?.rank!==79||q?.model_id!=='ln-ipc-t_model-1cla93g'||
    q?.actor!=='CO_IP'||q?.spot!=='UTG_CO'||q?.exact_line!=='b50 c/x'||q?.SPR!==7||
    q?.flops?.join(',')!=='Ks7h2d,8s8h3d,Js9h4d'||
    q?.textures?.length<2||new Set(q.textures).size<2||
    q?.source_run_shas?.length!==3||q?.historic_source_original_run!==44654973894||
    q?.genuine_source_GTO_3_and_actor_NL2_3!==true||
    q?.no_observed_private_card_conditional_NL2_villain_rates!==true||
    q.source_run_shas.some(p=>p.run<=0||p.GTO_SHA?.length!==64||p.NL2_SHA?.length!==64)||
    r?.label!=='CERT-MULTIBOARD'||r?.proven_exact_board_count!==3||
    r.certified_3_to_5_exact_flop_boards?.length!==3||
    r.certified_3_to_5_exact_flop_boards.some(p=>
       p.acting_seat!==1||p.actual_exact_action_line!=='b50 c/x'||
       p.strict_full_street_combo_reachable<=0||p.relative_spr_error_pct>5||
       p.nl2_locked_variants?.[0]?.version!=='exp_ip')||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='CERT-MULTIBOARD'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||Object.keys(d.records||{}).length!==392)
      throw Error('V46 rank79 3 real UTGCO original GTO plus genuine NL2 COIP actor source SHA failclosed');
 return d;
};
"""
 old="return fetch('data/nl2_hu_multiboard_status_v45_b345_rank71.json',{cache:'no-store'}).then(open).then(v45)"
 new=("return fetch('data/nl2_hu_multiboard_status_v46_b354_rank79.json',{cache:'no-store'}).then(open).then(v46)\n"
       "   .catch(()=>fetch('data/nl2_hu_multiboard_status_v45_b345_rank71.json',{cache:'no-store'}).then(open).then(v45))")
 existing=" if(chosenBoard.source_kind?.includes('OFFICIAL')&&!hasVerifiedBatch){"
 extra=""" if(chosenModel?.model_id==='ln-ipc-t_model-1cla93g'&&
    chosenBoard?.actual_exact_action_line==='b50 c/x'&&sourceSha(source)?.length===64){
   const p=status?.B354_rank79_three_true_original_GTO_NL2_CO_IP_flops?.
      source_run_shas?.find(x=>x.flop===chosenBoard.flop&&x.turn===chosenBoard.turn);
   if(p&&run===p.run&&((version==='gto'&&digest===p.GTO_SHA)||
      (version!=='gto'&&digest===p.NL2_SHA))){
      setMessage(version==='gto'
       ?'此具名公牌有原始 100bb UTGCO Rust GTO，CO-IP b50 c/x 嚴格前街 40%／70% 及 SPR 已查核；不能推廣到其他牌面。'
       :'此具名公牌有獨立真正 Rust NL2 CO-IP 局部鎖頻來源；只有街別及下注尺寸玩家池邊際頻率，不是逐私牌條件式實測策略。');
      const link=document.createElement('a');link.href=sourceUrl(run);
      link.target='_blank';link.rel='noopener';
      link.textContent='檢視 rank79 精確具名牌面原始 GTO／NL2 Rust Actions '+run;
      el('details').appendChild(link);el('combo-rows').replaceChildren();return;
   }
 }
"""
 for path in ('nl2-multiboard.js','nl2_hu_multiboard_ui.js'):
  f=R/path;raw=f.read_text()
  assert raw.count('const v45=d=>{')==1 and raw.count(old)==1
  assert 'const v46=d=>{' not in raw
  raw=raw.replace('const v45=d=>{',validator+'const v45=d=>{')
  raw=raw.replace(old,new)
  if path=='nl2-multiboard.js':
   assert raw.count(existing)==1
   raw=raw.replace(existing,extra+existing)
  f.write_text(raw)
 print('PASS B355 V46 primary exact rank79 actor GTO/NL2 158/234, V45/V44 immutable failclosed fallbacks')
if __name__=='__main__':main()
