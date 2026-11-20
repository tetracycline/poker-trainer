#!/usr/bin/env python3
"""Combine completed independently verified GitHub Rust CFR multi-board batches.

No new CERT-MULTIBOARD without 3–5 distinct exact boards and a paired
hero-side NL2 lock, validated action/actor/pot/SPR, and strict combo reach.
Missing batch results are never interpreted as completed work.
"""
import argparse, collections, gzip, hashlib, json, pathlib, sys

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
    return h.hexdigest()

def discover(root):
    ready=[];batches={}
    for code in ('B1','B2','B2_PARTIAL','B2_REPAIRED_GTO','B3','B4_MICRO','B5_SBGAPS','B6_REMAIN','B7_RIVER','B8_LOCK','B9_LMP_FAST','B10_RIVER_EXP','B11_RIVER_FAST','B12_LOCK_FAST','B13_LMP_B50','B14_FOCUS_EXP','B15_GTO_PARENT_EXP','B16_GTO_PARENT_TWO','B17_RIVER_PINNED','B18_RIVERPAIR','B19_LMP50_RESTRICTED','B20_B66_GTO','B22_B66_EXP','B23_LMP_NEXT','B25_LMP_TEXTURES','B26_LMP_NONPAIRED','B29_OFFICIAL_RELOCK','B32_BTN_RELOCK','B33_BTN_XB50_XX','B36_BTN_RELOCK','B37_BTN_XB50_XX','B38_BTN_IP_XX','B43_UTG_B75','B51_UTG_XX','B52_TWO_IP_LOCKS','B56_SB_B50_XX','B66_SB_B100_IP','B99_LMP_XX_RIVER','B102_SB_XX_RIVER','B105_BTN_XX_RIVER'):
        prefix='NL2_MULTIBOARD_'+code
        base=root/'solver_evidence'
        gz=base/(prefix+'.json.gz')
        idx=base/(prefix+'.index.json')
        if gz.exists()!=idx.exists():raise ValueError('Incomplete source archive '+code)
        if not gz.exists():
            batches[code]={'status':'PENDING_NOT_CERTIFIED'}
            continue
        ix=json.loads(idx.read_text())
        raw=gzip.decompress(gz.read_bytes())
        d=json.loads(raw)
        if (ix['batch']!=code or ix['generic_model_certification']!=0 or
            sha(gz)!=ix['gzip_sha256'] or hashlib.sha256(raw).hexdigest()!=ix['source_sha256']):
            raise ValueError('Source SHA or count mismatch '+code)
        # E's archived template hard-coded four jobs. New genuine work must
        # instead report the VERIFIED number of separate solver artifacts.
        # B5 retains five successful originals; the sixth timed out, and is EXCLUDED.
        # Repair only this KNOWN metadata defect, never infer extra GTO games.
        expected_new_jobs={'B5_SBGAPS':5,'B6_REMAIN':6,'B7_RIVER':5,'B8_LOCK':1,'B9_LMP_FAST':2,'B10_RIVER_EXP':1,'B11_RIVER_FAST':4,'B12_LOCK_FAST':1,'B13_LMP_B50':2}
        if code in expected_new_jobs and ix['actual_spot_flop_version_jobs']!=expected_new_jobs[code]:
            n=expected_new_jobs[code]
            if not (ix['actual_spot_flop_version_jobs']==4 and
                    len(d.get('artifacts',[]))==n and not d.get('errors') and
                    d['source_run_id']==ix['run_id'] and
                    d['new_authentic_board_cases']==ix['verified_cases'] and
                    d['exact_board_gto_sources']==ix['gto_cases'] and
                    d['imputed_pool_locked_sources']==ix['locked_cases'] and
                    all(len(z.get('cases',[]))>0 and not z.get('errors') for z in d['artifacts'])):
                raise ValueError('Archive index differs from verified raw job count '+code)
            ix['actual_spot_flop_version_jobs']=n
            idx.write_text(json.dumps(ix,ensure_ascii=False,indent=2)+'\n')
            print('REPAIRED VERIFIED JOB COUNT ONLY',code,'jobs=',n,flush=True)
        if (d['schema']!='NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1' or d['errors'] or
            d['source_run_id']!=ix['run_id'] or
            d['new_authentic_board_cases']!=ix['verified_cases'] or
            d['exact_board_gto_sources']!=ix['gto_cases'] or
            d['imputed_pool_locked_sources']!=ix['locked_cases'] or
            len(d['artifacts'])!=ix['actual_spot_flop_version_jobs']):
            raise ValueError('Incomplete actual Rust solver provenance '+code)
        ready.append(gz)
        batches[code]={'status':'VERIFIED','run_id':ix['run_id'],
                       'authentic_jobs':len(d['artifacts']),
                       'gto_cases':ix['gto_cases'],'locked_cases':ix['locked_cases'],
                       'new_subgames':ix['verified_cases'],
                       'gzip_sha256':ix['gzip_sha256']}
    return ready,batches

def make_report(data,batches,ranking):
    heading=[
     '# NL2 HU 392 models: multi-board CFR training labels and exact source evidence',
     '',
     'Scope: PR #2 Draft, never merge without explicit authorization.',
     'CERT-MULTIBOARD applies ONLY to 3–5 individually named true public board runs.',
     'Every unlisted board/texture action remains APPROX, not GTO.',
     '',
     '## Verified counts',
     '',
     '| status | nodes |',
     '| --- | ---: |',
     '| CERT-MULTIBOARD | '+str(data['CERT_MULTIBOARD'])+' |',
     '| APPROX approximate | '+str(data['APPROX'])+' |',
     '| Total | 392 |',
     '',
     '## Fixed frequency ranking and disclosure',
     '',
     'Source: pinned poker-solver inputs/pool_stats.json, 2,334,487 NL2 hands.',
     'Observed pot families: SRP 61.7%, 3BP 11.9%, limped 24.5%.',
     'ISO not measured as an isolated postflop family: reserve 25% of limped as ISO proxy and 75% as LMP.',
     'Sequential actions multiply marginal pooled frequencies, NOT observed exact multi-street frequencies.',
     'Preregistered cutoff top 24 of 392, 6.12%; lower-ranked 368 remain APPROX.',
     'CFR outcomes cannot be used to tune this cutoff.',
     '',
     '## Genuine GitHub Actions batches',
     '',
     '| batch | run | verified GTO games | partial NL2 lock games |',
     '| --- | --- | ---: | ---: |'
    ]
    for k,v in batches.items():
        heading.append('| '+k+' | '+(str(v['run_id']) if 'run_id' in v else 'PENDING')+
                       ' | '+str(v.get('gto_cases',0))+' | '+str(v.get('locked_cases',0))+' |')
    heading.extend([
      '',
      '## Top-24 preregistered game histories',
      '',
      '| rank | model ID | family/spot | original SPR | label | named GTO flop boards |',
      '| ---: | --- | --- | ---: | --- | --- |'
    ])
    for n in sorted((x for x in data['records'].values() if x['high_frequency_preregistered']),
                    key=lambda x:x['frequency_rank']):
        boards=n['certified_3_to_5_exact_flop_boards']
        choices=', '.join(x['flop']+' '+x['turn'] for x in boards) if boards else 'not enough authentic proof'
        heading.append('| '+str(n['frequency_rank'])+' | '+n['model_id']+
                       ' | '+n['family']+'/'+n['solver_profile']+' | '+str(n['assumed_model_node_spr'])+
                       ' | '+n['label']+' | '+choices+' |')
    c=collections.Counter(x['blocked_reason'] for x in data['records'].values() if x['label']=='APPROX')
    heading.extend(['', '## Reasons some MODEL nodes are not CERT', ''])
    for key,val in c.most_common():heading.append('- '+str(key)+': '+str(val))
    heading.extend([
      '',
      '## Convergence, combo reach and NL2 lock limits',
      '',
      'Each exact-board GTO proof must preserve the real flop-turn-river board, action history, actor, root range/pot/SPR,',
      'true node pot and effective SPR, source GitHub Actions run ID + SHA256, GTO gap <=0.5%,',
      'and at least one combo remaining after the earlier-street highest/near-mixed branch filter.',
      'Secondary actions only survive if f(a)>=40% absolute AND f(a)>=70% of highest frequency.',
      'NL2 only supplies aggregate observed action/street/size frequencies; missing conditional rates',
      'are IMPLICIT DEFAULTS, explicitly tagged: after a check bet45%; 33/50/75/100% sizing 35/35/20/10%.',
      'Real private-card player-pool behavior and fully locked villain range are not empirically known.',
      '50% pot depolarization is only a source-derived exact-board relative equity and action EV study candidate.',
      'A 3–5-board representative set NEVER proves the entire generic six-texture model cell is GTO.',
      '',
      'Do NOT merge Draft PR #2.',
      ''
    ])
    return '\n'.join(heading)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=pathlib.Path,default=pathlib.Path('data'))
    p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('data/nl2_hu_multiboard_status.json'))
    p.add_argument('--doc',type=pathlib.Path,default=pathlib.Path('docs/NL2_HU_MULTIBOARD_STATUS.md'))
    a=p.parse_args()
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
    from hu_multiboard_promote import promote
    source,batches=discover(a.root)
    rank=json.loads((a.root/'nl2_hu_multiboard_prerank.json').read_text())
    queue=json.loads((a.root/'nl2_hu_stage2_queue.json').read_text())
    data=promote(rank,queue,a.root,source)
    if data['CERT_MULTIBOARD']+data['APPROX']!=392:
        raise ValueError('Not exactly 392 user-visible labels')
    for n in data['records'].values():
        if n['label']=='APPROX':
            if n['certified_3_to_5_exact_flop_boards']:
                raise ValueError('False source data on APPROX')
            continue
        boards=n['certified_3_to_5_exact_flop_boards']
        if not 3<=len(boards)<=5 or len(set(x['flop'] for x in boards))!=len(boards) or len(set(x['flop_texture'] for x in boards))<2:
            raise ValueError('Invalid multi-board selection')
        if not n['high_frequency_preregistered'] or not all(
            x['nl2_locked_variants'] and x['strict_full_street_combo_reachable']>0 and
            x['genuine_gto_exploitability_pct']<=0.5 and x['relative_spr_error_pct']<=5 for x in boards):
            raise ValueError('Missing true solver proof for CERT-MULTIBOARD')
    data['independently_verified_completed_batches']=batches
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    a.doc.parent.mkdir(parents=True,exist_ok=True)
    a.doc.write_text(make_report(data,batches,rank))
    print(json.dumps({'CERT_MULTIBOARD':data['CERT_MULTIBOARD'],'APPROX':data['APPROX'],
                      'source_proofs':data['source_evidence'],'new_batches':batches},ensure_ascii=False))
if __name__=='__main__':main()
