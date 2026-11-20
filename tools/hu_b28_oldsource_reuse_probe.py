#!/usr/bin/env python3
"""Read-only inspect of original 44654973894 SB_BB Ks7h2d GTO and
partial NL2 lock artifacts. Determines if an actual pinned GTO flop root,
full path/subgame reach, NL2 lock source counts, and SHA-validated reuse
inputs exist; does NOT infer or reconstruct unobserved opponent frequencies.

No use of 2026 trading data; this task is poker NL2 source provenance.
"""
import gzip,hashlib,json,pathlib
ROOT=pathlib.Path('official_artifacts')
DEST=pathlib.Path('data/nl2_hu_b28_original_Ks7h2d_reuse_probe.json')
REG=pathlib.Path('data/nl2_hu_multiboard_status.json')
SOURCE_RUN=44654973894
FLOP='Ks7h2d'
EXPECTED={
 'gto':'nl2-stage2-SB_BB-gto-Ks7h2d',
 'exp_oop':'nl2-stage2-SB_BB-exp_oop-Ks7h2d'}

def sh(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def inspect_json(path):
    if path.suffix=='.gz':
        if path.stat().st_size>50_000_000:return None
        with gzip.open(path,'rt') as f: d=json.load(f)
    else:
        if path.stat().st_size>55_000_000:return None
        d=json.loads(path.read_text())
    if not isinstance(d,dict):return None
    content=dict(
        keys=list(d)[:35],
        schema=d.get('schema'),
        version=d.get('version'),
        spot=d.get('spot'),
        flop=d.get('flop'),
        source_run_id=d.get('source_run_id'),
        pot=d.get('pot'),
        stack=d.get('stack'),
        actor_hero=d.get('hero'),
        job_has_locks=bool(d.get('locks')),
        job_has_hands=bool(d.get('hands')),
        job_has_nodes=bool(d.get('nodes')),
        node_count=len(d['nodes']) if isinstance(d.get('nodes'),list) else None,
        source_root_action_lines=list(dict.fromkeys(
          x.get('line') for x in d.get('nodes',[]) if isinstance(x,dict) and
          x.get('line','').startswith(('b50 c/','b75 c/','x x/','b33 c/'))
        ))[:30] if isinstance(d.get('nodes'),list) else [],
        case_count=len(d.get('cases',[])) if isinstance(d.get('cases'),list) else None,
        failure_count=len(d.get('failures',[])) if isinstance(d.get('failures'),list) else None,
        rake_rate=d.get('rake_rate'),rake_cap=d.get('rake_cap'))
    if isinstance(d.get('nodes'),list) and isinstance(d.get('hands'),list):
        targets=[x for x in d['nodes'] if isinstance(x,dict) and
                 x.get('line')=='b50 c/' and 'wr' in x]
        content['exact_b50c_parent_weight_nodes']=len(targets)
        content['parent_root_turn_cards']=sorted(set(x.get('board','')[-2:] for x in targets))
        content['pinned_hero_seat_0_b50c_reach_feasible']=bool(targets)
    if isinstance(d.get('info'),dict):
        content['solver_info_keys']=list(d['info'])[:15]
        content['solver_gap_percent']=d['info'].get('gto_expl_pct')
    return content

def main():
    status=json.loads(REG.read_text())
    assert status['TOTAL']==392 and status['CERT_MULTIBOARD']==24
    official=[]
    for model in status['records'].values():
        if model['label']!='CERT-MULTIBOARD':continue
        for b in model['certified_3_to_5_exact_flop_boards']:
            if b['flop']==FLOP and b['source_run_id']==SOURCE_RUN:
                official.append(dict(model_id=model['model_id'],rank=model['frequency_rank'],
                    flop_line=b['actual_exact_action_line'],turn=b['turn'],
                    public_board=b['public_board'],
                    source_sha256=b['source_sha256'],
                    strict_reachable_combos=b['strict_full_street_combo_reachable'],
                    missing_provenance_lock_variants=[
                        dict(run_id=v['run_id'],sha256=v['sha256'],scope=v['source_scope'])
                        for v in b['nl2_locked_variants']
                        if v.get('observed_marginal_source_nodes') is None]))
    if len(official)<3:raise ValueError('Expected multiple rank-verified official Ks7h2d source uses')
    original_shas={x['source_sha256'] for x in official}
    summary={}
    for version,name in EXPECTED.items():
        folder=ROOT/name
        if not folder.is_dir():raise FileNotFoundError('Original GitHub artifact missing '+name)
        files=[p for p in folder.rglob('*') if p.is_file()]
        if not files:raise ValueError('No original immutable artifact files')
        indexed=[];matches=[]
        for path in files:
            relative=path.relative_to(folder).as_posix()
            digest=sh(path)
            sz=path.stat().st_size
            d=dict(relative_path=relative,bytes=sz,sha256=digest,
                official_registered_subgame_SHA_match=digest in original_shas)
            if digest in original_shas:matches.append(relative)
            if path.suffix=='.json' or path.name.endswith('.json.gz'):
                try:d['json_fingerprint']=inspect_json(path)
                except Exception as e:d['parse_issue']=str(e)[:160]
            indexed.append(d)
        summary[version]=dict(original_artifact_name=name,
           original_run=SOURCE_RUN,original_file_count=len(files),
           original_total_bytes=sum(x['bytes'] for x in indexed),
           exact_registered_source_sha_paths=matches,
           files=indexed[:100],
           evidence_is_read_only=True)
    report=dict(schema='TASK_HYBRID_B28_OLD_NL2_LOCK_SOURCE_REUSE_PROBE_V1',
      original_run_id=SOURCE_RUN,flop=FLOP,model_count=392,
      certified_status_unchanged=True,
      precommitted_sha_sources=official,
      original_artifact_audit=summary,
      interpretation='Known old source counts remain UNKNOWN. This is a forensic check for reusing exact GTO parent with new measured NL2 aggregate lock solves, not proof of original private-card conditional villain frequencies.',
      no_new_certification=True,
      no_b50_policy_from_this_probe=True,
      no_merge=True)
    DEST.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'run':SOURCE_RUN,'referenced_cert_rows':len(official),
        'files':{k:v['original_file_count'] for k,v in summary.items()},
        'original_sha_matches':{k:len(v['exact_registered_source_sha_paths'])
                                for k,v in summary.items()},
        'root_candidates':[
          dict(version=k,path=d['relative_path'],fingerprint=d['json_fingerprint'])
          for k,v in summary.items() for d in v['files']
          if isinstance(d.get('json_fingerprint'),dict) and
          d['json_fingerprint'].get('pinned_hero_seat_0_b50c_reach_feasible')]},
        ensure_ascii=False))
if __name__=='__main__':main()
