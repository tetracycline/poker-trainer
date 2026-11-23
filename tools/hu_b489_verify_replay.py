"""Compare reconstructed native arrays and rank79 decisions against the published snapshot."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


report=Path('data/nl2_hu_b489_rank79_attempts.json')
root=Path('data/solver_evidence')
raw_paths=sorted(root.glob('NL2_B489_*.json.gz'))
viewer_paths=sorted(root.glob('NL2_MULTIBOARD_REVERIFIED_R79_*.json.gz'))
assert len(raw_paths)==8 and len(viewer_paths)==4


def published(path):
    return subprocess.check_output(['git','show','HEAD:'+path.as_posix()])


def normalize_digests(value):
    # Encoded gzip streams can differ by zlib implementation. Raw source digests,
    # full native arrays, hand order, all masks, pool statistics and EVs must match.
    if isinstance(value,list):
        return [normalize_digests(v) for v in value]
    if isinstance(value,dict):
        compressed={'archive_sha256','locked_original_archive_sha256','viewer_sha256','locked_viewer_sha256','original_archive_sha256'}
        return {k:normalize_digests(v) for k,v in value.items() if k not in compressed}
    return value


def check_archive_links(attempts,load):
    pins=json.loads(Path('data/nl2_hu_b489_originals.json').read_bytes())
    for name,row in attempts['fresh'].items():
        flop,turn,version=name.split()
        original=attempts['fresh_original_artifacts'][str(row['archive_id'])]
        assert original['name']==f'NL2-B489-{flop}-{version}'
        code=f'B489_R79_{flop.upper()}_{turn.upper()}_{version.upper()}'
        blob=load(root/f'NL2_{code}.json.gz')
        assert hashlib.sha256(blob).hexdigest()==row['archive_sha256']
        archived=json.loads(gzip.decompress(blob))
        assert archived['github_artifact_sha256']==original['sha256']
        assert archived['source_sha256']==row['source_sha256']
    for pin in attempts['model']['pins']:
        id=pin['archive_code'].removeprefix('GITHUB_ARTIFACT_')
        assert pins[id]['sha256']==pin['archive_sha256']
        for code_key,hash_key,prefix in [('viewer_archive_code','viewer_sha256','NL2_MULTIBOARD_'),
                    ('locked_original_archive_code','locked_original_archive_sha256','NL2_'),
                    ('locked_viewer_archive_code','locked_viewer_sha256','NL2_MULTIBOARD_')]:
            assert hashlib.sha256(load(root/(prefix+pin[code_key]+'.json.gz'))).hexdigest()==pin[hash_key]


for path in raw_paths+viewer_paths:
    restored=json.loads(gzip.decompress(path.read_bytes()))
    previous=json.loads(gzip.decompress(published(path)))
    assert normalize_digests(restored)==normalize_digests(previous),path

replayed=json.loads(report.read_bytes())
check_archive_links(replayed,Path.read_bytes)
check_archive_links(json.loads(published(report)),published)
assert normalize_digests(replayed)==normalize_digests(json.loads(published(report)))
group=replayed['model']
assert len(group['boards'])==len(group['pins'])==2
assert {board['flop'] for board in group['boards']}=={'KsQh4d','QsJh4d'}
assert all(replayed['fresh'][f'KsQh3d {turn} gto']['compatible_hole_card_pairs']==0 for turn in ('Tc','7h','7s'))
print('Verified all eight completed native sources, four directional viewers, two positive pairs and three exact GTO zeros.')
