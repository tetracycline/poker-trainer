#!/usr/bin/env python3
"""Activate V45 157 CERT rank71 3 original LMP50+real NL2 BB-OOP boards only
after strict source+HU2475 PASS. Preserve old V44/V43 immutable fallback;
do not generalize per-texture GTO or turn pooled NL2 marginal to private-hand rates.
"""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATUS=ROOT/'data/nl2_hu_multiboard_status_v45_b345_rank71.json'
PARENT=ROOT/'data/nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json'
MID='ln-iso-lmp_r_model-vlgh2t'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    s=json.loads(STATUS.read_text())
    assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V45_B345_RANK71'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(157,235,0,392)
    assert s['parent_v44_sha256']==sha(PARENT)
    q=s['B345_rank71_true_3_flop_GTO_NL2_OOP_evidence']
    assert q['third_flop']=='3s3h2d' and q['third_turn']=='7d'
    assert q['flops']==['4s4h2d','7s5h3d','3s3h2d']
    assert len(q['textures'])>=2 and set(['PAIRED','LOW']).issubset(set(q['textures']))
    assert q['source_tree']=='RESTRICTED_LMP_50_ONLY_100BB_ASSUMED_PREFLOP'
    assert q['never_claim_unrestricted_game_or_private_hand_NL2_observation']
    assert len(q['original_archive_provenance'])==3
    for v in q['original_archive_provenance']:
        assert len(v['original_gto_case_sha256'])==64 and len(v['real_NL2_actor_partial_case_sha256'])==64
        assert len(v['archive_sha256'])==64 and len(v['index_sha256'])==64
    model=s['records'][MID]
    assert model['label']=='CERT-MULTIBOARD' and model['proven_exact_board_count']==3
    assert len(model['certified_3_to_5_exact_flop_boards'])==3
    assert all(b['acting_seat']==0 and b['actual_exact_action_line']=='b50 c/x b50 c/' and
       b['relative_spr_error_pct']<=5 and b['nl2_locked_variants'][0]['version']=='exp_oop' for b in model['certified_3_to_5_exact_flop_boards'])
    assert s['no_generic_texture_GTO'] and s['no_observed_private_card_NL2_rates']
    assert s['PR2_remains_draft_never_merge']
    validator="""const v45=d=>{
 const q=d.B345_rank71_true_3_flop_GTO_NL2_OOP_evidence;
 const b=d.records?.['ln-iso-lmp_r_model-vlgh2t'];
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V45_B345_RANK71'||
    d.CERT_MULTIBOARD!==157||d.APPROX!==235||d.EST!==0||d.TOTAL!==392||
    d.parent_v44_sha256?.length!==64||
    q?.third_flop!=='3s3h2d'||q?.third_turn!=='7d'||
    q?.flops?.join(',')!=='4s4h2d,7s5h3d,3s3h2d'||
    q?.textures?.length<2||!['PAIRED','LOW'].every(t=>q.textures.includes(t))||
    q?.source_tree!=='RESTRICTED_LMP_50_ONLY_100BB_ASSUMED_PREFLOP'||
    q?.never_claim_unrestricted_game_or_private_hand_NL2_observation!==true||
    q?.original_archive_provenance?.length!==3||
    q.original_archive_provenance.some(p=>
       p.original_GTO_run<=0||p.original_gto_case_sha256?.length!==64||
       p.real_NL2_actor_partial_case_sha256?.length!==64||
       p.index_sha256?.length!==64||p.archive_sha256?.length!==64)||
    b?.label!=='CERT-MULTIBOARD'||b?.proven_exact_board_count!==3||
    b.certified_3_to_5_exact_flop_boards?.length!==3||
    b.certified_3_to_5_exact_flop_boards.some(p=>
       p.acting_seat!==0||p.actual_exact_action_line!=='b50 c/x b50 c/'||
       p.relative_spr_error_pct>5||p.strict_full_street_combo_reachable<=0||
       p.nl2_locked_variants?.[0]?.version!=='exp_oop')||
    d.records?.['ln-ipfr-t_model-hxdit']?.label!=='CERT-MULTIBOARD'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||Object.keys(d.records||{}).length!==392)
      throw Error('V45 rank71 3 genuine 100bb original restricted LMP50 GTO and real NL2 actor BB OOP SHA source failclosed');
 return d;
};
"""
    old_fetch="return fetch('data/nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json',{cache:'no-store'}).then(open).then(v44)"
    new_fetch=("return fetch('data/nl2_hu_multiboard_status_v45_b345_rank71.json',{cache:'no-store'}).then(open).then(v45)\n"
      "   .catch(()=>fetch('data/nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json',{cache:'no-store'}).then(open).then(v44))")
    lookup="""  if(chosenBoard.source_kind?.includes('OFFICIAL')&&!hasVerifiedBatch){"""
    extra="""  if(chosenModel?.model_id==='ln-iso-lmp_r_model-vlgh2t'&&
     chosenBoard?.actual_exact_action_line==='b50 c/x b50 c/'&&
     sourceSha(source)?.length===64){
    const origin=status?.B345_rank71_true_3_flop_GTO_NL2_OOP_evidence?.
      original_archive_provenance?.find(x=>x.flop===chosenBoard.flop&&x.turn===chosenBoard.turn);
    if(origin&&run===origin.original_GTO_run&&
       ((version==='gto'&&digest===origin.original_gto_case_sha256)||
        (version!=='gto'&&digest===origin.real_NL2_actor_partial_case_sha256))){
      setMessage(version==='gto'
       ?'此具名公牌為原始 100bb 50%-only 限定下注樹真實 Rust GTO，嚴格 40%／70% 前街合法且 BB-OOP SPR 相符；非不限尺寸的 GTO。'
       :'此具名公牌有獨立 Rust 局部 NL2 BB-OOP 鎖頻來源，僅街別與下注尺寸玩家池邊際頻率；不是逐私牌條件式實測資料。');
      const link=document.createElement('a');
      link.href=sourceUrl(run);link.target='_blank';link.rel='noopener';
      link.textContent='檢視此 GTO／NL2 具名牌面原始 Rust Actions Run '+run;
      el('details').appendChild(link);el('combo-rows').replaceChildren();return;
    }
  }
"""
    for name in ('nl2-multiboard.js','nl2_hu_multiboard_ui.js'):
        p=ROOT/name;raw=p.read_text()
        assert raw.count('const v44=d=>{')==1
        assert 'const v45=d=>{' not in raw
        assert raw.count(old_fetch)==1
        raw=raw.replace('const v44=d=>{',validator+'const v44=d=>{')
        raw=raw.replace(old_fetch,new_fetch)
        if name=='nl2-multiboard.js':
            assert raw.count(lookup)==1
            raw=raw.replace(lookup,extra+lookup)
        p.write_text(raw)
    print('PASS V45 157 CERT/235 APPROX, 3 genuine restricted LMP50 original GTO and independent real NL2 BB-OOP actor source board links; immutable V44 fallback')
if __name__=='__main__':main()
