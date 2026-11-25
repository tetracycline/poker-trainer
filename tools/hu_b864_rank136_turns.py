"""B864: one new chance turn per authenticated B863 root; no original flop re-solve."""
import argparse,json,sys
from pathlib import Path
import hu_b792_rank136_chance_turns as old
from hu_b864_originals import authenticated,PINS
from hu_b467_river_source_gate import sha,json_bytes

def main(a):
    p=PINS[1];raw,files,receipts=authenticated(p)
    report=json.loads(files['report.json'])
    assert report['rank']==136 and report['native_solves']==report['cert_promotions']==0
    f,=[f for f in report['flops'] if f['flop']==a.flop]
    assert len(f['rows'])==39 and f['artifact']==a.original_id and len(f['excluded_original_turns'])==10
    assert sha(a.archive.read_bytes())==f['origin']['artifact_sha256']
    eligible=[r for r in f['rows'] if r['river_boundary_witnesses']]
    assert len(eligible)=={'Ac7h3d':21,'Ah7d4c':21,'As6c3h':18}[a.flop]
    # Frozen deterministic order: maximum sum of legal hero witnesses, then deck order.
    choice=min(eligible,key=lambda r:(-sum(len(v) for v in r['river_boundary_witnesses'].values()),old.DECK.index(r['turn'])))
    t=choice['turn'];assert t not in f['excluded_original_turns']
    assert a.flop not in old.TURNS
    old.TURNS[a.flop]=(t,)
    plan=dict(schema='NL2_B864_NEW_R136_TURN_PLAN_V1',source_screen_artifact=p['artifact'],screen_zip_sha256=p['digest'],flop=a.flop,turn=t,choice=choice,original_artifact=a.original_id,original_root_sha256=f['origin']['original_root_sha256'])
    print(json.dumps(dict(flop=a.flop,selected_new_turn=t,river_boundary_leads=len(choice['river_boundary_witnesses']))),flush=True)
    old.run(a)
    if not a.preflight:
        proof=json.loads((a.output/'proof.json').read_bytes())
        assert len(proof['turns'])==1 and proof['turns'][0]['turn']==t
        assert proof['turns'][0]['seat_weight_sha256']==choice['seat_weight_sha256']
        assert set(proof['turns'][0]['river_gate'])<=set(choice['river_boundary_witnesses'])
        assert proof['original_flop_solves_repeated']==0
        path=a.output/'b864-plan.json';content=json_bytes(plan)
        if a.driver:path.write_bytes(content)
        else:assert path.read_bytes()==content
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('archive','solver','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--flop',choices=('Ac7h3d','Ah7d4c','As6c3h'),required=True)
    p.add_argument('--original-id',type=int,required=True)
    p.add_argument('--driver',type=Path);p.add_argument('--preflight',action='store_true')
    main(p.parse_args())
