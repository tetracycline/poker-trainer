#!/usr/bin/env python3
"""B224 fail-closed regression for B163 rank313 parent. Synthetic objects test
authorization logic only; NOT a claim of a genuine solved GTO board or NL2 lock.
"""
import copy
import gzip
import hashlib
import json
import pathlib
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import verify_hu_multiboard_100bb as verifier

RUN = 44860436462
MODEL = 'ln-iso-lmp_r_model-wpg493'
def digest(data):
    return hashlib.sha256(data).hexdigest()
def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')
def check():
    with tempfile.TemporaryDirectory(prefix='nl2-r313-failclosed-') as temporary:
        root = pathlib.Path(temporary)
        d = root / 'data'
        proof = d / 'nl2_hu_b158_rank313_lmp_ks7h2d_gto_parent_pin.json'
        idxpath = d / 'solver_evidence/NL2_MULTIBOARD_B158_R313_KS7H2D_GTO.index.json'
        gzpath = d / 'solver_evidence/NL2_MULTIBOARD_B158_R313_KS7H2D_GTO.json.gz'
        root_sha = 'a' * 64
        job_sha = 'b' * 64
        manifest_sha = 'c' * 64
        raw = b'illustrative fixture; not an actual GTO or Rust solve'
        gz = gzip.compress(raw, mtime=0)
        gzpath.parent.mkdir(parents=True, exist_ok=True)
        gzpath.write_bytes(gz)
        pin = dict(
            schema='NL2_HU_B158_RANK313_LMP_KS7H2D_GTO_PARENT_PIN_V1',
            source_run_id=RUN, source_gto_job_id=None, spot='LMP_CO_BB',
            flop='Ks7h2d', flop_line='b75 r c', turn_line='x b50 c',
            target_rank=313, model_id=MODEL,
            original_full_100bb_lmp_gto_not_recomputed=True,
            observed_preflop_ranges=False, assumed_limped_169class=True,
            target_exact_actor_IP_river_nodes=1, target_exact_actor_IP_strict_combos=3,
            no_generic_model_certification=True,
            original_gto_root_sha256=root_sha,
            original_gto_job_sha256=job_sha,
            original_gto_manifest_sha256=manifest_sha,
        )
        idx = dict(
            schema='NL2_MULTIBOARD_VERIFIED_ARCHIVE_INDEX_V1',
            batch='B158_R313_KS7H2D_GTO', run_id=RUN,
            gto_cases=1, locked_cases=0, verified_cases=1,
            exact_target_actor_IP_river_nodes=1, exact_target_actor_IP_strict_combos=3,
            no_generic_model_certification=True,
            source_sha256=digest(raw),gzip_sha256=digest(gz),
            original_parent_GTO_root_SHA256=root_sha,
            original_parent_GTO_job_SHA256=job_sha,
            original_parent_GTO_manifest_SHA256=manifest_sha,
        )
        manifest = dict(
            spot='LMP_CO_BB', version='exp_ip', flop='Ks7h2d',
            selected_lines=['b75 r c'], selected_turn_lines=['x b50 c'],
            gto_parent_source_run_id=RUN,
            gto_parent_source_sha256=root_sha,
            flop_root_jobfile_sha256=job_sha,
            gto_parent_source_manifest_sha256=manifest_sha,
        )
        write(proof,pin);write(idxpath,idx)
        def accepts(m):
            return verifier.authorized_b163_rank313_exact_true_gto_parent(m)
        with patch.object(verifier,'__file__',str(root/'tools/verify_hu_multiboard_100bb.py')):
            assert accepts(manifest) is True, 'Valid rank313 fixture rejected (historical rank71 typo)'
            cases=0
            def must_reject():
                nonlocal cases
                assert accepts(manifest) is False
                cases+=1
            for rank in (71, 312):
                damaged=copy.deepcopy(pin);damaged['target_rank']=rank
                write(proof,damaged);must_reject()
            write(proof,pin)
            damaged=copy.deepcopy(pin);damaged['target_exact_actor_IP_strict_combos']=0
            write(proof,damaged);must_reject()
            damaged=copy.deepcopy(pin);damaged['target_exact_actor_IP_river_nodes']=0
            write(proof,damaged);must_reject()
            damaged=copy.deepcopy(pin);damaged['observed_preflop_ranges']=True
            write(proof,damaged);must_reject()
            write(proof,pin)
            damaged=copy.deepcopy(idx);damaged['source_sha256']='0'*64
            write(idxpath,damaged);must_reject()
            write(idxpath,idx)
            damaged=copy.deepcopy(idx);damaged['exact_target_actor_IP_strict_combos']=0
            write(idxpath,damaged);must_reject()
            write(idxpath,idx)
            damaged=copy.deepcopy(manifest);damaged['gto_parent_source_sha256']='0'*64
            assert accepts(damaged) is False;cases+=1
            damaged=copy.deepcopy(manifest);damaged['gto_parent_source_run_id']=RUN+1
            assert accepts(damaged) is False;cases+=1
            damaged=copy.deepcopy(manifest);damaged['version']='exp_oop'
            assert accepts(damaged) is False;cases+=1
            gzpath.write_bytes(gzip.compress(raw+b'changed',mtime=0))
            must_reject()
            assert cases==11, cases
    # The actual old B158 evidence still contains no valid target actor reach:
    # correcting the rank literal must never reclassify real zero-combo data.
    assert verifier.authorized_b163_rank313_exact_true_gto_parent(manifest) is False
    print('PASS B224: 1 synthetic positive metadata consistency, 11 fail-closed negatives, real B158 still blocked; ZERO new CERT')

if __name__ == '__main__':
    check()
