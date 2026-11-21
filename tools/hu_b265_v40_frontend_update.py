#!/usr/bin/env python3
"""B265 V40 only after authoritative 3 authentic exact-board GTO+NL2 source
file was independently generated. Keep original v39-v26 source guards
as fallbacks, never treat generic hand-class bucket as fully solved GTO.
"""
import pathlib,json,hashlib
D=pathlib.Path('data')
STATUS=D/'nl2_hu_multiboard_status_v40_b265_rank313.json'
def main():
 assert STATUS.is_file()
 d=json.loads(STATUS.read_text())
 assert d['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313'
 assert (d['CERT_MULTIBOARD'],d['APPROX'],d['EST'],d['TOTAL'])==(153,239,0,392)
 assert d['parent_v39_sha256']==hashlib.sha256(
  (D/'nl2_hu_multiboard_status_v39_b247_rank30.json').read_bytes()).hexdigest()
 model=d['records']['ln-iso-lmp_r_model-wpg493']
 assert model['label']=='CERT-MULTIBOARD' and model['proven_exact_board_count']==3
 assert {z['flop'] for z in model['certified_3_to_5_exact_flop_boards']}=={
   '6s5h3d','9s6h3d','KsQh4d'}
 verifier="""const v40=d=>{
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V40_B265_RANK313'||
    d.CERT_MULTIBOARD!==153||d.APPROX!==239||d.EST!==0||d.TOTAL!==392||
    d.parent_v39_sha256?.length!==64||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.rank!==313||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.model_id!=='ln-iso-lmp_r_model-wpg493'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.flops?.join(',')!=='6s5h3d,9s6h3d,KsQh4d'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.exact_line!=='b75 r c/x b50 c/x'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.actor!=='CO_IP'||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.['6s5h3d']!==44901784001||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.['9s6h3d']!==44666294821||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.original_GTO_runs?.KsQh4d!==44666294821||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.genuine_B263_real_NL2_IP_lock_run!==44903333583||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.B263_strict_CO_IP_river_combos!==73||
    d.B265_rank313_three_true_GTO_NL2_IP_flops?.LMP_explicit_169class_preflop_ASSUMED_not_observed_NL2_hand!==true||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-wpg493']?.proven_exact_board_count!==3||
    d.records?.['ln-opfr-t_model-1hmsxaw']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipc-r_model-dfikbd']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||
    d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||
    Object.keys(d.records||{}).length!==392)
   throw Error('V40 rank313 3 original LMP GTO plus actor matched NL2 CO-IP SHA gate failed');
 return d;
};
"""
 old="return fetch('data/nl2_hu_multiboard_status_v39_b247_rank30.json',{cache:'no-store'}).then(open).then(v39)"
 new=("return fetch('data/nl2_hu_multiboard_status_v40_b265_rank313.json',{cache:'no-store'}).then(open).then(v40)\n"
      "   .catch(()=>fetch('data/nl2_hu_multiboard_status_v39_b247_rank30.json',{cache:'no-store'}).then(open).then(v39))")
 for name in ('nl2-multiboard.js','nl2_hu_multiboard_ui.js'):
    p=pathlib.Path(name);text=p.read_text()
    assert text.count('const v39=d=>{')==1,name
    assert text.count(old)==1,name
    assert 'const v40=d=>{' not in text
    text=text.replace('const v39=d=>{',verifier+'const v39=d=>{').replace(old,new)
    if name=='nl2-multiboard.js':
      # This source is only a downstream partial NL2 lock; original backend
      # GTO archive is separate and must NEVER be impersonated by an exp source.
      marker=" if(chosenBoard.source_kind?.includes('OFFICIAL')&&!hasVerifiedBatch){"
      assert text.count(marker)==1
      safe=""" if(chosenModel?.model_id==='ln-iso-lmp_r_model-wpg493'&&version!=='gto'&&
    run===44903333583&&sourceSha(source)?.length===64){
    setMessage('此具名牌面只有 SHA 驗證的真實 Rust NL2 CO-IP 轉河牌局部鎖頻，不是整個 LMP 100bb GTO，也不是實測逐私牌條件頻率。');
    const link=document.createElement('a');
    link.href=sourceUrl(run);link.target='_blank';link.rel='noopener';
    link.textContent='查看原始 B263 Rust CO-IP 部分鎖頻 Actions Run '+run;
    el('details').appendChild(link);el('combo-rows').replaceChildren();return;
 }
"""
      text=text.replace(marker,safe+marker)
    p.write_text(text)
 print('PASS B265 V40 primary strict 153/239, original V39-v26 fallbacks, real B263 exp source NOT GTO')
if __name__=='__main__':main()
