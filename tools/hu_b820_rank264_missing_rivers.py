"""B820: preflight genuinely unexported rank264 rivers from B722 originals.
No native calls; no certification from static or reach-only evidence."""
import json,subprocess,argparse
from pathlib import Path
from zipfile import ZipFile
from hu_b467_river_source_gate import sha,json_bytes
from hu_b722_rank264 import parent
from hu_b677_rank264_checks import DECK
from hu_b568_caller_rivers import hand_cell
from hu_sequential_cfr_reach import accepted,cardkey
from hu_b711_bb_lead_rivers import cards
def run(output):
    evidence=Path('data/solver_evidence')
    summary=json.loads(Path('data/nl2_hu_b726_summary.json').read_bytes())
    route=json.loads(subprocess.check_output(['node','tools/hu_b677_rank264_routes.cjs']))
    assert all(route[k]=={'low:2':'過','mid_high:2':'過'} for k in ('flop','turn','river'))
    reports=[]
    for w in summary['workers']:
        archive=evidence/w['archive']
        assert sha(archive.read_bytes())==w['archive_sha256']
        with ZipFile(archive) as z:
            assert sha(z.read('proof.json'))==w['original_proof_sha256']
            claim=json.loads(z.read('proof.json'))
            assert claim['flop']==w['flop'] and claim['rank']==264
            root=json.loads(z.read('flop/result.json'))
            assert sha(z.read('flop/result.json'))==w['root_origin']['root_result_sha256']
            assert (root['flop'],root['pot'],root['stack'])==(w['flop'],2050,9000)
            for tr in w['turns']:
                if not tr['actor_locked']:continue
                t=tr['turn'];old=next(v for v in claim['turns'] if v['turn']==t)
                public=parent(root,t)['board'];boundary=parent(root,t)
                rootnodes={n['line']:n for n in root['nodes'] if len(n['board'])==6}
                live=[]
                for i,k in enumerate(('','x')):
                    n=rootnodes[k]
                    assert (n['player'],n['pot'],n['bets'])==(i,2050,[0,0])
                    live.append(accepted(n,root['hands'],'x')&{cardkey(h) for h,v in zip(root['hands'][i],boundary['wr'][i],strict=True) if v>1e-4 and cards(public).isdisjoint(cardkey(h))})
                original_picks=set(old['parent_gate']['preregistered_rivers'])
                policy={}
                for mode,label in (('gto','gto'),('exp_oop','nl2')):
                    path=t+'-'+mode+'/'
                    jb=z.read(path+'job.json');rb=z.read(path+'result.json')
                    assert sha(jb)==tr[label+'_job_sha256'] and sha(rb)==tr[label+'_result_sha256']
                    job=json.loads(jb);game=json.loads(rb)
                    assert (game['flop'],game['pot'],game['stack'])==(w['flop'],2050,9000)
                    nodes={n['line']:n for n in game['nodes'] if len(n['board'])==8}
                    for i,(line,key) in enumerate((('x x/','oop_w'),('x x/x','ip_w'))):
                        n=nodes[line]
                        assert (n['player'],n['board'])==(i,public)
                        live[i]&=accepted(n,game['hands'],'x')&{cardkey(h) for h,v in job[key] if v>1e-4}
                    policy[mode]=dict(job_sha256=sha(jb),result_sha256=sha(rb))
                hero=[h for h in sorted(live[0]) if hand_cell(''.join(h),public[:6])[0] in route['flop'] and hand_cell(''.join(h),public)[0] in route['turn']]
                missing={}
                for river in DECK:
                    if river in cards(public) or river in original_picks:continue
                    pairs=[[''.join(h),''.join(v)] for h in hero if river not in h and hand_cell(''.join(h),public+river)[0] in route['river'] for v in sorted(live[1]) if river not in v and set(h).isdisjoint(v)]
                    if pairs:missing[river]=dict(pair_count=len(pairs),example=pairs[0])
                reports.append(dict(flop=w['flop'],turn=t,archive=w['archive'],archive_sha256=w['archive_sha256'],policy=policy,common_turn_seats=list(map(len,live)),common_rendered_hero=len(hero),old_rivers=sorted(original_picks),new_rivers=missing))
    assert len(reports)==2
    result=dict(rank=264,original_flop_solves=0,conditional_solves=0,checked_turns=reports,eligible_turns=sum(bool(r['new_rivers']) for r in reports),not_a_certificate=True)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(json_bytes(result));print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
