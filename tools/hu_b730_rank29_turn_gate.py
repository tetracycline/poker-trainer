"""Check every legal turn against the actual BB half-pot range on 18 published rank29-compatible roots."""
import argparse
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile
from hu_b467_river_source_gate import json_bytes, sha
from hu_b582_rank29_reach import rendered
from hu_b703_rank29_highcards import cards, root_gate
from hu_sequential_cfr_reach import accepted, cardkey

PINS = {'NL2_B492_LMP_CO_BB_3S3H2D_7D_GTO.zip': ('1f2347f93c576473108723c8ce76b08c179b5e225ff0b3b75539e5752b9c741e',
                                          'original-flop.json',
                                          'eea1674b4a8454d5f09dad5c5898d2f429b87eefeb49df6c54a4db0527b22a3a'),
 'NL2_B492_LMP_CO_BB_4S4H2D_8S_GTO.zip': ('356d24c42e6a64aeeba51f484ffb9ceded184b95b560f3bc52d51492bfd8d911',
                                          'original-flop.json',
                                          '2a66de4feb627512736616a1a0220883304d49b01c4aefb26cbc6513cfe381be'),
 'NL2_B492_LMP_CO_BB_7S5H3D_6C_GTO.zip': ('069e51390d9fa1407edb741ec7767323f4de4ee90dfcb9deeec65de57ee5d2ae',
                                          'original-flop.json',
                                          '244cd8e9d427ad72d2002637e44a966351477388e165d314cc2d47e744443e19'),
 'NL2_B500_LMP_CO_BB_2C2D4H_4C_GTO.zip': ('5887fdf1eefedc863b39ebe174fc1fd4b24bd97225ebd15dd820b70e91a869a2',
                                          'original-flop.json',
                                          'bf1c5894cdc0dd8b4b38c8814821d91ba0ff64e7d77c47f5661605e3f5079129'),
 'NL2_B500_LMP_CO_BB_3C3D4H_7H_GTO.zip': ('3195be0cb0903fb4f99098dc04611c924746ef52e4ae3fc4fd8caa5bd8f20bb5',
                                          'original-flop.json',
                                          'c69e470baa2b936d81dc831328d7f159b52d3f6242ecb5a22091c61063c6fe36'),
 'NL2_B500_LMP_CO_BB_5C5D2H_KC_GTO.zip': ('5262789c631959bde7be45dc0001866133b06aed464c8645633d1d1eefea4a30',
                                          'original-flop.json',
                                          'cbc617dc307e1d698976188da4d72d6c4afee852a709b4491607979441abf33b'),
 'NL2_B582_R29_6D4S3S.zip': ('17931e3981715c31b28ede1cd255904c246a91738267e492114bc74f3f90c1de',
                             'root.json',
                             'c4bb2e40c462b70506b469fb76e87642db6732d4a0820eb6496b30012ce584d0'),
 'NL2_B582_R29_6H5H3D.zip': ('7e92c30103e7acce5038644357d7c7f863e0ed2ea841d2907970244d80c15483',
                             'root.json',
                             'c0873bc9604e9731e4712dc6be95da70d96d79bfb7bf9d2bc8e1765e496736a0'),
 'NL2_B582_R29_7D5C4C.zip': ('355923115454442a05a8e57fdf4660321809b486446cd9eaf4b7fee3f47e3c8e',
                             'root.json',
                             '10397c77f607170e2f6920989c8c9aa90900f4e20815f606fa923141b7c4a9b0'),
 'NL2_B642_R35_3S3H2D.zip': ('41fc6b90ba38bf1fa8d44fd39499efab7a34e7fb69dd5da2b7c60d23566d4d8b',
                             'root.json',
                             '2353eec8b8d159ecd8ed8421f67ad41a0ab498914da45fd168584dbf5407c3d9'),
 'NL2_B642_R35_4S4H2D.zip': ('7b0569a7e12d6d686536a4cb0a67432e612c13f2479fc8aeb7525f742d281bed',
                             'root.json',
                             'a64a4464720c76ba8f6bf18fa2eb085850b0453ca8080e890acb71b03ab2a110'),
 'NL2_B642_R35_5C5D2H.zip': ('e6b436ff13946666904055412a8cac67f15a744936b0277356e952797afa367c',
                             'root.json',
                             'c0acc83fa9d7965269e786d55aee9539049b366aeee8831175a2e59aeee50675'),
 'NL2_B706_R29_AS7S2D.zip': ('67cbdffafea7609d9fdedb4e4d3804edaa96ed93ab6d2cbc54a6564a66adea8b',
                             'flop/result.json',
                             '9f466f7b2e3a23ad148e6c76c73e6c13f4f615cbb799d364de97b709aaf15e32'),
 'NL2_B706_R29_KD9D4C.zip': ('6b5433a9e86cfb22bf3dd007d02db4b5eeadeaa65edadcae559b4c22c7f1407f',
                             'flop/result.json',
                             'af8043958ef871c0d774083cc9c590e9fde675ce4f972c03025376acc38b0971'),
 'NL2_B706_R29_QH8H3S.zip': ('50f9c74973dc0a57a7da6f6bc33be625a45398fde3179b79478205b471156a4e',
                             'flop/result.json',
                             'cd7d16bc2b21722bbb5f590155e60eb45d78b54096851b9a6a43035e3826cd12'),
 'NL2_B717_R29_5D4D2C.zip': ('84b79096e1422754c031a8a6495e28fca282dfdb7d40d65aea2b09bd215b9f8e',
                             'flop/result.json',
                             '25dadd2b5d10d8c99f6516f98c02c92acc420cc4dabec90a51e69e2ebbc95fa5'),
 'NL2_B717_R29_6C5C4H.zip': ('10dd43864d3728cfc7cf47eddcd3cf30e2d02ba5b36187ee2111c96b4eba13c5',
                             'flop/result.json',
                             '18be48219185a4a010153ec89b08099676d616fa91810a092d0c1459aaeba641'),
 'NL2_B717_R29_8S7S6D.zip': ('90148d38fb50111bb7828ec004b31283a7b4f113c8e62916d05e87571251cce5',
                             'flop/result.json',
                             '13528ff831b538d304de2b53bae8d8f70da336efa0fa6626ee291485e8a9111b')}
TARGET = '6h5h3d'
DECK = [r+s for r in '23456789TJQKA' for s in 'cdhs']


def eligible_turns(root, route):
    flop = root['flop']
    start, = [n for n in root['nodes'] if n['line']=='']
    call, = [n for n in root['nodes'] if n['line']=='b50']
    assert (start['pot'], start['player'],call['pot'],call['player']) == (250,0,375,1)
    bb = accepted(start,root['hands'],'b50')
    ip = accepted(call,root['hands'],'c')
    heroes = {h for h in bb if rendered(''.join(h),flop,'flop',route)}
    turns = {}
    for turn in DECK:
        if turn in cards(flop):continue
        passing = sorted(''.join(h) for h in heroes if turn not in h
                         and rendered(''.join(h),flop+turn,'turn',route)
                         and any(turn not in v and set(h).isdisjoint(v) for v in ip))
        if passing:turns[turn]=passing
    return len(bb), len(heroes), turns


def check_original_turn(archive, root, route, hands):
    parent, legal, _ = root_gate(root,'Th',route)
    assert set(hands)=={h for hs in legal.values() for h in hs}=={'JhTd','QhTd'} and len(legal)==23
    call, = [n for n in root['nodes'] if n['line']=='b50']
    original_call = accepted(call,root['hands'],'c')
    policies = {}
    for kind,name in [('gto','result.json'),('exp_oop','native.json')]:
        raw = archive.read('Th-'+kind+'/'+name);sub=json.loads(raw)
        assert (sub['pot'],sub['stack'])==(500,9775) and 0<=sub['info']['gto_expl_pct']<=.5
        if kind=='gto':assert not sub['info'].get('lock_stats')
        else:assert sub['info']['lock_stats'] and 0<=sub['info']['hero_gap_pct']<=.5
        nodes = {n['line']:n for n in sub['nodes'] if n['board']==parent['board']}
        own = accepted(nodes['b50 c/'],sub['hands'],'b75')
        opponent = accepted(nodes['b50 c/b75'],sub['hands'],'c') & original_call
        assert (nodes['b50 c/']['player'],nodes['b50 c/b75']['player'])==(0,1)
        live = sorted(''.join(h) for h in own if ''.join(h) in hands and any(set(h).isdisjoint(v) for v in opponent))
        assert not live
        exports={n['board'][-2:] for n in sub['nodes'] if n['line']=='b50 c/b75 c/' and n['player']==0}
        assert len(exports)==7 and exports<=set(legal)
        policies[kind]=dict(source_sha256=sha(raw),accepted_b75_hands=len(own),accepted_flop_and_turn_call_hands=len(opponent),
                   original_exported_rivers=sorted(exports),eligible_displayed_hands_after_b75_call=live)
    return dict(public_turn=parent['board'],legal_river_upper_bound=23,previously_exported_rivers=7,unexported_rivers=16,
                upstream_displayed_hands=hands,policies=policies)


def audit():
    route=json.loads(subprocess.check_output(['node','tools/hu_b703_rank29_routes.cjs']))
    assert (route['actor'],route['line'],route['turn'],route['river'])==(0,'b50 c/b75 c/',['mono:0'],{'mono:0':'下注 ¾'})
    rows=[];positive=[]
    for filename,(archive_sha,root_entry,root_sha) in sorted(PINS.items()):
        path=Path('data/solver_evidence')/filename
        assert sha(path.read_bytes())==archive_sha
        with ZipFile(path) as archive:
            raw=archive.read(root_entry);assert sha(raw)==root_sha
            root=json.loads(raw)
            assert (root['pot'],root['stack'])==(250,9900) and not root['info'].get('lock_stats')
            assert 0<=root['info']['gto_expl_pct']<=.5
            lead,displayed,turns=eligible_turns(root,route)
            if turns:
                assert root['flop']==TARGET and list(turns)==['Th']
                positive.append(check_original_turn(archive,root,route,turns['Th']))
            rows.append(dict(archive=filename,archive_sha256=archive_sha,original_flop=root['flop'],native_root_sha256=root_sha,
                bb_accepted_b50=lead,passes_flop_display=displayed,eligible_turns_before_native_turn_action=turns))
    assert len(positive)==1 and len({r['native_root_sha256'] for r in rows})==len(rows)==18
    return dict(schema='NL2_B730_R29_ORIGINAL_TURN_ANCESTRY_V1',rank=29,original_root_policies=len(rows),
        distinct_flop_deals=len({r['original_flop'] for r in rows}),turns_checked_per_root=49,
        root_turn_cases=len(rows)*49,only_static_turn_with_a_compatible_hand=positive[0],roots=rows,
        additional_certified_flops=0,additional_native_solves=0,additional_locked_public_boards=0,additional_halfpot_assessments=0,
        scope='Covers these 18 exact archived GTO flop policies and all legal turns. The existing GTO and NL2 turn actions rule out the remaining 16 rivers on the one surviving turn.')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--out',required=True,type=Path);a=cli.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(json_bytes(audit()))
