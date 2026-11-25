"""B863: read-only chance-boundary screen on three B652 roots not used by B792/B798.
No native execution. Reconstructed weights are only conditional inputs, not decisions.
"""
import json, subprocess, sys
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import hu_b792_rank136_chance_turns as old
from hu_b467_river_source_gate import sha,json_bytes
from hu_b859_limp_boundaries import api
from hu_sequential_cfr_reach import accepted,cardkey

JOBS={'Ac7h3d':138032553547,'Ah7d4c':138032553558,'As6c3h':138032554092}
RUN=45271606730
BRANCH='fix/nl2-hu-lines-audit-20261118'
def get(path):return json.loads(api(path))

def screen(root,t,weights,route):
    f=root['flop'];board=f+t
    nodes={n['line']:n for n in root['nodes'] if len(n['board'])==6}
    assert [nodes[k]['player'] for k in ('','x','x b75')]==[0,1,0]
    assert nodes['']['pot']==550 and 'b75' in nodes['x']['acts'] and 'c' in nodes['x b75']['acts']
    bb=accepted(nodes[''],root['hands'],'x') & accepted(nodes['x b75'],root['hands'],'c')
    btn=accepted(nodes['x'],root['hands'],'b75')
    live=[{cardkey(h) for h,w in zip(root['hands'][s],weights[s],strict=True) if w>1e-4 and old.public_cards(board).isdisjoint(cardkey(h))} for s in (0,1)]
    bb &= live[0];btn &= live[1]
    btn={h for h in btn if old.hand_cell(''.join(h),f)[0] in route['flop'] and old.hand_cell(''.join(h),board)[0] in route['turn']}
    witnesses={}
    for r in old.DECK:
        if r in old.public_cards(board):continue
        hs=sorted(h for h in btn if r not in h and route['river'].get(old.hand_cell(''.join(h),board+r)[0])=='過')
        vs=sorted(v for v in bb if r not in v)
        qualified={}
        for h in hs:
            v=next((v for v in vs if set(v).isdisjoint(h)),None)
            if v is not None:qualified[''.join(h)]=''.join(v)
        if qualified:witnesses[r]=qualified
    return dict(turn=t,seat_weight_sha256=[sha(old.weight_bytes(w)) for w in weights],
        live_bb=len(bb),displayed_btn=len(btn),river_boundary_witnesses=witnesses,
        status='UNSOLVED_BOUNDARY_LEAD' if witnesses else 'NO_DISPLAYED_BOUNDARY_WITNESS')

def main(out,solver):
    out.mkdir(parents=True,exist_ok=False)
    assert subprocess.check_output(['git','-C',solver,'rev-parse','HEAD'],text=True).strip()==old.SOLVER
    for p,d in (('postflop/py/pipeline.py',old.PIPELINE),('postflop/py/ranges.py',old.RANGES),('inputs/pool_stats.json',old.POOL)):
        assert sha((solver/p).read_bytes())==d
    sys.path.insert(0,str(solver/'postflop/py'));import pipeline,ranges
    route_raw=subprocess.check_output(['node',old.ROUTE]);route=json.loads(route_raw)['136']
    assert route==dict(id=old.MODEL,flop=['A_high:0','A_high:3','A_high:4'],turn=['A_high:4'],river={'A_high:4':'過'})
    prior=json.loads(Path(old.SOURCE).read_bytes());assert (prior['run'],prior['head'],prior['positive_flops'])==(RUN,old.SOURCE_HEAD,0)
    b794=json.loads(Path('data/nl2_hu_b794_results.json').read_bytes())
    b800=json.loads(Path('data/solver_evidence/partial/b800_rank136_original_observations.json').read_bytes())
    earlier={w['flop'] for w in b794['workers']}|{w['flop'] for w in b800['observations']}|set(old.TURNS)
    assert set(JOBS).isdisjoint(earlier)
    model=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records'][old.MODEL]
    assert (model['frequency_rank'],model['label'],model['solver_profile'])==(136,'APPROX','BTN_BB')
    assert abs((9337/1376)/model['assumed_model_node_spr']-1)<.05
    priority=json.loads(Path('data/nl2_hu_b838_234_approx_frequency_priority.json').read_bytes())
    p,=[p for p in priority['rows'] if p['rank']==136]
    assert p['passes_min_0_2_pct_frequency'] and p['model_id']==old.MODEL and priority['current_certified_opportunity_share_pct']<90
    run=get(f'actions/runs/{RUN}')
    assert (run['head_sha'],run['head_branch'],run['status'],run['conclusion'])==(old.SOURCE_HEAD,BRANCH,'completed','success')
    result=[]
    for f,jid in JOBS.items():
        pin,=[p for p in prior['observations'] if p['flop']==f];aid=pin['artifact_id']
        job=get(f'actions/jobs/{jid}');meta=get(f'actions/artifacts/{aid}')
        assert (job['run_id'],job['name'],job['status'],job['conclusion'])==(RUN,f'solve ({f})','completed','success')
        assert (meta['id'],meta['name'],meta['digest'],meta['expired'])==(aid,f'B652-R136-{f}','sha256:'+pin['artifact_sha256'],False)
        assert (meta['workflow_run']['id'],meta['workflow_run']['head_sha'])==(RUN,old.SOURCE_HEAD)
        raw=api(f'actions/artifacts/{aid}/zip');assert sha(raw)==pin['artifact_sha256'] and len(raw)==meta['size_in_bytes']
        archive=out/f'{aid}.zip';archive.write_bytes(raw)
        with ZipFile(BytesIO(raw)) as z,ZipFile(BytesIO(z.read('source.zip'))) as inner:
            assert z.testzip() is None and inner.testzip() is None
            rr=inner.read('root.json');assert sha(rr)==pin['original_root_sha256']
            root=json.loads(rr);proof=json.loads(inner.read('proof.json'))
        observed={n['board'][6:] for n in root['nodes'] if n['line']==old.CHILD}
        previous={r['turn'] for r in proof['turns']}
        # Exclude all exported original boundaries, not just the solved subset.
        assert previous<=observed and len(observed)==10
        turns=tuple(t for t in old.DECK if t not in old.public_cards(f) and t not in observed)
        assert len(turns)==39
        old.TURNS[f]=turns
        try:root,weights,origin=old.original(archive,f,pipeline,ranges)
        finally:del old.TURNS[f]
        rows=[screen(root,t,weights[t],route) for t in turns]
        result.append(dict(flop=f,job=jid,artifact=aid,origin=origin,excluded_original_turns=sorted(observed),rows=rows))
        (out/f'{aid}-receipts.json').write_bytes(json_bytes(dict(run=run,job=job,artifact=meta)))
        archive.unlink()
    report=dict(schema='NL2_B863_R136_UNSEEN_CHANCE_BOUNDARY_SCREEN_V1',rank=136,model=old.MODEL,
        scope='Reconstructed original GTO chance weights only, no actual new turn or river decision, no NL2 joint reach.',
        flops=result,route_sha256=sha(route_raw),native_solves=0,cert_promotions=0,locked_public_boards=0,
        joint_halfpot_assessed=0,nonpolarized_candidates=0,actual_model_opportunity_coverage_pct=priority['current_certified_opportunity_share_pct'])
    (out/'report.json').write_bytes(json_bytes(report));(out/'rendered-routes.json').write_bytes(route_raw)
    print(json.dumps(dict(flops=len(result),unseen_boundaries=sum(len(f['rows']) for f in result),
        leads={f['flop']:sum(bool(x['river_boundary_witnesses']) for x in f['rows']) for f in result},native_solves=0,cert_promotions=0)))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
