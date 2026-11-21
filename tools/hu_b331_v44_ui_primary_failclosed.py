#!/usr/bin/env python3
"""Activate V44 4 exact SHA-gated rank60 public boards ONLY after real B323
GTO plus separate B325 actor NL2 Rust partial lock, 597/689 proof,
full HU2475 audit. Preserve V43 and prior fallbacks, no generic advice.
"""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATUS=ROOT/'data/nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json'
PARENT=ROOT/'data/nl2_hu_multiboard_status_v43_b319_rank60.json'
MID='ln-ipfr-t_model-hxdit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    s=json.loads(STATUS.read_text())
    assert s['schema']=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V44_B331_RANK60_FOUR'
    assert (s['CERT_MULTIBOARD'],s['APPROX'],s['EST'],s['TOTAL'])==(156,236,0,392)
    assert s['parent_v43_sha256']==sha(PARENT)
    q=s['B331_rank60_four_true_GTO_NL2_actor_lock_boards']
    assert q['model_id']==MID and q['rank']==60 and q['actor']=='CO_IP'
    assert q['exact_line']=='x b50 c/x' and q['model_SPR']==8.614
    assert q['board_count']==4 and q['flops']==['9s7h4d','Js9h4d','Js9h5d','Js9s4s']
    assert {'LOW','JT_HIGH','MONOTONE'}.issubset(q['textures'])
    fourth=q['fourth_original_GTO_and_NL2_source']
    assert (fourth['flop'],fourth['turn'],fourth['original_GTO_run'],fourth['true_partial_Rust_NL2_run'])==(
       '9s7h4d','Ad',44960100932,44960924477)
    assert fourth['strict_GTO_actor_combos']==6 and fourth['strict_real_NL2_actor_combos']==6
    assert fourth['NL2_actor_matching_SPR_combos']==6
    assert len(fourth['original_GTO_case_sha256'])==len(fourth['authentic_real_NL2_source_sha256'])==64
    assert s['records'][MID]['label']=='CERT-MULTIBOARD'
    assert s['records'][MID]['proven_exact_board_count']==4
    assert s['PR2_remains_draft_never_merge'] and s['no_generic_texture_GTO'] and s['no_observed_private_card_NL2_rates']
    validator="""const v44=d=>{
 const q=d.B331_rank60_four_true_GTO_NL2_actor_lock_boards;
 const f=q?.fourth_original_GTO_and_NL2_source;
 if(d.schema!=='NL2_HU_392_MULTIBOARD_CERT_STATUS_V44_B331_RANK60_FOUR'||
    d.CERT_MULTIBOARD!==156||d.APPROX!==236||d.EST!==0||d.TOTAL!==392||
    d.parent_v43_sha256?.length!==64||
    q?.model_id!=='ln-ipfr-t_model-hxdit'||q?.rank!==60||
    q?.actor!=='CO_IP'||q?.exact_line!=='x b50 c/x'||q?.model_SPR!==8.614||
    q?.board_count!==4||q.flops?.length!==4||new Set(q.flops).size!==4||
    !['9s7h4d','Js9h4d','Js9h5d','Js9s4s'].every(p=>q.flops.includes(p))||
    q.textures?.length<3||!['LOW','JT_HIGH','MONOTONE'].every(p=>q.textures.includes(p))||
    f?.flop!=='9s7h4d'||f?.turn!=='Ad'||
    f?.original_GTO_run!==44960100932||f?.true_partial_Rust_NL2_run!==44960924477||
    f?.strict_GTO_actor_combos!==6||f?.strict_real_NL2_actor_combos!==6||
    f?.NL2_actor_matching_SPR_combos!==6||
    f?.original_GTO_case_sha256?.length!==64||f?.authentic_real_NL2_source_sha256?.length!==64||
    d.records?.['ln-ipfr-t_model-hxdit']?.label!=='CERT-MULTIBOARD'||
    d.records?.['ln-ipfr-t_model-hxdit']?.proven_exact_board_count!==4||
    d.records?.['ln-iso-lmp_r_model-vlgh2t']?.label!=='APPROX'||
    d.no_generic_texture_GTO!==true||d.no_observed_private_card_NL2_rates!==true||
    d.PR2_remains_draft_never_merge!==true||Object.keys(d.records||{}).length!==392)
      throw Error('V44 rank60 fourth LOW exact original GTO and true NL2 actor IP SHA source failclosed');
 return d;
};
"""
    oldfetch="return fetch('data/nl2_hu_multiboard_status_v43_b319_rank60.json',{cache:'no-store'}).then(open).then(v43)"
    newfetch=("return fetch('data/nl2_hu_multiboard_status_v44_b331_rank60_four_flops.json',{cache:'no-store'}).then(open).then(v44)\n"
      "   .catch(()=>fetch('data/nl2_hu_multiboard_status_v43_b319_rank60.json',{cache:'no-store'}).then(open).then(v43))")
    oldsource="""const proof=status?.B319_rank60_three_true_GTO_NL2_CO_IP_flops?.
      GTO_and_NL2_source_shas?.find(x=>
        x.flop===chosenBoard?.flop&&x.turn===chosenBoard?.turn);"""
    newsource="""const extra=status?.B331_rank60_four_true_GTO_NL2_actor_lock_boards?.fourth_original_GTO_and_NL2_source;
    const proof=status?.B319_rank60_three_true_GTO_NL2_CO_IP_flops?.
      GTO_and_NL2_source_shas?.find(x=>
        x.flop===chosenBoard?.flop&&x.turn===chosenBoard?.turn)||
       (extra?.flop===chosenBoard?.flop&&extra?.turn===chosenBoard?.turn?
        {GTO_run:extra.original_GTO_run,NL2_run:extra.true_partial_Rust_NL2_run}:null);"""
    for path in ('nl2-multiboard.js','nl2_hu_multiboard_ui.js'):
        file=ROOT/path;raw=file.read_text()
        assert raw.count('const v43=d=>{')==1
        assert raw.count(oldfetch)==1 and 'const v44=d=>{' not in raw
        raw=raw.replace('const v43=d=>{',validator+'const v43=d=>{')
        raw=raw.replace(oldfetch,newfetch)
        if path=='nl2-multiboard.js':
            assert raw.count(oldsource)==1
            raw=raw.replace(oldsource,newsource)
        file.write_text(raw)
    print('PASS V44 156 CERT/236 APPROX 4 named rank60 GTO+real NL2 actor partial locks, 3 textures, V43/V42 failclosed fallback')
if __name__=='__main__':main()
