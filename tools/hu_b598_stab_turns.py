from hu_checked_stab_turns import TurnStudy, main


STUDY = TurnStudy(
    batch="B598", rank=133, model="ln-ipc-t_model-day18r", filename="b598_stab",
    template="NL2_B538_JH9S4C_QC_45119866932.json.gz",
    template_sha="716e87c13e000aa3d8593bce99ba4a87157d8e57fd05e672589547d8c9ce6a93",
    spot="UTG_CO", family="SRP", preflop_source="PINNED_POKER_SOLVER_PREFLOP_CFR",
    root_pot=650, root_stack=9750, ip_bet_pct=100, root_branches=("x b100 c",),
    label="CO 翻牌下注滿池獲跟；轉河牌使用 NL2 分街對手回應鎖頻",
    report_schema="NL2_HU_B598_ORIGINAL_LOCKED_MEDIUM_V1",
)

if __name__ == "__main__":
    main(STUDY)
