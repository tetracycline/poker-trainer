#!/usr/bin/env python3
"""Validate, compress, and cross-reference source-certified NL2 HU CFR cases.

A generic six-texture MODEL is not an exact-board GTO certificate.
All inferred references here are educational source candidates, not promotions.
"""
import argparse, collections, gzip, hashlib, json, pathlib

def checksum(data):
    return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=pathlib.Path,default=pathlib.Path('data/nl2_hu_exact_boards.json'))
    p.add_argument('--queue',type=pathlib.Path,default=pathlib.Path('data/nl2_hu_stage2_queue.json'))
    p.add_argument('--prefix',type=pathlib.Path,default=pathlib.Path('data/nl2_hu_exact_boards'))
    a=p.parse_args()
    bs=a.source.read_bytes()
    obj=json.loads(bs)
    queue=json.loads(a.queue.read_text())
    assert obj['schema']=='HU_NL2_EXACT_BOARD_CFR_V1'
    assert obj['exact_subgame_count']==len(obj['subgames'])==347
    assert obj['generic_model_upgrades']==0
    assert len(queue['records'])==392
    status=collections.Counter()
    family=collections.Counter()
    versions=collections.Counter()
    spots=collections.Counter()
    nodes=near=b50=b50_npolar=0
    pool_cases=pool_matched=pool_total=0
    preview=[]
    spotrefs={}
    seen=set()
    for c in obj['subgames']:
        key=(c['spot'],c['version'],c['source_sha256'])
        assert key not in seen
        seen.add(key)
        assert c['status'] in ('CERT_EXACT_BOARD_GTO','EXPERIMENTAL_POOL_LOCKED')
        status[c['status']]+=1;family[c['pot_family']]+=1
        versions[c['version']]+=1;spots[c['spot']]+=1
        assert c['source_run_id'] in obj['run_ids']
        assert len(c['source_sha256'])==64
        if c['status']=='EXPERIMENTAL_POOL_LOCKED':
            lock=c.get('nl2_pool_lock_coverage') or {}
            pool_cases+=1
            pool_matched+=lock.get('matched_nodes',0)
            pool_total+=lock.get('villain_nodes',0)
        for n in c['nodes']:
            nodes+=1;near+=n['near_mixed_combos']
            b50+=n['medium_50pct_eligible_combos']
            if (n.get('b50_relative_equity_mix') or {}).get('nonpolarized_medium_bet_candidate'):
                b50_npolar+=1
        spotrefs.setdefault((c['spot'],c['pot_family']),[])
        if c['version']=='gto' and len(spotrefs[c['spot'],c['pot_family']])<5:
            spotrefs[c['spot'],c['pot_family']].append(dict(
                source_run_id=c['source_run_id'],spot=c['spot'],flop=c['flop'],
                turn=c['turn'],flop_line=c['flop_line'],turn_spr=c['turn_spr'],
                source_sha256=c['source_sha256'],
                reference_status='CERT_EXACT_BOARD_GTO_ONLY'))
    refs={}
    for m in queue['records']:
        if m['status']!='MODEL_UNCERTIFIED' or m['exact_turn_board'] is not None:
            raise ValueError('Generic MODEL was silently promoted: '+m['model_id'])
        possible=spotrefs.get((m['solver_profile'],m['family']),[])
        # Only a SOURCE PROFILE link is claimed. A source's exact board, line
        # or SPR is NOT asserted compatible with the generic model history.
        refs[m['model_id']]=dict(model_id=m['model_id'],spot=m['spot'],
            family=m['family'],solver_profile=m['solver_profile'],
            model_root_spr=m['root_spr'],model_node_spr=m['approx_spr'],
            reference_count=len(possible),
            references=possible,
            status='REFERENCE_ONLY_NOT_CERTIFIED',
            blockers=['MODEL_HAS_NO_EXACT_FLOP_TURN_RIVER',
                'MODEL_ACTION_AND_POT_HISTORY_NOT_MATCHED_TO_SOLVER',
                'MODEL_COMBO_REACH_NOT_DERIVED_FROM_EXACT_BOARD'])
    assert len(refs)==392
    gz=a.prefix.with_name('nl2_hu_exact_boards.json.gz')
    gz.write_bytes(gzip.compress(bs,compresslevel=9,mtime=0))
    assert gzip.decompress(gz.read_bytes())==bs
    summary={
        'schema':'NL2_HU_CFR_V1_VALIDATED_SOURCE_INDEX',
        'source_run_ids':obj['run_ids'],
        'raw_data_sha256':checksum(bs),
        'gzip_sha256':checksum(gz.read_bytes()),
        'gzip_file':gz.name,
        'raw_bytes':len(bs),'gz_bytes':gz.stat().st_size,
        'genuine_exact_board_subgames':len(obj['subgames']),
        'gto_cert_exact_board_subgames':status['CERT_EXACT_BOARD_GTO'],
        'nl2_pool_locked_provisional_subgames':status['EXPERIMENTAL_POOL_LOCKED'],
        'total_decision_nodes':nodes,'near_mixed_combo_nodes':near,
        'b50_eligible_combo_nodes':b50,
        'nonpolarized_50pct_exact_board_candidate_nodes':b50_npolar,
        'aggregate_lock_covered_nodes':pool_matched,
        'aggregate_lock_eligible_villain_nodes':pool_total,
        'aggregate_lock_sample_coverage_pct':round(100*pool_matched/pool_total,3) if pool_total else None,
        'models_in_original_website':len(refs),
        'models_certified_by_this_file':0,
        'statuses':dict(status),'by_pot_family':dict(family),'by_version':dict(versions),'by_spot':dict(spots),
        'provenance_files':obj['provenance_files'],
        'warning':'GTO CERT only for specified board/action/SPR combos; no generic MODEL has been promoted. NL2 opponent observations are aggregate node frequencies, not observed per-combo assignments.'
    }
    a.prefix.with_name('nl2_hu_exact_boards_index.json').write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    a.prefix.with_name('nl2_hu_model_source_references.json').write_text(
        json.dumps({'schema':'NL2_HU_MODEL_SOURCE_REFERENCES_V1',
                    'generic_certificates':0,'generic_models':392,'items':refs},
                   ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('by_spot','statuses')},ensure_ascii=False))
if __name__=='__main__':main()
