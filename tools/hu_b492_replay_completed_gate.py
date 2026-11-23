"""Authenticate the completed B492 gate and replay its native output using the frozen boundaries."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from hu_b467_river_source_gate import sha
from hu_b492_half_pot_leads import VERSIONS, code_for, read, write


INPUTS=Path('data/nl2_hu_b492_lead_inputs.json')
OUT=Path('data/nl2_hu_b492_half_pot_leads.json')
ARTIFACT=14786256954
RUN=45102821954
ARCHIVE_SHA='04847cb72fa39f60bf440a883ebb3d8885ba09755af2cbf499695c3d3b154196'
HEAD='7227b640eb76b8c249d471929b5987c3cca15327'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--metadata',type=Path,required=True)
    parser.add_argument('--originals',type=Path,required=True)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    info=read(args.metadata)
    assert (info['id'],info['name'],info['digest'],info['workflow_run']['id'],info['workflow_run']['head_sha'],info['workflow_run']['repository_id'])==(
        ARTIFACT,'B492-conditional-source-comparison','sha256:'+ARCHIVE_SHA,RUN,HEAD,1438346845)
    assert sha(args.archive.read_bytes())==ARCHIVE_SHA
    with ZipFile(args.archive) as gate:
        official=json.loads(gate.read(OUT.name))
        assert (official['source_run_id'],len(official['records']))==(RUN,17)
        assert Counter(row['status'] for row in official['records'])=={'BOTH_POSITIVE':16,'ZERO_JOINT_REACH':1}
        archive_refs={}
        for row in official['records']:
            for version in VERSIONS:
                decision=row[version]
                for path_key,sha_key in [('raw_path','raw_sha256'),('viewer_path','viewer_sha256')]:
                    if path_key in decision:
                        name=Path(decision[path_key]).relative_to('data').as_posix()
                        assert archive_refs.setdefault(name,decision[sha_key])==decision[sha_key]
        assert set(gate.namelist())==set(archive_refs)|{OUT.name}
        assert len(archive_refs)==39
        for name,expected in archive_refs.items():
            assert sha(gate.read(name))==expected
        for group in read(INPUTS)['groups']:
            for version in VERSIONS:
                filename=f'NL2_{code_for(group,version)}.zip'
                name=f'solver_evidence/{filename}'
                target=args.work/f'B492-source-{group}-{version}'
                target.mkdir(parents=True,exist_ok=True)
                package=target/filename
                package.write_bytes(gate.read(name))
                with ZipFile(package) as raw:
                    proof=json.loads(raw.read('provenance.json'))
                    assert (proof['group'],proof['version'],proof['run_id'])==(group,version,RUN)
                write(target/'outcome.json',dict(proof,status='SOLVED',archive=filename,archive_sha256=archive_refs[name]))
        subprocess.run([sys.executable,'tools/hu_b492_half_pot_leads.py','--assemble','--solver',str(args.solver),
                        '--originals',str(args.originals),'--work',str(args.work),'--run-id',str(RUN)],check=True)
        assert read(OUT)==official
        for name,expected in archive_refs.items():
            assert sha((Path('data')/name).read_bytes())==expected,name
    print('Verified 22 original/native pairs, all native job hashes, 17 viewer files and full conditional decision report.')


if __name__=='__main__':
    main()
