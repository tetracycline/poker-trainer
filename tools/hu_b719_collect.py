"""Authenticate the seven immutable source archives used for rank255."""
import argparse
import json
from pathlib import Path

from hu_b467_river_source_gate import json_bytes, sha
from hu_b710_collect import REPO, REPO_ID, BRANCH, api

RUN = 45325812961
HEAD = '16d1567d7bc1b0886d5a0148eba37cd99b4c90cf'
RUNS = {
    45325812961: ('16d1567d7bc1b0886d5a0148eba37cd99b4c90cf', '.github/workflows/nl2-hu-b714-rank255-rivers.yml'),
    44654973894: ('d1c7d1e07f214ca957dd7d707c452de846ecf007', '.github/workflows/nl2-hu-stage2-batch05.yml'),
    44653774402: ('d7be700ecc467d46af8f472c820bcc33320f9f7c', '.github/workflows/nl2-hu-stage2-batch04.yml'),
}
OLD = {
    'Ks7h2d': ('2d7hKs9d5s', 14593390837, 14592064422),
    'KsQh4d': ('4dQhKsTc3h', 14592263783, 14593171704),
}
PINS = {
    14889308245: (45325812961, 138215014727, 'Qs8h4d', 'paired', 'f7932af513ebe0ded485e101a8ed79b61eccab9ab2190ac802dc6acfa8d88484'),
    14889293183: (45325812961, 138215014961, 'Jh8d3c', 'paired', 'f86e471ccc5831d3c840f3b3b5bca80a02f8252a2921b1a806085ecd66132093'),
    14889113524: (45325812961, 138215015135, '9c6c3h', 'paired', '504cda5b366cb34c641bd53d7f942da471eabd7dda8d285c1770307900b7ab2b'),
    14593390837: (44654973894, 136018840350, 'Ks7h2d', 'gto', 'cd5c9cb6bedb3cc3bc72a3fc5053b950698ae8d150f1b57b2c8af2c657680311'),
    14592064422: (44654973894, 136018840043, 'Ks7h2d', 'exp_ip', 'addb58794ffc911b2c37e34974a5aad28627434fd268cd4d9e06ad630f90c897'),
    14593171704: (44653774402, 136014875231, 'KsQh4d', 'exp_ip', 'd8a2bf420354618d8ddfcbd7c31c1e80479f89bd2bc996fbfe1ccace326444ed'),
    14592263783: (44653774402, 136014875377, 'KsQh4d', 'gto', 'b2cb83c4641c7991b5aba9d76c199879073d72d49313ce960a1a921b1c5d93cc'),
}
LEGACY_STEPS = {
    'Compile pinned authentic Rust CFR solver',
    'Compute genuine GTO or NL2 villain-frequency-locked multi-street CFR',
    'Preserve parent and all river subgames plus per-combo reach and SHA-256',
}
NEW_STEPS = {
    'Authenticate the published rank103 roots, original turn studies and three-street rank255 route',
    'Build the pinned native solver',
    'Solve only new conditional turns and checked river decisions from verified original roots',
    'Run actions/upload-artifact@v4',
}


def validate(receipts):
    sources = {}
    for ident, (rid, jid, flop, version, digest) in PINS.items():
        head, path = RUNS[rid]
        run = receipts['runs'][str(rid)]
        job = receipts['jobs'][str(jid)]
        artifact = receipts['artifacts'][str(ident)]
        assert (run['id'],run['head_sha'],run['path'],run['head_branch'],run['status'],run['conclusion']) == (
            rid,head,path,BRANCH,'completed','success')
        assert (run['repository']['id'],run['repository']['full_name']) == (REPO_ID,REPO)
        paired = version == 'paired'
        name = f'B714-R255-{flop}' if paired else f'nl2-stage2-BB3_BTN-{version}-{flop}'
        jobname = f'solve ({flop})' if paired else f'solve (BB3_BTN, {flop}, {version})'
        assert (job['run_id'],job['id'],job['name'],job['head_sha'],job['run_attempt'],job['status'],job['conclusion']) == (
            rid,jid,jobname,head,run['run_attempt'],'completed','success')
        successful = {s['name'] for s in job['steps'] if (s['status'],s['conclusion']) == ('completed','success')}
        assert (NEW_STEPS if paired else LEGACY_STEPS) <= successful
        workflow = artifact['workflow_run']
        assert (workflow['id'],workflow['repository_id'],workflow['head_sha'],workflow['head_branch']) == (rid,REPO_ID,head,BRANCH)
        assert (artifact['id'],artifact['name'],artifact['digest'],artifact['expired']) == (ident,name,'sha256:'+digest,False)
        sources[ident] = dict(id=ident,sha256=digest,run=rid,head=head,job=jid,flop=flop,version=version,name=name)
    assert set(receipts['runs']) == {str(r) for r in RUNS}
    assert set(receipts['artifacts']) == {str(a) for a in PINS}
    assert set(receipts['jobs']) == {str(p[1]) for p in PINS.values()}
    return sources


def main(directory):
    directory.mkdir(parents=True,exist_ok=True)
    assert not any(directory.iterdir())
    receipt = dict(runs={}, jobs={}, artifacts={})
    for rid in RUNS:
        receipt['runs'][str(rid)] = json.loads(api('actions/runs/'+str(rid)))
    for ident,(_,jid,_,_,_) in PINS.items():
        receipt['jobs'][str(jid)] = json.loads(api('actions/jobs/'+str(jid)))
        receipt['artifacts'][str(ident)] = json.loads(api('actions/artifacts/'+str(ident)))
    sources = validate(receipt)
    (directory/'receipt.json').write_bytes(json_bytes(receipt))
    for ident,source in sources.items():
        raw = api(f'actions/artifacts/{ident}/zip')
        assert sha(raw) == source['sha256']
        (directory/f'{ident}.zip').write_bytes(raw)
    print(json.dumps(dict(authenticated_originals=len(sources),runs=list(RUNS))))


if __name__ == '__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',required=True,type=Path)
    main(cli.parse_args().output)
