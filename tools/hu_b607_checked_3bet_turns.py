"""Verify BTN's turn decision after a checked-through flop in a 100bb 3-bet pot."""
from hu_checked_stab_turns import TurnStudy, main


STUDY = TurnStudy(
    batch="B607", rank=198, model="ln-3bp-3b_t_model-wsml7c", filename="b607_checked_3bet",
    template="NL2_B537_8S7H4D_QH.json.gz",
    template_sha="263e7ecf337f9a05bc7cd2d4dc297fc3bca284e863c5423da5727e8c43195b14",
    spot="CO3_BTN", family="3BP", preflop_source="PINNED_POKER_SOLVER_PREFLOP_CFR",
    root_pot=1650, root_stack=9250, ip_bet_pct=50, root_branches=("x x",),
    label="翻牌雙方過牌；轉河牌按 NL2 分街頻率鎖定對手回應",
    report_schema="NL2_HU_B607_ORIGINAL_LOCKED_MEDIUM_V1",
)

if __name__ == "__main__":
    main(STUDY)
