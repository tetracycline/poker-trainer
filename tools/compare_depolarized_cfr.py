#!/usr/bin/env python3
"""Genuine CFR test of a medium-size, potentially depolarized flop bet.

This only reports paired solver outcomes. It NEVER automatically alters NL2
tables or calls a small bet 'best' before convergence and combo reach checks.
"""
import argparse, hashlib, json, pathlib, sys, time
def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--solver-root",required=True,type=pathlib.Path)
    p.add_argument("--spot",default="BTN_BB")
    p.add_argument("--flop",default="Ks7h2d")
    p.add_argument("--version",choices=["gto","exp_ip","exp_oop"],default="gto")
    p.add_argument("--out",type=pathlib.Path,required=True)
    a=p.parse_args()
    pf=a.solver_root.resolve()/"postflop"
    sys.path.insert(0,str(pf/"py"))
    import job, pipeline, locks
    if a.spot not in pipeline.SPOTS:
        raise SystemExit("Unknown HU spot")
    a.out.mkdir(parents=True,exist_ok=True)
    is_ip_pfr=pipeline.SPOTS[a.spot]["pfr"]=="ip"
    records=[]
    for profile,sizes in [("baseline","33%,75%"),("medium_added","33%,50%,75%")]:
        raw=a.out/f"{a.spot}_{a.flop}_{a.version}_{profile}.json"
        extract=[{"prefix":[],"street":True}]
        lk= [] if a.version=="gto" else pipeline.lock_list(a.spot,a.version,a.flop)[0]
        j=job.make_job(a.spot,a.version,a.flop,str(raw),extract=extract,locks=lk,compress=False,target=0.5)
        if is_ip_pfr:
            j["flop_ip"]=sizes
        else:
            j["flop_oop"]=sizes
        jobfile=a.out/f"{a.spot}_{a.flop}_{a.version}_{profile}.job.json"
        started=time.monotonic()
        log=job.run(j,str(jobfile))
        result=json.loads(raw.read_text())
        info=result.get("info",{})
        nodes=result.get("nodes",[])
        initial=next((n for n in nodes if n.get("line","") in ("","x") and ("b33" in n.get("acts",[]))),None)
        metric="ev_eq" if a.version=="gto" else "ev_exploit"
        records.append({"profile":profile,"sizes":sizes,"version":a.version,
                        "raw_file":str(raw),"sha256":sha256(raw),"job_sha256":sha256(jobfile),
                        "elapsed_seconds":round(time.monotonic()-started,2),
                        "reported_hero_gap_pct":info.get("hero_gap_pct"),
                        "reported_gto_exploitability_pct":info.get("gto_expl_pct"),
                        "metric_name":metric,"metric":info.get(metric),
                        "node_count":len(nodes),
                        "root_actions":initial.get("acts",[]) if initial else [],
                        "root_player":initial.get("player") if initial else None,
                        "node_lock_stats":info.get("lock_stats",{}),
                        "stderr_tail":log[-1200:]})
    report={"spot":a.spot,"flop":a.flop,"version":a.version,
            "comparison":"same preflop ranges/rake/flop, adding 50% pot option",
            "results":records,
            "decision":"EXPERIMENT_ONLY_NOT_PUBLISHED",
            "limitation":"Must verify convergence, per-combo reachability, and matched medium-bet strategy before changing NL2."}
    (a.out/"comparison.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"spot":a.spot,"version":a.version,
                      "baselines":len(records),"decision":report["decision"]}))
if __name__=="__main__": main()
