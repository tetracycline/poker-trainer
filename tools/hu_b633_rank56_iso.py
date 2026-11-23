"""Verify BTN turn decisions after a one-third-pot CO lead, BTN call and CO check."""
from hu_checked_stab_turns import TurnStudy, main


STUDY = TurnStudy(
    batch="B633", rank=56, model="ln-iso-t_model-1xvw4lk", filename="b633_iso",
    template="NL2_B539_9S7D4H_4S_B33_GTO.json.gz",
    template_sha="efc57abd1d8ceeb9ef5cf174d80703d7fd68d49cd8a66c44df4135e497cafd77",
    spot="ISO_BTN_CO", family="ISO", preflop_source="ASSUMED_EXPLICIT_169CLASS",
    root_pot=950, root_stack=9600, ip_bet_pct=33, oop_bet_pct=33,
    root_threads=1, root_branches=("b33 c", "x b33 c"), target_flop_branch="b33 c",
    label="CO 翻牌下注三分之一底池後 BTN 跟注；轉河牌使用 NL2 分街對手鎖頻",
    report_schema="NL2_HU_B633_ORIGINAL_LOCKED_MEDIUM_V1",
)

if __name__ == "__main__":
    main(STUDY)
