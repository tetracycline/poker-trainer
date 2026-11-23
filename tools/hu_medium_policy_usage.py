"""Read the actual action masks and equity research flags for each verified medium-size policy."""
from collections import Counter


def policy(version, run, digest, eligible, candidate):
    assert isinstance(eligible, int) and eligible >= 0 and isinstance(candidate, bool)
    assert not candidate or eligible > 0
    return dict(version=version, source_run_id=run, source_sha256=digest,
                eligible_combos=eligible, nonpolarized_candidate=candidate)


def summarize(policies, field):
    if not policies:
        return "SOURCE_UNAVAILABLE"
    gto, *locks = policies
    assert gto["version"] == "gto" and locks and all(p["version"].startswith("exp_") for p in locks)
    gto_pass = bool(gto[field])
    lock_count = sum(bool(p[field]) for p in locks)
    if gto_pass and lock_count == len(locks):
        return "GTO_AND_ALL_VERIFIED_LOCKS"
    if gto_pass and lock_count:
        return "GTO_AND_SOME_VERIFIED_LOCKS"
    if gto_pass:
        return "GTO_ONLY"
    return "LOCKED_POLICY_ONLY" if lock_count else "NEITHER_POLICY"


def medium_usage(board, alternate, frozen):
    status = board["half_pot_status"]
    policies = []
    action = "b50"
    pot_pct = 50
    if status == "NATIVE_ACTION":
        for p in [board["gto"], *board["opponent_locks"]]:
            if "b50" not in p["actions"]:
                assert p["half_pot_eligible_combos"] == 0 and not p["nonpolarized_candidate"]
            policies.append(policy(p["version"], p["run"], p["sha256"], p["half_pot_eligible_combos"],
                                   p["nonpolarized_candidate"]))
    elif status == "EXCEEDS_EFFECTIVE_STACK":
        action = "a"
        pot_pct = round(100 * board["stack_bb"] / board["pot_bb"], 3)
        for p in [board["gto"], *board["opponent_locks"]]:
            a = p.get("short_stack_all_in")
            if a:
                assert a["pot_pct"] == pot_pct and a["action"] == action
                policies.append(policy(p["version"], p["run"], p["sha256"], a["eligible_combos"],
                                       a["nonpolarized_research_candidate"]))
        # A future short stack without a complete bound pair has no verified comparison.
        if len(policies) != len(board["opponent_locks"]) + 1:
            policies = []
    elif status == "CONDITIONAL_FROZEN_RIVER_BOTH_POSITIVE":
        for side in ("gto", "exp_oop"):
            p = frozen["policies"][side]
            policies.append(policy(side, frozen["run"], p["output_sha256"], p["b50"]["eligible"], p["b50"]["candidate"]))
    elif status == "CONDITIONAL_BOTH_POSITIVE":
        for side in ("gto", "exp_oop"):
            p = alternate[side]
            assert p["version"] == side and p["source_run_id"] == board["conditional_run"]
            policies.append(policy(side, p["source_run_id"], p["source_sha256"], p["b50"]["eligible"], p["b50"]["candidate"]))
    return dict(source_scope=status, action=action, pot_pct=pot_pct, policies=policies,
                eligible_policy_comparison=summarize(policies, "eligible_combos"),
                nonpolarized_policy_comparison=summarize(policies, "nonpolarized_candidate"))


def comparison_counts(boards, field):
    counts = Counter(board["medium_policy_usage"][field] for board in boards)
    assert sum(counts.values()) == len(boards)
    return dict(counts)
