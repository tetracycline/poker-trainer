#!/usr/bin/env python3
"""Join independently proven CFR source archives without generalizing any
source board or violating action-history/SPR and combo-reach provenance."""
import argparse,collections,gzip,hashlib,json,pathlib

def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):
    data=path.read_bytes()
    return json.loads(gzip.decompress(data)),data
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,type=pathlib.Path)
    p.add_argument('--out',required=True,type=pathlib.Path)
    p.add_argument('--summary',required=True,type=pathlib.Path)
    a=p.parse_args()
    base=a.root/'nl2_hu_exact_boards.json.gz'
    d,bin0=read(base)
    ix=json.loads((a.root/'nl2_hu_exact_boards_index.json').read_text())
    if ix['gzip_sha256']!=sha(bin0) or ix['genuine_exact_board_subgames']!=len(d['subgames']):
        raise ValueError('Base source-provenance mismatch')
    total=list(d['subgames']);indices=[]
    runs=set(d['run_ids']);seen={(x['spot'],x['version'],x['source_sha256']) for x in total}
    if len(seen)!=len(total):raise ValueError('Repeated original CFR case')
    for stage in ('04','05'):
        name='nl2_hu_exact_boards_b'+stage
        bpath=a.root/(name+'.json.gz');jpath=a.root/(name+'.index.json')
        if not bpath.is_file() or not jpath.is_file():
            raise FileNotFoundError('Missing source artifact '+name)
        index=json.loads(jpath.read_text())
        x,rawzip=read(bpath)
        if index['schema']!='NL2_HU_AUTHENTIC_CFR_STAGE2_BATCH_INDEX_V1' or index['gz_sha256']!=sha(rawzip):
            raise ValueError('Unverified incremental payload digest')
        if index['raw_sha256']!=sha(gzip.decompress(rawzip)):
            raise ValueError('Compressed source hash not matching original')
        if index['generic_model_certs']!=0 or x['generic_model_upgrades']!=0:
            raise ValueError('Fictitious generic model GTO certification')
        if x['exact_subgame_count']!=len(x['subgames'])!=index['solved_subgames']:
            raise ValueError('Count mismatch')
        runs.add(index['run_id'])
        for c in x['subgames']:
            if c['source_run_id']!=index['run_id']:
                raise ValueError('CFR subgame run provenance mismatch')
            key=(c['spot'],c['version'],c['source_sha256'])
            if key in seen:raise ValueError('Repeated CFR source across batches')
            seen.add(key)
            total.append(c)
        indices.append(index)
    if len(total)!=len(seen):raise ValueError('Incomplete uniqueness check')
    status=collections.Counter(x['status'] for x in total)
    spots=collections.Counter(x['spot'] for x in total)
    pot=collections.Counter(x['pot_family'] for x in total)
    if status['CERT_EXACT_BOARD_GTO']!=sum([ix['gto_cert_exact_board_subgames']]+[z['actual_gto_cert_exact_board'] for z in indices]):
        raise ValueError('GTO-CERT source count mismatch')
    if status['EXPERIMENTAL_POOL_LOCKED']!=sum([ix['nl2_pool_locked_provisional_subgames']]+[z['actual_pool_locked_experimental'] for z in indices]):
        raise ValueError('Pool-locked response count mismatch')
    obj=dict(schema='HU_NL2_EXACT_BOARD_CFR_V1',
        public_board_scope_only=True,
        generic_model_upgrades=0,
        exact_subgame_count=len(total),
        status_counts=dict(status),
        run_ids=sorted(runs),
        warning='Each GTO CERT applies to one exact public board and action line+SPR. No generic 392 MODEL abstract nodes are certified.',
        subgames=total)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
    summary=dict(schema='NL2_HU_STAGE2_COMBINED_SOURCE_V1',
        run_ids=sorted(runs),source_cases=len(total),
        gto_exact_board_certificates=status['CERT_EXACT_BOARD_GTO'],
        nl2_provisional_pool_locked_source_cases=status['EXPERIMENTAL_POOL_LOCKED'],
        by_spot=dict(spots),by_pot_family=dict(pot),
        abstract_model_nodes=392,
        abstract_model_CERT=0,abstract_model_EST=0,
        source_status='AUTHENTIC_CFR_ONLY_ON_EXACT_BOARD_AND_ACTION_HISTORY',
        blocker='NL2 model 392 cells are class/texture level, lack actual flop-turn-river and complete action size SPR combo-weight lineage; no source transfer without this.'
    )
    a.summary.parent.mkdir(parents=True,exist_ok=True)
    a.summary.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
