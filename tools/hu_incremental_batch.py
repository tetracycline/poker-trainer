#!/usr/bin/env python3
"""Pack a VERIFIED genuine CFR stage-2 batch for NL2 source-only viewing.

Only exact public boards/action histories/pot/SPR may be CERT.
No generic MODEL node is ever promoted via texture resemblance.
"""
import argparse, collections, gzip, hashlib, json, pathlib, re, sys

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def pack(a):
    sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
    import export_hu_exact_board_cert as upstream
    verified=json.loads(a.proof.read_text())
    if verified.get('errors') or verified.get('run_id')!=a.run_id:
        raise ValueError('Unverified or mismatched independent source provenance')
    data=upstream.build(a.downloads,verified)
    if data['generic_model_upgrades']!=0:
        raise ValueError('Cross-texture MODEL substitution prohibited')
    cases=data['subgames']
    counts=collections.Counter(x['status'] for x in cases)
    if len(cases)!=verified['solved_subgames'] or len(cases)==0:
        raise ValueError('Subgames count does not reconcile with original sources')
    if counts['CERT_EXACT_BOARD_GTO']<=0 or counts['EXPERIMENTAL_POOL_LOCKED']<=0:
        raise ValueError('Missing GTO or locked response source')
    keys=set()
    for r in cases:
        k=(r['spot'],r['version'],r['source_sha256'])
        if k in keys:raise ValueError('Repeated solver hash/profile')
        keys.add(k)
        if r['source_run_id']!=a.run_id or r['pot_family'] not in ('SRP','3BP'):
            raise ValueError('Run/pot provenance mismatch')
        for n in r['nodes']:
            if n['reachable_combos']<=0:continue
            if len(n['eligible_action_masks_b64'])<10 or n['node_spr']<0:
                raise ValueError('Combo/SPR source invalid')
    result={
      'schema':'HU_NL2_EXACT_BOARD_CFR_V1',
      'run_ids':[a.run_id],
      'source_proof_run_id':a.run_id,
      'public_board_scope_only':True,
      'generic_model_upgrades':0,
      'exact_subgame_count':len(cases),
      'status_counts':dict(counts),
      'combo_rules':data['rules'],
      'warning':'Each source is GTO CERT for its own actual board and pot/SPR/action line only, never for generic NL2 MODEL.',
      'subgames':cases}
    raw=(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    compressed=gzip.compress(raw,compresslevel=9,mtime=0)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(compressed)
    assert gzip.decompress(a.out.read_bytes())==raw
    index={
      'schema':'NL2_HU_AUTHENTIC_CFR_STAGE2_BATCH_INDEX_V1',
      'run_id':a.run_id,
      'payload':a.out.name,
      'gz_sha256':digest(compressed),
      'raw_sha256':digest(raw),
      'compressed_bytes':len(compressed),
      'actual_gto_cert_exact_board':counts['CERT_EXACT_BOARD_GTO'],
      'actual_pool_locked_experimental':counts['EXPERIMENTAL_POOL_LOCKED'],
      'solved_subgames':len(cases),
      'generic_model_certs':0,
      'actual_preflop_spots':sorted({x['spot'] for x in cases}),
      'pool_source_scope':'NL2 aggregate sample frequencies may cover only a fraction of villain nodes; no unobserved combo behavior is empirical.',
    }
    ix=a.out.with_suffix('').with_suffix('.index.json')
    ix.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(index,ensure_ascii=False))
    return index

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--downloads',type=pathlib.Path,required=True)
    p.add_argument('--proof',type=pathlib.Path,required=True)
    p.add_argument('--run-id',type=int,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    pack(a)
if __name__=='__main__':main()
