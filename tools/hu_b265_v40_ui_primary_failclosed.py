#!/usr/bin/env python3
"""B265 V40 frontend: exact board rank313 source-frozen UI primary,
V39-V26 preserved fallback; NL2 partial Rust never presented as baseline GTO.
Run only after full 100bb GTO SHA + actor-matched NL2 source cert succeeds.
"""
from pathlib import Path
import json,hashlib

ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/'data/nl2_hu_multiboard_status_v40_b265_rank313.json'
PARENT=ROOT/'data/nl2_hu_multiboard_status_v39_b247_rank30.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert STATUS.is_file() and PARENT.is_file()
    d=json.loads(STATUS.read_text())
    assert (d['CERT_MULTIBOARD'],d['APPROX'],d['EST'],d['TOTAL'])==(153,239,0,392)
    assert d['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313'
    assert d['parent_v39_sha256']==sha(PARENT)
    mid='ln-iso-lmp_r_model-wpg493'
    assert d['records'][mid]['label']=='CERT-MULTIBOARD'
    assert d['records'][mid]['proven_exact_board_count']==3
    exact=d['B265_rank313_three_true_GTO_NL2_IP_flops']
    assert exact['flops']==['6s5h3d','9s6h3d','KsQh4d']
    assert (exact['rank'],exact['model_id'],exact['actor'],exact['exact_line'])==(
       313,mid,'CO_IP','b75 r c/x b50 c/x')
    assert exact['original_GTO_runs']['6s5h3d']==44901784001
    assert exact['genuine_B263_real_NL2_IP_lock_run']==44903333583
    assert exact['no_observed_NL2_private_card_conditionals'] is True
    assert d['no_generic_texture_GTO'] and d['no_observed_private_card_NL2_rates']
    assert d['PR2_remains_draft_never_merge']
    old="return fetch('data/nl2_hu_multiboard_status_v39_b247_rank30.json',{cache:'no-store'}).then(open).then(v39)"
    new=("return fetch('data/nl2_hu_multiboard_status_v40_b265_rank313.json',{cache:'no-store'}).then(open).then(v40)\n"
         "   .catch(()=>fetch('data/nl2_hu_multiboard_status_v39_b247_rank30.json',{cache:'no-store'}).then(open).then(v39))")
    verifier="""const v40=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313'||
    d.CERT_MULTIBOARD!==153||d.APPROX!==239||d.EST!==0||d.TOTAL!==392||
    d.parent_v39_sha256?.length!==64||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.rank!==313||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.model_id!=='ln-iso-lmp_r_model-wpg493'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.flops?.join(',')!=='6s5h3d,9s6h3d,KsQh4d'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.exact_line!=='b75 r c/x b50 c/x'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.actor!=='CO_IP'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.['9s6h3d']!==44666294821||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.KsQh4d!==44666294821||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.['6s5h3d']!==44901784001||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.genuine_B263_real_NL2_IP_lock_run!==44903333583||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.B263_strict_CO_IP_river_combos!==73||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.LMP_explicit_169class_preflop_ASSUMED_not_observed_NL2_hand!==true||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.no_observed_NL2_private_card_conditionals!==true||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.proven_exact_board_count!==3||
    d.records?.['ln-opfr-t_model-1hmsxaw']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
    throw Error('V40 exact original three named GTO and true CO-IP NL2 Rust SHA gate failed');
 return d;
};
 """
    source_anchor="const v39=d=>{"
    guard_anchor=" if(chosenBoard.source_kind?.includes('OFFICIAL')&&!hasVerifiedBatch){"
    safe=""" if(chosenModel?.model_id==='ln-iso-lmp_r_model-wpg493'&&
    chosenBoard?.flop==='6s5h3d'&&chosenBoard?.turn==='Qs'&&
    chosenBoard?.actual_exact_action_line==='b75 r c/x b50 c/x'&&
    ((version==='gto'&&run===44901784001)||
     (version!=='gto'&&run===44903333583))&&
    sourceSha(source)?.length===64){
   setMessage(version==='gto'
     ?'此具名牌面原始 100bb Rust GTO 已經來源 SHA/座位/前街合法 combo 驗證；其 LMP 169 類翻前範圍是假設，非觀測到的私有手牌。原始證據詳見 GitHub Actions；不將 EXP source 當 GTO。'
     :'此具名牌面是真實 Rust NL2 部分 node-lock（限後續轉河牌），觀測的 NL2 來源僅為街別/下注尺寸玩家池聚合；未知及預設頻率未視為實測逐私牌條件。');
   const link=document.createElement('a');
   link.href=sourceUrl(run);link.target='_blank';link.rel='noopener';
   link.textContent='檢視本具名公牌的真實 GTO／NL2 source GitHub Actions Run '+run;
   el('details').appendChild(link);
   el('combo-rows').replaceChildren();return;
 }
 """
    for filename in ('nl2-multiboard.js','nl2_hu_multiboard_ui.js'):
        file=ROOT/filename
        s=file.read_text()
        assert s.count(source_anchor)==1 and s.count(old)==1
        assert "const v40=d=>{" not in s
        assert "v39_b247_rank30.json" in s
        s=s.replace(source_anchor,verifier+source_anchor).replace(old,new)
        if filename=='nl2-multiboard.js':
            assert s.count(guard_anchor)==1
            s=s.replace(guard_anchor,safe+guard_anchor)
        file.write_text(s)
    print('PASS B265 source-guarded V40 two frontends, V39-V26 exact fallbacks retained, no EXP misrepresented as GTO')
if __name__=='__main__':main()
