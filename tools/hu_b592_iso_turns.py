from hu_checked_stab_turns import TurnStudy, main


STUDY = TurnStudy(
    batch="B592", rank=124, model="ln-iso-t_model-1gjwm8f", filename="b592_iso",
    template="NL2_B539_9S7D4H_4S_B33_GTO.json.gz",
    template_sha="efc57abd1d8ceeb9ef5cf174d80703d7fd68d49cd8a66c44df4135e497cafd77",
    spot="ISO_BTN_CO", family="ISO", preflop_source="ASSUMED_EXPLICIT_169CLASS",
    root_pot=950, root_stack=9600, ip_bet_pct=50, root_branches=("b50 c","x b50 c"),
    label="翻牌限半池；轉河牌使用 NL2 分街對手回應鎖頻",
    report_schema="NL2_HU_B592_ORIGINAL_LOCKED_MEDIUM_V1",
)

if __name__ == "__main__":
    main(STUDY)
