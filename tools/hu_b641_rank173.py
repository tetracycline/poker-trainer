"""Verify BTN turn decisions after an exact three-quarter-pot flop c-bet against CO."""
from hu_checked_stab_turns import TurnStudy, main


STUDY = TurnStudy(
    batch="B641", rank=173, model="ln-3bp-3b_t_model-3sv4e8", filename="b641_btn_barrels",
    template="NL2_B537_8S7H4D_QH.json.gz",
    template_sha="263e7ecf337f9a05bc7cd2d4dc297fc3bca284e863c5423da5727e8c43195b14",
    spot="CO3_BTN", family="3BP", preflop_source="PINNED_POKER_SOLVER_PREFLOP_CFR",
    root_pot=1650, root_stack=9250, ip_bet_pct=75, root_branches=("x b75 c",),
    label="BTN 翻牌下注四分之三底池、CO 跟注；轉河牌按 NL2 分街頻率鎖定 CO 回應",
    report_schema="NL2_HU_B641_ORIGINAL_LOCKED_MEDIUM_V1",
)

if __name__ == "__main__":
    main(STUDY, displayed_actions={"過":"x", "下注 ½":"b50", "下注 ¾":"b75"})
