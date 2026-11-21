#!/usr/bin/env python3
"""V41 exact rank61 GTO+NL2 CO-IP source-guard UI primary, V40-V26 fallback.
Source proof only named public board, exact actor and action history.
The GTO cases and real Rust downstream NL2 partial locks must NOT be conflated.
"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/'data/nl2_hu_multiboard_status_v41_b271_rank61.json'
OLD=ROOT/'data/nl2_hu_multiboard_status_v40_b265_rank313.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert STATUS.is_file() and OLD.is_file()
    s=json.loads(STATUS.read_text())
    assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(154,238,0,392)
    assert s['parent_v40_sha256']==sha(OLD)
    meta=s['B271_rank61_three_authentic_GTO_NL2_CO_IP_flops']
    assert (meta['rank'],meta['model_id'],meta['actor'],meta['exact_line'])==(
       61,'ln-ipfr-t_model-qpx6tn','CO_IP','x b100 c/x')
    assert meta['flops']==['Js9h5d','KsQh4d','QsJh4d']
    assert len(meta['original_GTO_and_NL2_actor_locked_source_pins'])==3
    assert meta['true_100bb_preflop_CFR_source_frozen_not_observed_NL2_private_card']
    assert meta['only_exact_public_board_actions_actor_SPR_certified']
    assert s['records'][meta['model_id']]['label']=='CERT-MULTIBOARD'
    assert s['records'][meta['model_id']]['proven_exact_board_count']==3
    assert s['no_generic_texture_GTO'] and s['no_observed_private_card_NL2_rates']
    assert s['PR2_remains_draft_never_merge']
    old="return fetch('data/nl2_hu_multiboard_status_v40_b265_rank313.json',{cache:'no-store'}).then(open).then(v40)"
    new=("return fetch('data/nl2_hu_multiboard_status_v41_b271_rank61.json',{cache:'no-store'}).then(open).then(v41)\n"
        "   .catch(()=>fetch('data/nl2_hu_multiboard_status_v40_b265_rank313.json',{cache:'no-store'}).then(open).then(v40))")
    validator="""const v41=d=>{
 const z=d.B271_rank61_three_authentic_GTO_NL2_CO_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V41_B271_RANK61'||
    d.CERT_MULTIBOARD!==154||d.APPROX!==238||d.EST!==0||d.TOTAL!==392||
    d.parent_v40_sha256?.length!==64||
    z?.rank!==61||z?.model_id!=='ln-ipfr-t_model-qpx6tn'||
    z?.flops?.join(',')!=='Js9h5d,KsQh4d,QsJh4d'||
    z?.exact_line!=='x b100 c/x'||z?.actor!=='CO_IP'||
    z?.true_100bb_preflop_CFR_source_frozen_not_observed_NL2_private_card!==true||
    z?.only_exact_public_board_actions_actor_SPR_certified!==true||
    z?.original_GTO_and_NL2_actor_locked_source_pins?.length!==3||
    z?.original_GTO_and_NL2_actor_locked_source_pins?.some(p=>
      !['KsQh4d','Js9h5d','QsJh4d'].includes(p.flop)||
      ![44902146101,44902831383,44934430727].includes(p.original_GTO_run)||
      ![44902973337,44903478906,44935281174].includes(p.source_lock_run)||
      p.pin_sha256?.length!==64||p.gto_archive_sha256?.length!==64||
      p.NL2_archive_sha256?.length!==64||
      p.GTO_strict_actor_combos<=0||p.NL2_SPR_eligible_combos<=0)!==false||
    d.records?.['ln-ipfr-t_model-qpx6tn']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipfr-t_model-qpx6tn']?.proven_exact_board_count!==3||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-opfr-t_model-1hmsxaw']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
    throw Error('V41 exact source-rank61 three original CO-IP GTO + true NL2 Rust source gate failed');
 return d;
};
 """
    src_anchor="const v40=d=>{"
    guard_anchor=" if(chosenBoard.source_kind?.includes('OFFICIAL')&&!hasVerifiedBatch){"
    exact_scope=""" if(chosenModel?.model_id==='ln-ipfr-t_model-qpx6tn'&&
     chosenBoard?.actual_exact_action_line==='x b100 c/x'&&
     sourceSha(source)?.length===64){
   const z=status?.B271_rank61_three_authentic_GTO_NL2_CO_IP_flops?.
     original_GTO_and_NL2_actor_locked_source_pins?.find(x=>
       x.flop===chosenBoard?.flop&&x.turn===chosenBoard?.turn);
   if(z&&((version==='gto'&&run===z.original_GTO_run)||
          (version!=='gto'&&run===z.source_lock_run))){
     setMessage(version==='gto'
       ?'這是固定翻前 CFR 的真實 100bb Rust GTO 具名公牌；僅限此動作歷史、actor、SPR，非逐私牌實測 NL2 策略。來源 SHA 與嚴格前街 reach 在 GitHub Actions 可核。'
       :'此來源是真實 Rust 後續轉河牌 NL2 局部 node-lock，與 GTO 分開求解。NL2 玩家池只具備街別／尺寸邊際統計，來源分母未知不等於零、不得稱為逐私牌實測。');
     const link=document.createElement('a');
     link.href=sourceUrl(run);link.target='_blank';link.rel='noopener';
     link.textContent='檢視精確具名公牌的原始 GitHub Actions Run '+run;
     el('details').appendChild(link);el('combo-rows').replaceChildren();return;
   }
 }
 """
    for file in (ROOT/'nl2-multiboard.js',ROOT/'nl2_hu_multiboard_ui.js'):
        raw=file.read_text()
        assert raw.count(src_anchor)==1 and raw.count(old)==1,file
        assert "const v41=d=>{" not in raw
        raw=raw.replace(src_anchor,validator+src_anchor).replace(old,new)
        if file.name=='nl2-multiboard.js':
            assert raw.count(guard_anchor)==1
            raw=raw.replace(guard_anchor,exact_scope+guard_anchor)
        file.write_text(raw)
    print('PASS V41 exact source guarded, GTO and NL2 partial never conflated, V40-V26 unchanged fallbacks')
if __name__=='__main__':main()
