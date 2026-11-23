"""Persist and authenticate native turn jobs rooted in a frozen original GTO flop."""
import json
from zipfile import ZipFile
import subprocess

from hu_b463_rank45_gate import SOLVER, RUST
from hu_b467_river_source_gate import compact, sha
from hu_b470_rank73_new_rivers import audit_patterns
from hu_b483_locked_medium import POOL
from hu_b492_half_pot_leads import zip_payload


def replay(original, version, pool, pipeline, path, run, code, make_job):
    job, locks = make_job(original, version, pool, pipeline)
    gto = original["source"]
    frozen = original["identity"]
    with ZipFile(path) as archive:
        raw = archive.read("turn.json")
        meta = json.loads(archive.read("provenance.json"))
        assert archive.read("job.json") == compact(job) and archive.read("locks.json") == compact(locks)
        assert sha(archive.read("original-flop.json")) == frozen["root_sha256"]
    assert meta == dict(solver=SOLVER, rust=RUST, pool_sha256=POOL, run=run, version=version,
                        original=frozen, result_sha256=sha(raw), job_sha256=sha(compact(job)))
    sub = json.loads(raw)
    assert all(sub[k] == gto["subgame"][k] for k in ("hands","pot","stack","flop"))
    sub.update(line0=gto["subgame"]["line0"], turn=job["turn"], rivers=gto["subgame"]["rivers"])
    manifest = dict(gto["manifest"], locks=locks)
    source = dict(root=gto["root"], subgame=sub, manifest=manifest, version=version, run=run,
                  source_sha256=sha(raw), archive_code=code, archive_sha256=sha(path.read_bytes()))
    if version != "gto":
        parent = dict(run=gto["run"], sha256=frozen["root_sha256"])
        manifest.update(gto_parent_source_run_id=parent["run"],gto_parent_source_sha256=parent["sha256"])
        source.update(verified_gto_parent=parent, measured_lock_application=audit_patterns(sub,job,manifest,pool,job["hero"]))
    else:
        assert not sub["info"].get("lock_stats") and not job.get("locks")
    source["applied_rust_rates"] = sub["info"].get("lock_stats",{})
    return source


def run_native(directory, driver, original, job, locks, run, version, name):
    folder = directory.resolve()
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"job.json").write_bytes(compact(job))
    subprocess.run([str(driver.resolve()),"job.json"],cwd=folder,check=True,timeout=360)
    raw = (folder/"turn.json").read_bytes()
    provenance = dict(solver=SOLVER,rust=RUST,pool_sha256=POOL,run=run,version=version,
          original=original["identity"],result_sha256=sha(raw),job_sha256=sha(compact(job)))
    zip_payload(folder/name,{"turn.json":raw,"job.json":compact(job),"locks.json":compact(locks),
              "original-flop.json":compact(original["source"]["root"]),"provenance.json":compact(provenance)})
    return folder/name
