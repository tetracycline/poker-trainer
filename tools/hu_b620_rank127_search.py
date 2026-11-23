"""Solve an independent flop and export a river only when both native policies reach it."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from hu_b463_rank45_gate import RUST
from hu_b467_river_source_gate import compact, json_bytes, sha
from hu_b568_caller_rivers import conditional_source, hand_cell
from hu_sequential_cfr_reach import accepted, game_reach
from hu_b620_rank127_rivers import root_job, make_jobs, observations

TURNS = {
    '9h7s4d': ['2h','3s','5s','6h','8c'],
    '8h6d3s': ['2d','4s','5h','7c','9h'],
    'As8c4s': ['2d','3h','5c','6d','9s'],
}


def native(directory, name, job, driver, threads):
    (directory / name).write_bytes(compact(job))
    subprocess.run([str(driver), name], cwd=directory, check=True,
                   env=dict(os.environ, RAYON_NUM_THREADS=str(threads)))
    return (directory/job['out']).read_bytes()


def search(flop, output, solver, run, route, pool, pipeline):
    turns = TURNS[flop]
    assert subprocess.check_output(['git','-C',solver/'postflop/postflop-solver','rev-parse','HEAD'],text=True).strip()==RUST
    driver=solver/'postflop/pfdriver/target/release/pfdriver'
    output.mkdir(parents=True,exist_ok=True)
    result = {'flop':flop,'tested_turns':[], 'selected':None}
    with tempfile.TemporaryDirectory() as tmp:
        directory=Path(tmp)
        job=root_job(flop,turns,pipeline)
        root_raw=native(directory,'root.job.json',job,driver,2)
        root=json.loads(root_raw)
        assert (root['flop'],root['pot'],root['stack'])==(flop,600,9700)
        assert 0 <= root['info']['gto_expl_pct'] <= .5 and not root['info'].get('lock_stats')
        flop_nodes = {n['line']:n for n in root['nodes'] if len(n['board'])==6}
        bb_calls = accepted(flop_nodes['b50'], root['hands'], 'c')
        sb_bets = accepted(flop_nodes[''], root['hands'], 'b50')
        for t in turns:
            parent, = (n for n in root['nodes'] if n['line']=='b50 c/' and n['board'][-2:]==t)
            pub=parent['board']
            can_reach = any(t not in h and
                hand_cell(''.join(h),pub[:6])[0] in route['flop'] and
                hand_cell(''.join(h),pub)[0] in route['turn'] and
                any(t not in opp and set(h).isdisjoint(opp) for opp in sb_bets)
                for h in bb_calls)
            if not can_reach:
                result['tested_turns'].append(dict(turn=t, shared_hands={}, root_route_reach=0))
                continue
            cards={pub[i:i+2] for i in range(0,8,2)}
            # Export two suits of each river rank. All private-hand and board eligibility
            # checks are run again on the actual source policies after solving.
            rivers=[r+s for r in '23456789TJQKA' for s in 'ch' if r+s not in cards]
            spec=dict(flop=flop,turn=t,root_turns=turns,river_extracts=rivers,river=rivers[0],turn_ip='50%',turn_oop='50%,100%')
            jobs,meta,_=make_jobs(root,spec,pool,pipeline)
            eligible=[]
            raw_results=[]
            for mode, name, current in zip(('gto','exp_ip'),('gto','native'),jobs,strict=True):
                raw=native(directory,name+'.job.json',current,driver,1)
                source=conditional_source(root,raw,current,meta if mode=='exp_ip' else [],mode,run,pool,rivers)
                source.update(archive_sha256=sha(raw))
                assert 0<=source['subgame']['info']['gto_expl_pct']<=.5
                if mode=='exp_ip': assert 0<=source['subgame']['info']['hero_gap_pct']<=.5
                raw_results.append(raw)
                viable={}
                masks=game_reach(root,source['subgame'])[0]
                for river in rivers:
                    board=pub+river
                    row,hands=observations(source,board,route,masks)
                    if hands: viable[river]=set(hands)
                eligible.append(viable)
                if not viable: break
            matches={}
            if len(eligible)==2:
                matches={rv:len(hands & eligible[1].get(rv,set())) for rv,hands in eligible[0].items()}
                matches={rv:n for rv,n in matches.items() if n>0}
            result['tested_turns'].append(dict(turn=t,shared_hands=matches))
            if not matches:continue
            spec['river']=max(matches,key=matches.get)
            package=output/f'NL2_B620_R127_{flop.upper()}.zip'
            with ZipFile(package,'w',compression=ZIP_DEFLATED,compresslevel=9) as z:
                for key,raw in [('root.job.json',compact(job)),('root.json',root_raw),
                                ('gto.job.json',compact(jobs[0])),('gto.json',raw_results[0]),
                                ('native.job.json',compact(jobs[1])),('native.json',raw_results[1])]:
                    z.writestr(key,raw)
            spec.update(archive=package.name,sha256=sha(package.read_bytes()),origin_solve_run_id=run)
            result['selected']=spec
            break
    (output/f'{flop}.summary.json').write_bytes(json_bytes(result))
