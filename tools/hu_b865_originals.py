"""B865: archive B864's three completed conditional rank136 native sources; never solve again."""
import json,subprocess,sys
from pathlib import Path
from tempfile import TemporaryDirectory
from hu_b864_originals import authenticated
from hu_b710_publish import unpack_original
from hu_b467_river_source_gate import sha,json_bytes

HEAD='e09907a5dfa55829ab32b3a2693ef9226b3fe5dd'
RUN=45658231550
AUDIT=45658231399
WF='.github/workflows/nl2-hu-b864-rank136-turns.yml'
WORKER='tools/hu_b864_rank136_turns.py'
PINS=[
 ('Ac7h3d','Ts',14866311407,139360636855,15043463579,1213948,'943035041a410e42993e00d293fda9c215fc2597fdbd7cf8091b30875ae7f727',15),
 ('Ah7d4c','Js',14865802214,139360636232,15043187976,1229108,'9ea170ffe95093826d72b00f94ed5cbba912314f6c09b082041a55f31b91da49',11),
 ('As6c3h','Td',14866286699,139360636859,15042124693,1179336,'6471367ad7930fab9b16fe475e693c3045941169c6db716deda026c9f07cbe42',7)]
def main(stage,solver):
    stage=stage.resolve();solver=solver.resolve()
    assert not stage.exists()
    partial=stage/'solver_evidence'/'partial';partial.mkdir(parents=True)
    registry=Path('data/nl2_hu_multiboard_status_current.json')
    before=registry.read_bytes();status=json.loads(before)
    assert (status['CERT_MULTIBOARD'],status['APPROX'],status['TOTAL'])==(158,234,392)
    priority=json.loads(Path('data/nl2_hu_b838_234_approx_frequency_priority.json').read_bytes())
    assert priority['source_status_git_blob_sha']==subprocess.check_output(['git','hash-object',str(registry)],text=True).strip()
    row,=[x for x in priority['rows'] if x['rank']==136]
    assert status['records'][row['model_id']]['label']=='APPROX'
    observations=[]
    for f,t,original,job,aid,size,digest,half in PINS:
        p=dict(run=RUN,audit=AUDIT,head=HEAD,job=job,artifact=aid,size=size,digest=digest,name='B864-R136-'+f,workflow=WF)
        raw,files,receipts=authenticated(p)
        assert receipts['job']['name']==f'solve ({f}, {original})'
        assert all(s['conclusion']=='success' for s in receipts['job']['steps'])
        for path in (WF,WORKER,'tools/hu_b792_rank136_chance_turns.py'):
            assert subprocess.check_output(['git','hash-object',path],text=True).strip()==subprocess.check_output(['git','rev-parse',HEAD+':'+path],text=True).strip()
        with TemporaryDirectory(prefix='b865-') as tmp:
            d=Path(tmp);names=unpack_original(raw,d)
            assert names==set(files)
            expected={'original-b652.zip','rendered-routes.json','proof.json','b864-plan.json'}|{t+'-'+mode+'/'+n for mode in ('gto','exp_ip') for n in ('job.json','result.json')}
            assert names==expected
            hashes={n:sha(files[n]) for n in sorted(names)}
            for seed in ('23','867'):
                import os
                subprocess.run([sys.executable,WORKER,'--solver',str(solver),'--flop',f,'--original-id',str(original),'--archive',str(d/'original-b652.zip'),'--output',str(d)],check=True,env=dict(os.environ,PYTHONHASHSEED=seed))
                assert all(sha((d/n).read_bytes())==v for n,v in hashes.items())
            proof=json.loads(files['proof.json']);plan=json.loads(files['b864-plan.json'])
            assert (proof['rank'],proof['flop'],proof['actor'],proof['line'])==(136,f,1,'x b75 c/x x/x')
            assert proof['model_id']==row['model_id'] and proof['selected'] is None and proof['positive_distinct_flops']==0
            assert proof['original_flop_solves_repeated']==0 and not proof['measured_private_hand_frequencies']
            assert (proof['locked_public_boards'],proof['joint_halfpot_assessed'],proof['halfpot_candidates'])==(16,16,half)
            turn,=proof['turns'];assert turn['turn']==plan['turn']==t and not turn['common']
            assert set(turn['policies'])=={'gto','exp_ip'}
            for mode,policy in turn['policies'].items():
                assert policy['job_sha256']==hashes[t+'-'+mode+'/job.json'] and policy['source_sha256']==hashes[t+'-'+mode+'/result.json']
            assert turn['policies']['exp_ip']['applied_lock'] is not None
            name='NL2_B864_R136_'+f.upper()+'_'+t.upper()+'.zip'
            (partial.parent/name).write_bytes(raw)
            (partial/('b864_r136_'+f+'_receipts.json')).write_bytes(json_bytes(receipts))
            observations.append(dict(flop=f,turn=t,artifact=aid,archive=name,archive_sha256=digest,member_sha256=hashes,proof=proof,plan=plan))
    result=dict(schema='NL2_HU_B865_R136_ORIGINAL_ARCHIVE_V1',source_run=RUN,source_audit=AUDIT,source_head=HEAD,
        positive_distinct_flops=0,cert_promotions=0,original_flop_solves_repeated=0,native_repeated=0,
        locked_public_boards=48,locked_policy_compatible_halfpot_assessed=48,locked_policy_halfpot_research_candidates=33,
        same_two_seat_displayed_action_positive_flops=0,
        scope='48 halfpot assessments are within the partial NL2 locked policy, not cross-policy common displayed-action evidence.',
        unchanged_registry_sha256=sha(before),model_node_opportunity_coverage_pct=priority['current_certified_opportunity_share_pct'])
    (partial/'b865_rank136_observations.json').write_bytes(json_bytes(dict(result=result,observations=observations)))
    (stage/'nl2_hu_b865_results.json').write_bytes(json_bytes(result))
    assert registry.read_bytes()==before
    print(json.dumps(result))
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
