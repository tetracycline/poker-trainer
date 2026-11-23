"""Verify published rank8 witnesses against original native joint reach and the actual rendered street rows."""
import base64
import gzip
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b467_river_source_gate import EVIDENCE, sha
from hu_b483_locked_medium import proof
from hu_b536_sb_barrels import tx
from hu_sequential_cfr_reach import cardkey, game_reach

sys.path.insert(0,str(Path(__file__).resolve().parent/'lines_pipeline'))
from run10_common import hcls


def original(pin,version,identity,expected_sha):
    flop,turn=pin['flop'],pin['turn']
    path=EVIDENCE/f'NL2_B524_R8_{flop.upper()}_{version.upper()}.zip'
    assert sha(path.read_bytes())==identity['artifact_sha256'] and identity['source_sha256']==expected_sha
    with ZipFile(path) as archive:
        base=f'solver/postflop/out/BTN_BB/{version}/{flop}'
        root=archive.read(base+'_multiboard.json')
        sub=archive.read(base+'_b50c_'+turn+'.json')
    assert sha(root)==identity['root_sha256'] and sha(sub)==expected_sha
    return json.loads(root),json.loads(sub)


def masks(root,sub,public):
    assert (root['pot'],root['stack'],sub['pot'],sub['stack'])==(550,9750,1100,9475)
    parent,=(n for n in root['nodes'] if n['line']=='b50 c/' and n['board']==public)
    assert parent['bets']==[275,275] and parent['pot']==1100
    target,=(n for n in sub['nodes'] if n['line']=='b50 c/x' and n['board']==public)
    assert target['player']==1 and target['bets']==[0,0] and target['pot']==1100
    proof_row=proof(root,sub,target,game_reach(root,sub)[0])
    mask=base64.b64decode(proof_row['compatible_action_mask_b64'],validate=True)
    assert proof_row['compatible_hole_card_pairs']>0
    return {''.join(cardkey(h)):{a for i,a in enumerate(target['acts']) if bits&(1<<i)}
            for h,bits in zip(sub['hands'][1],mask,strict=True) if bits}


def main():
    route=json.loads(subprocess.check_output(['node','tools/hu_b549_rank8_current_rows.cjs']))
    group=json.loads((EVIDENCE/'reverified/rank8.json').read_bytes())
    assert group['rank']==8 and len(group['boards'])==len(group['pins'])==3
    for pin in group['pins']:
        flop,public=pin['flop'],pin['public_board']
        root,sub=original(pin,'gto',pin['original_gto_archive'],pin['original_GTO_SHA256'])
        if 'original_locked_archive' in pin:
            lockroot,locksub=original(pin,'exp_ip',pin['original_locked_archive'],pin['actual_NL2_SHA256'])
        else:
            archive=EVIDENCE/f"NL2_{pin['locked_original_archive_code']}.json.gz"
            assert sha(archive.read_bytes())==pin['locked_original_archive_sha256']
            raw=json.loads(gzip.decompress(archive.read_bytes()))
            assert raw['original']==pin['original_gto_archive'] and raw['version']=='exp_ip' and raw['run']==pin['locked_source_run_id']
            src=base64.b64decode(raw['source_file_b64'],validate=True)
            assert sha(src)==raw['source_sha256']==pin['actual_NL2_SHA256']
            lockroot,locksub=root,json.loads(src)
            locksub.update(line0='b50 c',turn=pin['turn'])
        g,e=masks(root,sub,public),masks(lockroot,locksub,public)
        flop_row,turn_row=tx(public[:6]),tx(public)
        witnesses=pin['shared_rendered_action_hands']
        assert witnesses and len({w['hand'] for w in witnesses})==len(witnesses)
        for w in witnesses:
            hand=w['hand']
            first,last=hcls(hand,public[:6]),hcls(hand,public)
            assert (w['flop_class'],w['turn_class'])==(first,last) and first in route[flop_row]['flop']
            assert w['turn_action']==route[turn_row]['turn'][last] and w['turn_action'] in (g[hand]&e[hand])
        print(f"{flop}/{pin['turn']} {flop_row}/{turn_row} {len(witnesses)} verified shared rendered actions")


if __name__=='__main__':
    main()
