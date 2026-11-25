"""B874: original indexed source price/actor inventory; never solve or promote.

Separate absent exact source, mismatched chip price, zero indexed sequential
reach, and missing same-actor lock. The old compact index is not a complete
native-source search and cannot prove a generic impossibility.
"""
import json,itertools,math,hashlib,subprocess,sys
from pathlib import Path
from hu_multiboard_promote import build_source_index,hero_seat,tokenize
D=Path('data')
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
    out.mkdir(parents=True,exist_ok=False)
    rp=D/'nl2_hu_multiboard_status_current.json'
    fp=D/'nl2_hu_multiboard_prerank.json'
    pp=D/'nl2_hu_b838_234_approx_frequency_priority.json'
    reg,rank,pri=map(load,(rp,fp,pp))
    nodes={n['model_id']:n for n in rank['nodes']}
    assert len(nodes)==len(reg['records'])==392
    count=sum(x['label']=='CERT-MULTIBOARD' for x in reg['records'].values())
    total=math.fsum(x['estimated_NL2_hand_opportunity_fraction'] for x in nodes.values())
    certified=math.fsum(nodes[k]['estimated_NL2_hand_opportunity_fraction'] for k,v in reg['records'].items() if v['label']=='CERT-MULTIBOARD')
    coverage=round(100*certified/total,6)
    assert (count,reg['APPROX'],coverage)==(158,234,84.700987)
    assert [x['rank'] for x in pri['rows'] if x['passes_min_0_2_pct_frequency']][-3:]==[154,157,158]
    raw=subprocess.check_output(['node','tools/hu_b874_tail_routes.cjs'])
    (out/'routes.json').write_bytes(raw)
    exact,locks,info=build_source_index(D,[Path(p) for p in reg['source_evidence']['source_files']])
    report=[]
    for route in json.loads(raw):
        m=reg['records'][route['id']]; seat=hero_seat(m['preflop_text'])
        assert seat in (0,1) and m['street']==2
        fragments=[tokenize(s) for s in m['abstract_action_history'].split('|')]
        assert len(fragments)==3 and all(fragments)
        lines=sorted({'/'.join(x) for x in itertools.product(*fragments)})
        expected_version='exp_ip' if seat==1 else 'exp_oop'
        found=[]
        for line in lines:
            for g,n,proof,origin in exact.get((m['solver_profile'],m['family'],2,seat,line),()):
                key=(g['spot'],g['family'],g['flop'],g['turn'],g['flop_line'],n['board'],n['line'],seat)
                paired=[l for l in locks.get(key,[]) if l['version']==expected_version]
                root_ok=all(abs(a-b)<=.011 for a,b in zip([g['root_pot_bb'],g['root_remaining_bb']],[route['root']['pot'],route['root']['stack']]))
                price_ok=all(abs(a-b)<=.011 for a,b in zip([n['pot_bb'],n['stack_bb']],[route['pot'],route['stack']]))
                reasons=[]
                if not root_ok:reasons.append('ROOT_PRICE_MISMATCH')
                if not price_ok:reasons.append('NODE_PRICE_MISMATCH')
                if not (g['gto_gap_pct'] is not None and 0<=g['gto_gap_pct']<=.5):reasons.append('CONVERGENCE')
                if not proof or not n['reachable']:reasons.append('ZERO_INDEXED_SEQUENTIAL_REACH')
                if not paired:reasons.append('NO_SAME_ACTOR_LOCK_IN_INDEX')
                found.append(dict(flop=g['flop'],turn=g['turn'],board=n['board'],line=line,actor=seat,
                  run_id=g['run_id'],gto_sha256=g['sha'],root_pot_stack=[g['root_pot_bb'],g['root_remaining_bb']],
                  pot_stack=[n['pot_bb'],n['stack_bb']],indexed_strict_reach=proof,origin=origin,
                  actor_lock_sources=paired,reasons=reasons,raw_replay_required=True))
        found.sort(key=lambda x:(x['flop'],x['turn'],x['board'],x['line'],x['gto_sha256']))
        report.append(dict(rank=route['rank'],id=route['id'],actor=seat,possible_abstract_source_lines=lines,
          exact_actor_line_index_entries=len(found),indexed_candidates_needing_raw_dual_replay=sum(not x['reasons'] for x in found),
          distinct_candidate_flops=sorted({x['flop'] for x in found if not x['reasons']}),sources=found,
          status='APPROX',route_scope='Rendered prices and compact index inventory only. No independent joint combo witness.'))
    payload=dict(schema='NL2_B874_TAIL_RANK_EXACT_PRICE_INDEX_INVENTORY',rank_order=[x['rank'] for x in report],
      registry_sha256=sha(rp),rank_sha256=sha(fp),priority_sha256=sha(pp),route_sha256=hashlib.sha256(raw).hexdigest(),
      CERT=count,APPROX=reg['APPROX'],weighted_model_opportunity_coverage_pct=coverage,native_solves=0,CERT_promotions=0,
      models=report,source_index_summary=info,scope='Only original previously verified compact index; missing index entries are not solver negatives. No private-card NL2 observation or nonpolarization inferred.')
    (out/'report.json').write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({r['rank']:[r['exact_actor_line_index_entries'],r['indexed_candidates_needing_raw_dual_replay']] for r in report}))
if __name__=='__main__':main(Path(sys.argv[1]))
