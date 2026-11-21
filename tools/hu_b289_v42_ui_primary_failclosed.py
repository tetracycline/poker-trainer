#!/usr/bin/env python3
"""B289 V42 source-guard exact rank46 three GTO+actual Rust NL2 CO-IP
on named public boards only; V41-V26 immutable fallbacks remain available.
"""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/'data/nl2_hu_multiboard_status_v42_b289_rank46.json'
PARENT=ROOT/'data/nl2_hu_multiboard_status_v41_b271_rank61.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert STATUS.is_file() and PARENT.is_file()
    q=json.loads(STATUS.read_text())
    assert q['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46'
    assert (q['CERT_MULTIBOARD'],q['APPROX'],q['EST'],q['TOTAL'])==(155,237,0,392)
    assert q['parent_v41_sha256']==sha(PARENT)
    x=q['B289_rank46_three_true_GTO_NL2_CO_IP_flops']
    assert (x['rank'],x['model_id'],x['actor'],x['exact_line'])==(
       46,'ln-iso-lmp_t_model-17z0wyl','CO_IP','x b50 c/x')
    assert x['flops']==['7s7h2d','8s8h3d','9s6h3d']
    assert x['third_B286_original_GTO_strict_combos']==12
    assert x['third_B288_actual_NL2_actor_SPR_strict_combos']==12
    assert x['assumed_limped_169class_preflop_not_observed_NL2_private_cards'] is True
    assert len(x['GTO_and_NL2_source_shas'])==3
    assert q['records'][x['model_id']]['label']=='CERT-MULTIBOARD'
    assert q['records'][x['model_id']]['proven_exact_board_count']==3
    assert q['no_generic_texture_GTO'] and q['no_observed_private_card_NL2_rates']
    assert q['PR2_remains_draft_never_merge']
    old="return fetch('data/nl2_hu_multiboard_status_v41_b271_rank61.json',{cache:'no-store'}).then(open).then(v41)"
    new=("return fetch('data/nl2_hu_multiboard_status_v42_b289_rank46.json',{cache:'no-store'}).then(open).then(v42)\n"
         "   .catch(()=>fetch('data/nl2_hu_multiboard_status_v41_b271_rank61.json',{cache:'no-store'}).then(open).then(v41))")
    validator="""const v42=d=>{
 const z=d.B289_rank46_three_true_GTO_NL2_CO_IP_flops;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V42_B289_RANK46'||
    d.CERT_MULTIBOARD!==155||d.APPROX!==237||d.EST!==0||d.TOTAL!==392||
    d.parent_v41_sha256?.length!==64||
    z?.rank!==46||z?.model_id!=='ln-iso-lmp_t_model-17z0wyl'||
    z?.flops?.join(',')!=='7s7h2d,8s8h3d,9s6h3d'||
    z?.exact_line!=='x b50 c/x'||z?.actor!=='CO_IP'||
    z?.assumed_limped_169class_preflop_not_observed_NL2_private_cards!==true||
    z?.third_B286_original_GTO_strict_combos!==12||
    z?.third_B288_actual_NL2_actor_SPR_strict_combos!==12||
    z?.genuine_GTO_runs?.['7s7h2d']!==44939456600||
    z?.genuine_GTO_runs?.['8s8h3d']!==44666294821||
    z?.genuine_GTO_runs?.['9s6h3d']!==44666294821||
    z?.real_NL2_actor_lock_runs?.['9s6h3d']!==44882669727||
    z?.real_NL2_actor_lock_runs?.['8s8h3d']!==44666294821||
    z?.real_NL2_actor_lock_runs?.['7s7h2d']!==44947726457||
    z?.GTO_and_NL2_source_shas?.length!==3||
    z?.GTO_and_NL2_source_shas?.some(p=>
       !['7s7h2d','8s8h3d','9s6h3d'].includes(p.flop)||
       p.GTO_case_sha?.length!==64||p.NL2_raw_case_sha?.length!==64||
       p.strict_GTO_actor_combos<=0)!==false||
    d.records?.['ln-iso-lmp_t_model-17z0wyl']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_t_model-17z0wyl']?.proven_exact_board_count!==3||
    d.records?.['ln-ipfr-t_model-qpx6tn']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
     throw Error('V42 rank46 exact original 3 GTO plus actual CO-IP NL2 Rust SHA evidence gate failed');
 return d;
};
 """
    specific=""" if(chosenModel?.model_id==='ln-iso-lmp_t_model-17z0wyl'&&
    chosenBoard?.actual_exact_action_line==='x b50 c/x'&&
    sourceSha(source)?.length===64){
    const v=status?.B289_rank46_three_true_GTO_NL2_CO_IP_flops?.
       GTO_and_NL2_source_shas?.find(x=>
         x.flop===chosenBoard?.flop&&x.turn===chosenBoard?.turn);
    if(v&&((version==='gto'&&run===v.GTO_run)||
          (version!=='gto'&&run===v.NL2_run))){
      setMessage(version==='gto'
        ?'此精確公牌為原生 100bb Rust GTO，CO-IP 座位與 x b50 c/x 前街完整可達性經 SHA 驗證；LMP 169 類翻前範圍是假設，非實際逐私牌 NL2 觀測。'
        :'此公牌為真正 Rust NL2 部分轉河牌鎖頻證據，玩家池實測只限街別與下注尺寸邊際；未知來源分母不等於零或逐私牌實測。');
      const l=document.createElement('a');
      l.href=sourceUrl(run);l.rel='noopener';l.target='_blank';
      l.textContent='檢視精確公牌的 GTO 或 NL2 原生 Rust Actions Run '+run;
      el('details').appendChild(l);el('combo-rows').replaceChildren();return;
    }
 }
 """
    anchor="const v41=d=>{"
    source_guard=" if(chosenBoard.source_kind?.includes('OFFICIAL')&&!hasVerifiedBatch){"
    for filename in ('nl2-multiboard.js','nl2_hu_multiboard_ui.js'):
        f=ROOT/filename
        s=f.read_text()
        assert s.count(anchor)==1 and s.count(old)==1,filename
        assert 'const v42=d=>{' not in s
        s=s.replace(anchor,validator+anchor).replace(old,new)
        if filename=='nl2-multiboard.js':
            assert s.count(source_guard)==1
            s=s.replace(source_guard,specific+source_guard)
        f.write_text(s)
    print('PASS V42 155/237 exact GTO and authentic Rust COIP partial source guarded, immutable V41-V26 fallbacks')
if __name__=='__main__':main()
