"""Authenticate B19 and B472 and build a selectable supplementary lock on their exact board."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path

from hu_b472_street_lock import GTO, LOCK, MODEL, PACK, POOL, RESULT, ROOT, RUN, read
from hu_sequential_cfr_reach import cardkey, compatible_node_reach, game_reach
from verify_hu_multiboard_100bb import locked_model_gain, source_nodes

NEW_RUN=45097676214
CODE="B478_R1_B472_STREET_LOCK"
ARCHIVES=Path("data/solver_evidence")
MID_BOARD="2d4h4s8s"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decision(root,sub):
    n,=(n for n in sub["nodes"] if (n["board"],n["line"],n["player"])==(MID_BOARD,"b50 c/",0))
    key=f'{MID_BOARD}|b50 c/|0'
    m=game_reach(root,sub)[0][key]
    compatible=compatible_node_reach(root,sub,n,m)
    result,=source_nodes(dict(sub,nodes=[n]),{"nodes":{key:compatible}})
    mask=base64.b64decode(compatible["mask"],validate=True)
    assert len(mask)==len(sub["hands"][0])
    hands={cardkey(h) for h,b in zip(sub["hands"][0],mask) if b}
    assert len(hands)==compatible["count"]==result["strictly_reachable_combos"]>0
    return result,hands


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--old-gto",required=True,type=Path)
    cli.add_argument("--old-exp",required=True,type=Path)
    cli.add_argument("--out-dir",type=Path,default=ARCHIVES)
    args=cli.parse_args()
    args.out_dir.mkdir(parents=True,exist_ok=True)
    result=read(RESULT)
    packed=json.loads(gzip.decompress(PACK.read_bytes()))
    assert digest(PACK.read_bytes())==result["archive_sha256"] and result["run"]==packed["run"]==NEW_RUN
    history=packed["history"]
    assert (history["model"],history["actor"],history["original_run"],history["GTO_sha256"],history["lock_sha256"],history["pool_sha256"])==(MODEL,"BB_OOP",RUN,GTO,LOCK,POOL)
    roots,subs={},{}
    for version,parent,sub_sha in (("gto",args.old_gto,GTO),("exp_oop",args.old_exp,LOCK)):
        folder=parent/"solver/postflop/out/LMP_CO_BB"/version
        manifest=read(parent/"evidence"/f"LMP_CO_BB-4s4h2d-{version}.json")
        assert (manifest["flop"],manifest["version"],manifest["spot"],manifest["pool_source_sha256"])==("4s4h2d",version,"LMP_CO_BB",POOL)
        roots[version]=read(folder/"4s4h2d_multiboard.json",manifest["file_flop_sha256"])
        subs[version]=read(folder/"4s4h2d_b50c_8s.json",sub_sha)
    new_bytes=base64.b64decode(packed["source_file_b64"],validate=True)
    assert digest(new_bytes)==packed["source_sha256"]==result["source_sha256"]
    old=subs["exp_oop"];raw=json.loads(new_bytes)
    new=dict(raw,line0=old["line0"],turn=old["turn"],rivers=old["rivers"])
    assert new["hands"]==old["hands"] and (new["flop"],new["pot"],new["stack"])==(old["flop"],old["pot"],old["stack"])
    old_root=roots["exp_oop"]
    assert history["root_sha256"]==ROOT
    g,gh=decision(roots["gto"],subs["gto"])
    e,eh=decision(old_root,old)
    n,nh=decision(old_root,new)
    assert n==packed["exact_node"] and len(nh)==result["new_compatible_combos"]
    assert n["medium_50pct_strict_evidence"]==result["b50"] and n["action_frequency_weighted_pct"]==result["action_frequencies_pct"]
    assert (g["node_spr"],e["node_spr"],n["node_spr"])==(19.55,)*3
    scope=result["lock_scope"]
    assert (raw["info"]["gto_expl_pct"],raw["info"]["hero_gap_pct"])==(result["gto_expl_pct"],result["hero_gap_pct"])
    assert 0<=result["hero_gap_pct"]<=.5 and 0<=result["gto_expl_pct"]<=.5
    assert len(result["achieved"])==4
    for r in result["achieved"]:
        tested=next(q for q in history["rows"] if (q["street"],q["token"])==(r["street"],r["token"]))
        stats=raw["info"]["lock_stats"][tested["pattern"]]
        assert stats["nodes"]==r["nodes"]>0 and abs(100*stats["fold"]-tested["fold"])<.2 and abs(100*stats["agg"]-tested["raise_pct"])<.2
    case=dict(run_id=NEW_RUN,version="exp_oop",source_sha256=result["source_sha256"],
              spot="LMP_CO_BB",pot_family="LMP",flop="4s4h2d",turn="8s",flop_line="b50 c",
              hands_by_seat=new["hands"],nodes=[n],gto_exploitability_pct=result["gto_expl_pct"],
              locked_hero_gap_pct=result["hero_gap_pct"],villain_lock_scope=scope)
    proof=dict(schema="NL2_HU_MULTIBOARD_PINNED_CFR_CERT_EVIDENCE_V1",source_run_id=NEW_RUN,
               no_generic_texture_certification=True,errors=[],artifacts=[dict(cases=[case])])
    encoded=gzip.compress(json.dumps(proof,ensure_ascii=False,separators=(",",":")).encode(),mtime=0)
    # RFC1952 OS is informational; use a fixed header on Python versions delegating to zlib.
    encoded=encoded[:9]+bytes([255])+encoded[10:]
    (args.out_dir/f"NL2_MULTIBOARD_{CODE}.json.gz").write_bytes(encoded)
    comparison=dict(GTO_strict_combos=len(gh), prior_NL2_strict_combos=len(eh), NL2_strict_combos=len(nh),
                    common_legal_hero_combos=len(gh&nh),prior_and_new_common_combos=len(eh&nh))
    lock=dict(version="exp_oop",run_id=NEW_RUN,sha256=result["source_sha256"],source_scope="PARTIALLY_LOCKED_NL2_MARGINAL_PROXY",
              viewer_archive_code=CODE,viewer_sha256=digest(encoded),pool_sha256=POOL,
              variant_label="分街實測池鎖頻",measurement_policy="STREET_SPECIFIC_POOL_MARGINALS",
              observed_marginal_source_nodes=scope["observed_marginal_source_nodes"],
              assumed_default_source_nodes=scope["imputed_assumption_nodes"],unlocked_source_nodes=scope["unmatched_nodes"],
              villain_observed_pattern_node_share_pct=scope["coverage_pct"],
              unknown_history_frequency_filled_with_default=scope["imputed_assumption_nodes"]>0,
              source_not_real_per_combo_observation=True,hero_model_gain_bb=locked_model_gain(new,"exp_oop"),
              true_hero_gap_pct=result["hero_gap_pct"],strictly_reachable_combos=len(nh),
              medium_50pct_eligible_combos=n["medium_50pct_eligible_combos"],
              b50_nonpolarized_relative_equity_research_candidate=n["b50_nonpolarized_relative_equity_research_candidate"],
              reach_comparison=comparison,applied_street_rates=result["achieved"])
    row=dict(model_id=MODEL,flop="4s4h2d",turn="8s",public_board=MID_BOARD,line="b50 c/",acting_seat=0,
             gto_run=RUN,gto_sha256=GTO,parent_lock_run=RUN,parent_lock_sha256=LOCK,
             original_package=PACK.name,original_package_sha256=result["archive_sha256"],lock=lock)
    dest=args.out_dir/"lock_variants";dest.mkdir(exist_ok=True)
    (dest/"rank1_b472.json").write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n")
    print(comparison)


if __name__=="__main__":
    main()
