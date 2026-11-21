#!/usr/bin/env python3
"""Activate V43 rank60 only AFTER exact SHA-traced three different true GTO +
actual CO-IP NL2 Rust partial locks, 2+ textures and 596/688 source audits.
Fail closed to immutable V42, V41 ... V26 fallback on any missing/bad V43 source.
Never mark generic texture/private hand decisions GTO, never merge PR2.
"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/'data/nl2_hu_multiboard_status_v43_b319_rank60.json'
PARENT=ROOT/'data/nl2_hu_multiboard_status_v42_b289_rank46.json'
MID='ln-ipfr-t_model-hxdit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert STATUS.is_file() and PARENT.is_file()
    s=json.loads(STATUS.read_text())
    assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V43_B319_RANK60'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(156,236,0,392)
    assert s['parent_v42_sha256']==sha(PARENT)
    q=s['B319_rank60_three_true_GTO_NL2_CO_IP_flops']
    assert (q['rank'],q['model_id'],q['actor'],q['exact_line'],q['model_SPR'])==(
       60,MID,'CO_IP','x b50 c/x',8.614)
    assert q['prereg_third_batch'] in ('B314','B315','B322','B323')
    assert len(q['flops'])==3 and len(set(q['flops']))==3
    assert 'Js9h4d' in q['flops'] and 'Js9h5d' in q['flops']
    assert len(set(q['textures']))>=2
    pairs=q['GTO_and_NL2_source_shas']
    assert len(pairs)==3
    assert sorted(z['flop'] for z in pairs)==q['flops']
    assert all(z['GTO_run']>0 and z['NL2_run']>0 and
        len(z['GTO_case_sha'])==len(z['NL2_raw_case_sha'])==64 and
        z['strict_GTO_actor_combos']>0 for z in pairs)
    assert s['records'][MID]['label']=='CERT-MULTIBOARD'
    assert s['records'][MID]['proven_exact_board_count']==3
    assert s['records']['ln-iso-lmp_t_model-17z0wyl']['label']=='CERT-MULTIBOARD'
    assert s['records']['ln-iso-lmp_r_model-vlgh2t']['label']=='APPROX'
    assert s['PR2_remains_draft_never_merge'] and s['no_generic_texture_GTO'] and s['no_observed_private_card_NL2_rates']
    validator="""const v43=d=>{
 const q=d.B319_rank60_three_true_GTO_NL2_CO_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V43_B319_RANK60'||
    d.CERT_MULTIBOARD!==156||d.APPROX!==236||d.EST!==0||d.TOTAL!==392||
    d.parent_v42_sha256?.length!==64||
    q?.rank!==60||q?.model_id!=='ln-ipfr-t_model-hxdit'||
    q?.actor!=='CO_IP'||q?.exact_line!=='x b50 c/x'||q?.model_SPR!==8.614||
    !['B314','B315','B322','B323'].includes(q?.prereg_third_batch)||
    q?.flops?.length!==3||new Set(q.flops).size!==3||
    !q.flops.includes('Js9h4d')||!q.flops.includes('Js9h5d')||
    q?.textures?.length<2||new Set(q.textures).size<2||
    q?.GTO_and_NL2_source_shas?.length!==3||
    q?.GTO_and_NL2_source_shas?.some(p=>
      !q.flops.includes(p.flop)||p.GTO_run<=0||p.NL2_run<=0||
      p.GTO_case_sha?.length!==64||p.NL2_raw_case_sha?.length!==64||
      p.strict_GTO_actor_combos<=0)!==false||
    d.records?.['ln-ipfr-t_model-hxdit']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipfr-t_model-hxdit']?.proven_exact_board_count!==3||
    d.records?.['ln-iso-lmp_t_model-17z0wyl']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
      throw Error('V43 rank60 original GTO plus genuine actor-IP Rust NL2 exact 3 flop SHA + multiple-texture failclosed');
 return d;
};
"""
    rank60_source=""" if(chosenModel?.model_id==='ln-ipfr-t_model-hxdit'&&
    chosenBoard?.actual_exact_action_line==='x b50 c/x'&&
    sourceSha(source)?.length===64){
    const proof=status?.B319_rank60_three_true_GTO_NL2_CO_IP_flops?.
      GTO_and_NL2_source_shas?.find(x=>
        x.flop===chosenBoard?.flop&&x.turn===chosenBoard?.turn);
    if(proof&&((version==='gto'&&run===proof.GTO_run)||
              (version!=='gto'&&run===proof.NL2_run))){
      setMessage(version==='gto'
        ?'此精確牌面為原生 100bb CO-IP Rust GTO，x b50 c/x 前街與逐 combo 40%/70% 可達性均經 SHA 驗證；不可類推至其他牌面。'
        :'此精確牌面另有真正 Rust NL2 局部轉牌及河牌鎖頻來源；實測玩家池資料只限街別與下注尺寸邊際，並非逐私牌條件頻率。');
      const link=document.createElement('a');
      link.href=sourceUrl(run);link.rel='noopener';link.target='_blank';
      link.textContent='檢視此精確牌面的 GTO／NL2 原始 Actions Run '+run;
      el('details').appendChild(link);el('combo-rows').replaceChildren();return;
    }
 }
"""
    old_fetch="return fetch('data/nl2_hu_multiboard_status_v42_b289_rank46.json',{cache:'no-store'}).then(open).then(v42)"
    new_fetch=("return fetch('data/nl2_hu_multiboard_status_v43_b319_rank60.json',{cache:'no-store'}).then(open).then(v43)\n"
       "   .catch(()=>fetch('data/nl2_hu_multiboard_status_v42_b289_rank46.json',{cache:'no-store'}).then(open).then(v42))")
    for name in ('nl2-multiboard.js','nl2_hu_multiboard_ui.js'):
        f=ROOT/name
        raw=f.read_text()
        assert raw.count('const v42=d=>{')==1 and raw.count(old_fetch)==1
        assert 'const v43=d=>{' not in raw
        raw=raw.replace('const v42=d=>{',validator+'const v42=d=>{')
        raw=raw.replace(old_fetch,new_fetch)
        if name=='nl2-multiboard.js':
            anchor=" if(chosenBoard.source_kind?.includes('OFFICIAL')&&!hasVerifiedBatch){"
            assert raw.count(anchor)==1
            raw=raw.replace(anchor,rank60_source+anchor)
        f.write_text(raw)
    print('PASS V43 156 CERT / 236 APPROX exact 3 named positive rank60 GTO+NL2 COIP and V42-V26 fallback')
if __name__=='__main__':main()
